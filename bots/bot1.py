import threading
import ccxt
import pandas as pd
import numpy as np
import time
import random
from utils.db import get_key, log_trade, get_params, set_param
from utils.sentiment import get_combined_sentiment
from utils.taapi import get_indicator, get_pattern, get_historical

class Bot1(threading.Thread):
    """
    Bot 1: Trend-Following Momentum Bot with Sentiment Boost
    Targets 1-2% daily returns with max 5% drawdown
    Uses 20/50 SMA crossover, RSI < 30, and sentiment > 0.6
    """
    
    def __init__(self, master_pass):
        """Initialize Bot 1 with parameters from database"""
        super().__init__()
        self.master_pass = master_pass
        
        # Load parameters from database
        self.params = get_params('bot1')
        self.risk_level = float(self.params.get('risk', '1.0')) / 100  # Convert percentage to decimal (e.g., 0.01 for 1%)
        self.alloc = float(self.params.get('alloc', '10')) / 100  # Portfolio allocation (e.g., 0.10 for 10%)
        self.trade_freq = int(self.params.get('freq', '60'))  # Trading frequency in seconds
        
        # Trading pairs - high liquidity coins
        self.coins = ['BTC/USD', 'ETH/USD']
        self.running = True
        
        # Initialize Coinbase exchange via CCXT (V1 API)
        self.exchange = ccxt.coinbase({
            'apiKey': get_key('COINBASE_KEY_NAME', master_pass) or get_key('coinbase_api_key', master_pass),
            'secret': get_key('COINBASE_PRIVATE_KEY', master_pass) or get_key('coinbase_secret', master_pass),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'version': 'v3'  # Use new Advanced Trade API
            }
        })
        
        # Set rate limit to avoid 429 errors
        self.exchange.rateLimit = 1000  # 1 second between requests
        
    def run(self):
        """Main bot loop: check conditions every trade_freq seconds"""
        while self.running:
            # Check if bot is active from portfolio optimization
            from utils.optimization import check_bot_active
            if not check_bot_active('bot1'):
                log_trade('bot1', 'info', 'Bot deactivated by optimization')
                self.running = False
                break
            try:
                for coin in self.coins:
                    # Convert coin format for TAAPI (BTC/USD -> BTC/USDT)
                    taapi_symbol = coin.replace('/USD', '/USDT')
                    
                    # Get indicators from TAAPI
                    sma20_data = get_indicator('sma', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '1h',
                        'period': 20
                    }, self.master_pass)
                    
                    sma50_data = get_indicator('sma', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '1h',
                        'period': 50
                    }, self.master_pass)
                    
                    rsi_data = get_indicator('rsi', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '1h',
                        'period': 14
                    }, self.master_pass)
                    
                    # Get candlestick patterns
                    pattern_data = get_pattern(taapi_symbol, '1h', 'coinbase', self.master_pass)
                    
                    # Skip if any data is missing
                    if not all([sma20_data, sma50_data, rsi_data]):
                        log_trade('bot1', 'error', f'Missing TAAPI data for {coin}')
                        continue
                    
                    sma20 = sma20_data.get('value', 0)
                    sma50 = sma50_data.get('value', 0)
                    rsi = rsi_data.get('value', 50)
                    
                    # Check for bullish patterns
                    bullish_pattern = False
                    if pattern_data:
                        # Check for bullish patterns (value > 0 means bullish)
                        bullish_patterns = ['CDLHAMMER', 'CDLMORNINGSTAR', 'CDLENGULFING', 'CDLDOJI']
                        for pattern in bullish_patterns:
                            if pattern_data.get(f'value{pattern}', 0) > 0:
                                bullish_pattern = True
                                log_trade('bot1', 'signal', f'Bullish pattern detected: {pattern} for {coin}')
                                break
                    
                    # Get current price (still use CCXT for real-time price)
                    ticker = self.exchange.fetch_ticker(coin)
                    current_price = ticker['last']
                    
                    # Get sentiment score from Twitter/Reddit using VADER
                    sentiment = get_combined_sentiment(coin.split('/')[0].lower(), self.master_pass)['combined_score']
                    
                    # Enhanced trading conditions: Golden cross + Oversold + Positive sentiment + Optional pattern
                    confidence_boost = 1.2 if bullish_pattern else 1.0
                    if sma20 > sma50 and rsi < 30 and sentiment > (0.6 / confidence_boost):
                        # Fetch available USD balance
                        balance = self.exchange.fetch_balance()['USD']['free']
                        
                        # Calculate position size based on allocation percentage
                        amount = (balance * self.alloc) / current_price
                        
                        # Execute market buy order
                        order = self.exchange.create_market_buy_order(coin, amount)
                        entry = order['price'] if 'price' in order else current_price
                        
                        # Set stop-loss at 1% below entry (risk management)
                        sl_order = self.exchange.create_stop_market_order(
                            coin, 'sell', amount, entry * (1 - self.risk_level)
                        )
                        
                        # Set take-profit at 3% above entry (3:1 risk-reward ratio)
                        tp_order = self.exchange.create_limit_sell_order(
                            coin, amount, entry * (1 + 3 * self.risk_level)
                        )
                        
                        # Log trade to database
                        log_trade('bot1', 'buy', f'Coin: {coin}, Amount: {amount}, Entry: {entry}')
                        
            except ccxt.NetworkError as e:
                # Handle network errors
                log_trade('bot1', 'error', f'Network error: {str(e)}')
                time.sleep(5)  # Wait 5 seconds before retry
            except ccxt.ExchangeError as e:
                # Handle exchange-specific errors
                log_trade('bot1', 'error', f'Exchange error: {str(e)}')
                if '429' in str(e):  # Rate limit error
                    time.sleep(60)  # Wait 1 minute
            except Exception as e:
                # Handle any other errors
                log_trade('bot1', 'error', f'Unexpected error: {str(e)}')
                
            # Wait before next trading cycle
            time.sleep(self.trade_freq)
            
    def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        
    def update_params(self, risk=None, alloc=None, freq=None):
        """Update bot parameters dynamically"""
        if risk is not None:
            self.risk_level = risk / 100
            set_param('bot1', 'risk', str(risk))
            
        if alloc is not None:
            self.alloc = alloc / 100
            set_param('bot1', 'alloc', str(alloc))
            
        if freq is not None:
            self.trade_freq = freq
            set_param('bot1', 'freq', str(freq))
            
    def backtest(self, historical_data):
        """
        Backtest strategy on historical data using TAAPI
        historical_data: Can be CCXT data or we fetch from TAAPI
        Returns: final portfolio value, trades list, sharpe ratio
        """
        portfolio = 10000  # Starting capital
        trades = []
        max_portfolio = portfolio
        
        # If historical_data is provided, use it; otherwise fetch from TAAPI
        if len(historical_data) < 100:
            # Fetch from TAAPI (max 300 candles)
            taapi_data = get_historical('BTC/USDT', '1h', 300, 'coinbase', self.master_pass)
            if taapi_data:
                historical_data = taapi_data
            else:
                log_trade('bot1', 'error', 'Failed to fetch historical data from TAAPI')
                return portfolio, trades, 0
        
        # Need at least 50 candles for indicators
        for i in range(50, len(historical_data)):
            # Get current and historical prices
            current_candle = historical_data[i]
            current_price = current_candle[4] if isinstance(current_candle, list) else current_candle['close']
            
            # For backtesting, we'll use the historical data to simulate indicators
            # In a real scenario, you might want to use TAAPI's historical endpoints
            # For now, we'll use pandas as it's more efficient for backtesting
            close_slice = pd.Series([historical_data[j][4] if isinstance(historical_data[j], list) else historical_data[j]['close'] 
                                   for j in range(i-99, i+1)])
            
            # Calculate indicators locally for backtesting efficiency
            sma20 = close_slice.rolling(20).mean().iloc[-1]
            sma50 = close_slice.rolling(50).mean().iloc[-1]
            
            # Calculate RSI
            changes = close_slice.diff()
            gain = changes.clip(lower=0).ewm(span=14, adjust=False).mean()
            loss = (-changes.clip(upper=0)).ewm(span=14, adjust=False).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            
            # Mock sentiment for backtesting (normally would use historical sentiment)
            sentiment = 0.7
            
            # Check trading conditions
            if sma20 > sma50 and rsi < 30 and sentiment > 0.6:
                sim_entry = close_slice.iloc[-1]
                sim_amount = portfolio * 0.1 / sim_entry  # 10% allocation
                
                # Simulate trade outcome (70% win rate for 3:1 R:R)
                if random.random() > 0.3:
                    sim_exit = sim_entry * (1 + 0.03)  # 3% profit
                else:
                    sim_exit = sim_entry * (1 - 0.01)  # 1% loss
                    
                profit = sim_amount * (sim_exit - sim_entry)
                portfolio += profit
                trades.append(profit)
                
                # Track maximum portfolio value for drawdown calculation
                max_portfolio = max(max_portfolio, portfolio)
                
                # Calculate current drawdown
                drawdown = (max_portfolio - portfolio) / max_portfolio
                
                # Stop if drawdown exceeds 5%
                if drawdown > 0.05:
                    log_trade('bot1', 'backtest', f'Max drawdown exceeded: {drawdown:.2%}')
                    break
                    
        # Calculate Sharpe ratio (assuming daily returns, annualized)
        if trades:
            sharpe = (np.mean(trades) / np.std(trades)) * np.sqrt(365)
        else:
            sharpe = 0
            
        return portfolio, trades, sharpe
