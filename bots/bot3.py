import threading
import ccxt
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
from utils.db import get_key, log_trade, get_params, set_param
from utils.sentiment import get_combined_sentiment, get_coindesk_news, get_grok_sentiment
from utils.taapi import get_indicator, get_pattern, get_historical
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class Bot3(threading.Thread):
    """
    Bot 3: News-Driven Breakout Bot with Sentiment and Arbitrage Edge
    Targets 6-9% daily returns using news catalysts and technical breakouts
    Uses NewsAPI, Donchian Channels, and triangular arbitrage opportunities
    """
    
    def __init__(self, master_pass):
        """Initialize Bot 3 with parameters and exchange connections"""
        super().__init__()
        self.master_pass = master_pass
        self.running = True
        
        # Load parameters from database
        self.params = get_params('bot3')
        if not self.params:
            self.params = {
                'risk_level': 1.5,  # 1.5% stop-loss
                'allocation': 8.0,  # 8% portfolio allocation
                'arbitrage_freq': 300  # Check arbitrage every 5 minutes
            }
        
        # Initialize exchange connection (V1 API)
        self.exchange = ccxt.coinbase({
            'apiKey': get_key('COINBASE_KEY_NAME', master_pass) or get_key('coinbase_api_key', master_pass),
            'secret': get_key('COINBASE_PRIVATE_KEY', master_pass) or get_key('coinbase_secret', master_pass),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'version': 'v3'  # Use new Advanced Trade API
            }
        })
        
        # Initialize sentiment analyzer
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Trading pairs for news-driven breakouts
        self.pairs = ['ETH/USD', 'MATIC/USD']
        
        # Triangular arbitrage paths
        self.tri_paths = [['BTC/USD', 'ETH/BTC', 'ETH/USD']]
        
        # Track last news check time
        self.last_news_time = 0
        self.last_arbitrage_time = 0
        
    def run(self):
        """Main trading loop - monitors news, sentiment, and breakouts"""
        while self.running:
            # Check if bot is still active
            from utils.optimization import check_bot_active
            if not check_bot_active('bot3'):
                log_trade('bot3', 'info', 'Bot deactivated by optimization')
                self.running = False
                break
                
            try:
                for pair in self.pairs:
                    # Convert for TAAPI
                    taapi_symbol = pair.replace('/USD', '/USDT')
                    
                    # Get ATR from TAAPI
                    atr_data = get_indicator('atr', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '30m',
                        'period': 14
                    }, self.master_pass)
                    
                    # Get longer ATR for comparison
                    atr_avg_data = get_indicator('atr', {
                        'exchange': 'coinbase',
                        'symbol': taapi_symbol,
                        'interval': '30m',
                        'period': 20
                    }, self.master_pass)
                    
                    # Get pattern recognition
                    pattern_data = get_pattern(taapi_symbol, '30m', 'coinbase', self.master_pass)
                    
                    if not atr_data or not atr_avg_data:
                        log_trade('bot3', 'error', f'Missing TAAPI data for {pair}')
                        continue
                    
                    atr = atr_data.get('value', 0)
                    atr_avg = atr_avg_data.get('value', 0)
                    
                    # Check for breakout patterns
                    breakout_pattern = False
                    if pattern_data:
                        breakout_patterns = ['CDLBREAKAWAY', 'CDLMORNINGSTAR', 'CDLTHREEWHITESOLDIERS']
                        for pattern in breakout_patterns:
                            if pattern_data.get(f'value{pattern}', 0) > 0:
                                breakout_pattern = True
                                log_trade('bot3', 'signal', f'Breakout pattern detected: {pattern} for {pair}')
                                break
                    
                    # Get general sentiment from Twitter/Reddit
                    sentiment_data = get_combined_sentiment(pair.split('/')[0], self.master_pass)
                    sentiment = sentiment_data['combined_score']
                    
                    # Check news every hour
                    if time.time() - self.last_news_time > 3600:
                        # Get news for the coin
                        news = self._get_news(pair.split('/')[0])
                        
                        # Analyze news sentiment
                        news_sent = self._analyze_news_sentiment(news)
                        
                        # If both news and general sentiment are bullish, or breakout pattern detected
                        if (news_sent > 0.7 and sentiment > 0.7) or breakout_pattern:
                            # Get price data for breakout check
                            df = pd.DataFrame(
                                self.exchange.fetch_ohlcv(pair, '30m', limit=100),
                                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                            )
                            # Check for technical breakout
                            self._check_breakout(df, pair, news_sent, sentiment)
                        
                        self.last_news_time = time.time()
                    
                    # Only trade when volatility is above average (trending market)
                    if atr > atr_avg:
                        # Additional breakout check without news requirement
                        self._check_breakout(df, pair, 0.0, sentiment)
                
                # Check for arbitrage opportunities
                if time.time() - self.last_arbitrage_time > self.params.get('arbitrage_freq', 300):
                    self._arbitrage_check()
                    self.last_arbitrage_time = time.time()
                
                # Sleep between scans
                time.sleep(30)
                
            except ccxt.NetworkError as e:
                log_trade('bot3', 'error', f'Network error: {str(e)}')
                time.sleep(5)  # Retry after 5 seconds
            except ccxt.ExchangeError as e:
                log_trade('bot3', 'error', f'Exchange error: {str(e)}')
                if '429' in str(e):  # Rate limit
                    time.sleep(60)
                else:
                    time.sleep(5)
            except Exception as e:
                log_trade('bot3', 'error', f'Unexpected error: {str(e)}')
                time.sleep(60)
    
    def _get_news(self, coin):
        """Fetch news from Coindesk API for the specified coin"""
        try:
            # Use our new get_coindesk_news function
            articles = get_coindesk_news(coin, master_pass=self.master_pass)
            return articles[:20]  # Return top 20 articles
        except Exception as e:
            log_trade('bot3', 'error', f'News fetch error: {str(e)}')
            return []
    
    def _analyze_news_sentiment(self, articles):
        """Analyze sentiment of news articles using VADER"""
        if not articles:
            return 0.0
            
        scores = []
        for article in articles:
            if article and article.get('title'):
                # Combine title and description for sentiment analysis
                text = article['title'] + ' ' + article.get('description', '')
                # Get VADER compound score
                score = self.analyzer.polarity_scores(text)['compound']
                scores.append(score)
        
        return np.mean(scores) if scores else 0.0
    
    def _calc_atr(self, df):
        """Calculate Average True Range using TAAPI data"""
        # This is now deprecated - we use TAAPI directly
        # Keeping for backward compatibility in backtesting
        prev_close = df['close'].shift(1)
        true_range = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - prev_close),
            abs(df['low'] - prev_close)
        ], axis=1).max(axis=1)
        return true_range.rolling(14).mean()
    
    def _check_breakout(self, df, pair, news_sentiment, general_sentiment):
        """
        Check for Donchian Channel breakout and execute trades
        Donchian Channel: channel_high = rolling max of highs over 20 periods
        Breakout occurs when current close > previous channel high
        """
        try:
            # Calculate Donchian Channel (20-period)
            # Example: highs = df['high'][-20:], channel_high = highs.max()
            channel_high = df['high'].rolling(20).max()
            channel_low = df['low'].rolling(20).min()
            
            current_price = df['close'].iloc[-1]
            prev_channel_high = channel_high.iloc[-2]
            
            # Breakout condition: price breaks above channel high
            if current_price > prev_channel_high:
                # Combined sentiment check (news weighted 50% for this bot)
                combined_sentiment = (news_sentiment * 0.5 + general_sentiment * 0.5)
                
                if combined_sentiment > 0.7:
                    # Get available balance
                    balance = self.exchange.fetch_balance()['USD']['free']
                    
                    # Calculate position size (8% default allocation)
                    allocation = self.params.get('allocation', 8.0) / 100
                    size = (balance * allocation) / current_price
                    
                    # Check minimum order size (e.g., 0.001 BTC equivalent)
                    min_order_value = 10  # $10 minimum
                    if size * current_price >= min_order_value:
                        # Execute market buy order
                        order = self.exchange.create_market_buy_order(pair, size)
                        entry_price = order.get('price', current_price)
                        
                        # Set stop-loss at 1.5% below entry
                        stop_price = entry_price * (1 - self.params.get('risk_level', 1.5) / 100)
                        sl_order = self.exchange.create_stop_loss_order(
                            pair, 'sell', size, stop_price
                        )
                        
                        # Set take-profit at 5% above entry (3:1 risk-reward ratio)
                        tp_price = entry_price * (1 + 5 / 100)
                        tp_order = self.exchange.create_take_profit_order(
                            pair, 'sell', size, tp_price
                        )
                        
                        # Log trade details
                        log_trade('bot3', 'buy', 
                                f'Breakout buy {pair} size {size:.6f} at {entry_price:.2f}, '
                                f'SL: {stop_price:.2f}, TP: {tp_price:.2f}, '
                                f'News sent: {news_sentiment:.2f}, General sent: {general_sentiment:.2f}')
                        
        except Exception as e:
            log_trade('bot3', 'error', f'Breakout check error: {str(e)}')
    
    def _arbitrage_check(self):
        """
        Check for triangular arbitrage opportunities
        Path example: BTC/USD → ETH/BTC → ETH/USD
        Profit = (1 / price1) * price2 * price3 - 1
        Execute if profit > 0.1% after fees
        """
        try:
            for path in self.tri_paths:
                # Get current prices for the triangular path
                ticker1 = self.exchange.fetch_ticker(path[0])
                ticker2 = self.exchange.fetch_ticker(path[1])
                ticker3 = self.exchange.fetch_ticker(path[2])
                
                # Use ask/bid prices for realistic calculation
                p1 = ticker1['ask']  # Buy BTC with USD
                p2 = ticker2['bid']  # Sell ETH for BTC
                p3 = ticker3['bid']  # Sell ETH for USD
                
                # Calculate arbitrage opportunity
                # Start with 1 USD → BTC → ETH → USD
                arb = (1 / p1) * p2 * p3 - 1
                
                # Account for fees (0.05% taker fee * 3 trades)
                net_arb = arb - 0.0015
                
                if net_arb > 0.001:  # 0.1% profit after fees
                    # Execute arbitrage trades
                    balance = self.exchange.fetch_balance()['USD']['free']
                    arb_amount = balance * 0.1  # Use 10% of balance for arbitrage
                    
                    if arb_amount > 100:  # Minimum $100 for arbitrage
                        # Execute the three trades
                        # Note: In production, these should be atomic or very fast
                        try:
                            # Trade 1: Buy BTC with USD
                            btc_amount = arb_amount / p1
                            order1 = self.exchange.create_market_buy_order(path[0], btc_amount)
                            
                            # Trade 2: Buy ETH with BTC
                            eth_amount = btc_amount * p2
                            order2 = self.exchange.create_market_buy_order(path[1], eth_amount)
                            
                            # Trade 3: Sell ETH for USD
                            order3 = self.exchange.create_market_sell_order(path[2], eth_amount)
                            
                            # Log arbitrage trade
                            log_trade('bot3', 'arbitrage',
                                    f'Arb opportunity {net_arb:.4f} on {path}, '
                                    f'Amount: ${arb_amount:.2f}')
                        except Exception as e:
                            log_trade('bot3', 'error', f'Arbitrage execution error: {str(e)}')
                
        except Exception as e:
            log_trade('bot3', 'error', f'Arbitrage check error: {str(e)}')
    
    def stop(self):
        """Stop the bot gracefully"""
        self.running = False
    
    def update_params(self, new_params):
        """Update bot parameters dynamically"""
        for k, v in new_params.items():
            self.params[k] = v
            set_param('bot3', k, str(v))
    
    def backtest(self, historical_data, mock_sentiment=0.7, mock_news_sent=0.8):
        """
        Backtest news-driven strategy using TAAPI
        Uses mock sentiment since we can't fetch historical sentiment
        """
        portfolio = 10000
        trades = []
        max_portfolio = portfolio
        
        # If insufficient data, fetch from TAAPI
        if len(historical_data) < 100:
            taapi_data = get_historical('SOL/USDT', '30m', 300, 'coinbase', self.master_pass)
            if taapi_data:
                historical_data = taapi_data
            else:
                log_trade('bot3', 'error', 'Failed to fetch historical data from TAAPI')
                return portfolio, trades, 0
        
        for i in range(50, len(historical_data)):
            # For backtesting, calculate indicators locally
            candles = historical_data[:i+1]
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) if isinstance(candles[0], list) else pd.DataFrame(candles)
            
            # Calculate local ATR for efficiency
            atr_series = self._calc_atr(df)
            atr = atr_series.iloc[-1]
            atr_avg = atr_series.rolling(20).mean().iloc[-1]
            
            # Check for breakout
            if df['close'].iloc[-1] > df['high'].rolling(20).max().iloc[-2] and mock_sentiment > 0.7 and mock_news_sent > 0.7:
                # Simulate trade
                allocation = self.params.get('allocation', 8.0) / 100
                trade_amount = portfolio * allocation
                size = trade_amount / df['close'].iloc[-1]
                
                # Simulate outcome (60% win rate for news-driven trades)
                if np.random.random() < 0.6:
                    # Win: 5% profit
                    exit_price = df['close'].iloc[-1] * 1.05
                else:
                    # Loss: 1.5% stop-loss
                    exit_price = df['close'].iloc[-1] * 0.985
                
                profit = size * (exit_price - df['close'].iloc[-1])
                portfolio += profit
                
                trades.append({
                    'entry': df['close'].iloc[-1],
                    'exit': exit_price,
                    'size': size,
                    'profit': profit,
                    'return': profit / trade_amount
                })
                
                # Update max portfolio for drawdown calculation
                max_portfolio = max(max_portfolio, portfolio)
                
                # Calculate drawdown
                drawdown = (max_portfolio - portfolio) / max_portfolio * 100
                
                # Stop if drawdown exceeds 4%
                if drawdown > 4:
                    log_trade('bot3', 'backtest', f'Max drawdown exceeded: {drawdown:.2f}%')
                    break
        
        # Calculate performance metrics
        if trades:
            returns = pd.Series([t['return'] for t in trades])
            sharpe = returns.mean() / returns.std() * np.sqrt(365) if returns.std() else 0
            avg_return = returns.mean() * 100
            win_rate = len([t for t in trades if t['profit'] > 0]) / len(trades)
        else:
            sharpe = 0
            avg_return = 0
            win_rate = 0
        
        return {
            'final_value': portfolio,
            'trades': trades,
            'sharpe': sharpe,
            'avg_return': avg_return,
            'win_rate': win_rate,
            'max_drawdown': drawdown if 'drawdown' in locals() else 0
        }
