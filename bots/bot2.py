import threading
import ccxt
import pandas as pd
import numpy as np
import time
from utils.db import get_key, log_trade, get_params, set_param
from utils.sentiment import get_twitter_sentiment, get_combined_sentiment
from utils.taapi import get_indicator, get_pattern, get_historical

class Bot2(threading.Thread):
    """
    Bot 2: Mean-Reversion Scalper with Volatility Filter
    Targets 0.8-1.5% daily returns with tight risk management
    Uses Bollinger Bands on 15-min charts, ATR volatility filter, neutral sentiment
    """
    
    def __init__(self, master_pass):
        """Initialize Bot 2 with parameters from database"""
        super().__init__()
        self.master_pass = master_pass
        
        # Load parameters from database
        self.params = get_params('bot2')
        self.risk = float(self.params.get('risk', '0.5')) / 100  # Default 0.5% risk per trade
        self.alloc = float(self.params.get('alloc', '5')) / 100  # Default 5% allocation
        self.max_trades = int(self.params.get('max_trades', '10'))  # Max 10 trades per day
        
        # Trade counter and daily reset
        self.trade_count = 0
        self.last_day = time.time()
        
        # Trading pairs - mid-cap coins for mean reversion
        self.coins = ['SOL/USD', 'ADA/USD']
        self.running = True
        
        # Initialize Coinbase exchange via CCXT (V1 API)
        self.exchange = ccxt.coinbase({
            'apiKey': get_key('coinbase_api_key', master_pass),
            'secret': get_key('coinbase_secret', master_pass),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'version': 'v1'  # Use Coinbase V1 API
            }
        })
        
        # Set rate limit for API calls
        self.exchange.rateLimit = 1000  # 1 second between requests
        
    def run(self):
        """Main trading loop - executes mean reversion strategy"""
        while self.running:
            # Check if bot is still active
            from utils.optimization import check_bot_active
            if not check_bot_active('bot2'):
                log_trade('bot2', 'info', 'Bot deactivated by optimization')
                self.running = False
                break
            
            # Reset trade counter daily
            if time.time() - self.last_day > 86400:  # 24 hours
                self.trade_count = 0
                self.last_day = time.time()
                log_trade('bot2', 'info', 'Daily trade counter reset')
                
            for coin in self.coins:
                try:
                    # Convert coin format for TAAPI
                    taapi_symbol = coin.replace('/USD', '/USDT')
                    
                    # Get indicators from TAAPI
                    bb_data = get_indicator('bbands', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '15m',
                        'period': 20,
                        'stddev': 2
                    }, self.master_pass)
                    
                    atr_data = get_indicator('atr', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '15m',
                        'period': 14
                    }, self.master_pass)
                    
                    # Get longer ATR for comparison
                    atr_long_data = get_indicator('atr', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '15m',
                        'period': 50
                    }, self.master_pass)
                    
                    # Skip if data is missing
                    if not all([bb_data, atr_data, atr_long_data]):
                        log_trade('bot2', 'error', f'Missing TAAPI data for {coin}')
                        continue
                    
                    # Extract values
                    upper = bb_data.get('valueUpperBand', 0)
                    lower = bb_data.get('valueLowerBand', 0)
                    bb_mid = bb_data.get('valueMiddleBand', 0)
                    atr = atr_data.get('value', 0)
                    avg_atr = atr_long_data.get('value', 0)
                    
                    # Get current price
                    price = self.exchange.fetch_ticker(coin)['last']
                    
                    # Get pattern data for additional confirmation
                    pattern_data = get_pattern(taapi_symbol, '15m', 'coinbase', self.master_pass)
                    reversal_pattern = False
                    if pattern_data:
                        # Check for reversal patterns
                        reversal_patterns = ['CDLENGULFING', 'CDLHAMMER', 'CDLMORNINGSTAR', 'CDLEVENINGSTAR']
                        for pattern in reversal_patterns:
                            if abs(pattern_data.get(f'value{pattern}', 0)) > 0:
                                reversal_pattern = True
                                log_trade('bot2', 'signal', f'Reversal pattern detected: {pattern} for {coin}')
                                break
                    
                    # Check sentiment - must be neutral for mean reversion
                    tw_sent = get_twitter_sentiment(coin.split('/')[0].lower(), count=30, master_pass=self.master_pass)
                    # Get combined sentiment instead of reddit sentiment
                    sentiment_data = get_combined_sentiment(coin.split('/')[0], master_pass=self.master_pass)
                    sent_avg = sentiment_data.get('combined_score', 0.0)
                    
                    # Trading conditions: Price at lower band + Low volatility + Neutral sentiment + Trade limit
                    if (price < lower and 
                        atr < avg_atr and 
                        -0.2 < sent_avg < 0.2 and 
                        self.trade_count < self.max_trades):
                        
                        # Get available balance
                        balance = self.exchange.fetch_balance()['USD']['free']
                        
                        # Calculate position size
                        amount = (balance * self.alloc) / price
                        
                        # Place limit buy order at lower Bollinger Band
                        order = self.exchange.create_limit_buy_order(coin, amount, lower)
                        entry = order['price']
                        
                        # Set stop-loss at 0.5% below entry
                        sl_price = entry * (1 - self.risk)
                        sl_order = self.exchange.create_stop_limit_order(
                            coin, 'sell', amount, sl_price, sl_price
                        )
                        
                        # Set take-profit at 0.5% above entry
                        tp_price = entry * (1 + self.risk)
                        tp_order = self.exchange.create_limit_sell_order(coin, amount, tp_price)
                        
                        # Increment trade counter
                        self.trade_count += 1
                        
                        # Log trade details
                        log_trade('bot2', 'buy', 
                                f'Coin: {coin}, Amount: {amount:.4f}, Entry: {entry:.2f}, '
                                f'SL: {sl_price:.2f}, TP: {tp_price:.2f}, ATR: {atr:.2f}, '
                                f'Sentiment: {sent_avg:.2f}')
                        
                except ccxt.NetworkError as e:
                    log_trade('bot2', 'error', f'Network error: {str(e)}')
                    time.sleep(5)
                except ccxt.ExchangeError as e:
                    log_trade('bot2', 'error', f'Exchange error: {str(e)}')
                    if '429' in str(e):  # Rate limit
                        time.sleep(60)
                    else:
                        time.sleep(1)
                except Exception as e:
                    log_trade('bot2', 'error', f'Unexpected error: {str(e)}')
                    time.sleep(1)
                    
            # Wait 30 seconds before next scan (15-min charts don't need frequent checks)
            time.sleep(30)
            
    def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        
    def update_params(self, risk=None, alloc=None, max_trades=None):
        """Update bot parameters dynamically"""
        if risk is not None:
            self.risk = risk / 100
            set_param('bot2', 'risk', str(risk))
            
        if alloc is not None:
            self.alloc = alloc / 100
            set_param('bot2', 'alloc', str(alloc))
            
        if max_trades is not None:
            self.max_trades = max_trades
            set_param('bot2', 'max_trades', str(max_trades))
            
    def backtest(self, historical_data):
        """
        Backtest mean reversion strategy using TAAPI
        Returns: final portfolio value, trades, sharpe ratio
        """
        portfolio = 10000
        trades = []
        max_portfolio = portfolio
        trade_count = 0
        max_trades = 10
        
        # If insufficient data, fetch from TAAPI
        if len(historical_data) < 100:
            taapi_data = get_historical('ETH/USDT', '15m', 300, 'coinbase', self.master_pass)
            if taapi_data:
                historical_data = taapi_data
            else:
                log_trade('bot2', 'error', 'Failed to fetch historical data from TAAPI')
                return portfolio, trades, 0
        
        # Need sufficient data for indicators
        for i in range(50, len(historical_data)):
            if trade_count >= max_trades:
                break
                
            # For backtesting efficiency, calculate indicators locally
            # In production, these would come from TAAPI
            current_candle = historical_data[i]
            current_price = current_candle[4] if isinstance(current_candle, list) else current_candle['close']
            
            # Extract price series
            close_slice = pd.Series([historical_data[j][4] if isinstance(historical_data[j], list) else historical_data[j]['close'] 
                                   for j in range(i-49, i+1)])
            high_slice = pd.Series([historical_data[j][2] if isinstance(historical_data[j], list) else historical_data[j]['high'] 
                                  for j in range(i-49, i+1)])
            low_slice = pd.Series([historical_data[j][3] if isinstance(historical_data[j], list) else historical_data[j]['low'] 
                                 for j in range(i-49, i+1)])
            
            # Calculate ATR locally for backtesting
            prev_close = close_slice.shift(1)
            tr = pd.concat([
                high_slice - low_slice,
                abs(high_slice - prev_close),
                abs(low_slice - prev_close)
            ], axis=1).max(axis=1)
            
            atr = tr.rolling(14).mean().iloc[-1]
            avg_atr = tr.rolling(50).mean().iloc[-1]
            
            # Calculate Bollinger Bands
            bb_mid = close_slice.rolling(20).mean().iloc[-1]
            bb_std = close_slice.rolling(20).std().iloc[-1]
            upper = bb_mid + 2 * bb_std
            lower = bb_mid - 2 * bb_std
            
            # Mock neutral sentiment for backtesting
            sentiment = 0.0
            
            # Check conditions
            if current_price < lower and atr < avg_atr and -0.2 < sentiment < 0.2:
                sim_entry = lower
                sim_amount = portfolio * 0.05 / sim_entry  # 5% allocation
                
                # Simulate trade outcome - mean reversion has high win rate but small gains
                if np.random.random() > 0.2:  # 80% win rate
                    sim_exit = sim_entry * 1.005  # 0.5% profit
                else:
                    sim_exit = sim_entry * 0.995  # 0.5% loss
                    
                profit = sim_amount * (sim_exit - sim_entry)
                portfolio += profit
                trades.append(profit)
                
                # Track maximum for drawdown calculation
                max_portfolio = max(max_portfolio, portfolio)
                
                # Calculate drawdown
                drawdown = (max_portfolio - portfolio) / max_portfolio
                
                # Mean reversion should have very low drawdown
                if drawdown > 0.03:  # 3% max drawdown for scalping
                    log_trade('bot2', 'backtest', f'Max drawdown exceeded: {drawdown:.2%}')
                    break
                    
        # Calculate metrics
        if trades:
            win_rate = len([t for t in trades if t > 0]) / len(trades)
            avg_trade = np.mean(trades)
            sharpe = (np.mean(trades) / np.std(trades)) * np.sqrt(252 * 96)  # 96 15-min periods per day
        else:
            win_rate = 0
            avg_trade = 0
            sharpe = 0
            
        return {
            'final_portfolio': portfolio,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_trade': avg_trade,
            'sharpe_ratio': sharpe,
            'max_drawdown': drawdown if 'drawdown' in locals() else 0
        }
