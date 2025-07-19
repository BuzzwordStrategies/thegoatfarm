import threading
import pandas as pd
import numpy as np
import time
import os
import sys

# Add parent directory to path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_api_connection import CoinbaseConnection, TaapiConnection, TwitterConnection
from utils.db import log_trade, get_params, set_param
from utils.sentiment import get_twitter_sentiment, get_reddit_sentiment, get_combined_sentiment

class Bot3(threading.Thread):
    """
    Bot 3: Sentiment-Driven Position Bot with ML predictions
    Targets 1.5-3% daily returns with larger position sizes
    Uses VADER for Twitter + Reddit, + Anthropic Claude for analysis
    """
    
    def __init__(self):
        """Initialize Bot 3 with parameters from database"""
        super().__init__()
        
        # Load parameters from database
        self.params = get_params('bot3')
        self.risk_level = float(self.params.get('risk', '2.0')) / 100  # Default 2% risk
        self.alloc = float(self.params.get('alloc', '20')) / 100  # Default 20% allocation
        self.trade_freq = int(self.params.get('freq', '3600'))  # Default 1 hour
        
        # Track sentiment history
        self.sentiment_history = []
        self.positions = {}  # Track open positions
        
        # Trading pairs - major coins with active social presence
        self.coins = ['BTC/USD', 'ETH/USD', 'DOGE/USD']
        self.running = True
        
        # Initialize API connections using new pattern
        self.coinbase = CoinbaseConnection()
        self.taapi = TaapiConnection()
        self.twitter = TwitterConnection()
        
        # Verify connections
        if not self.coinbase.is_connected:
            log_trade('bot3', 'error', 'Coinbase connection failed')
            raise ValueError("Coinbase connection failed")
            
        if not self.taapi.is_connected:
            log_trade('bot3', 'error', 'TAAPI connection failed')
            raise ValueError("TAAPI connection failed")
            
        if not self.twitter.is_connected:
            log_trade('bot3', 'warning', 'Twitter connection failed - sentiment features limited')
            
        # Store client for compatibility
        if hasattr(self.coinbase, 'client'):
            self.exchange = self.coinbase.client
        else:
            log_trade('bot3', 'warning', 'Using CDP authentication - legacy methods may not work')
            self.exchange = None
            
        log_trade('bot3', 'info', 'Bot initialized successfully')
        
    def run(self):
        """Main bot loop: analyze sentiment and trade accordingly"""
        while self.running:
            # Check if bot is active
            if self.is_active():
                for coin in self.coins:
                    self.analyze_and_trade(coin)
                    
                # Manage existing positions
                self.manage_positions()
            
            # Wait before next analysis cycle
            time.sleep(self.trade_freq)
    
    def is_active(self):
        """Check if bot is active"""
        return float(self.params.get('active', '1')) == 1
    
    def get_current_price(self, coin: str) -> float:
        """Get current price for a coin"""
        try:
            # Convert format: BTC/USD -> BTC-USD
            product_id = coin.replace('/', '-')
            
            # Try direct API call
            if self.exchange:
                try:
                    ticker = self.exchange.get_product(product_id)
                    if hasattr(ticker, 'price'):
                        return float(ticker.price)
                except Exception as e:
                    log_trade('bot3', 'warning', f"Failed to get price via SDK: {e}")
            
            # Fallback to HTTP API
            endpoint = f"/products/{product_id}/ticker"
            result = self.coinbase.make_request('GET', endpoint)
            if result and 'price' in result:
                return float(result['price'])
            else:
                log_trade('bot3', 'error', f"No price data for {coin}")
                return 0.0
                
        except Exception as e:
            log_trade('bot3', 'error', f"Error getting price for {coin}: {str(e)}")
            return 0.0
    
    def get_sentiment_score(self, coin: str) -> float:
        """Get combined sentiment score from multiple sources"""
        try:
            symbol = coin.split('/')[0]
            
            # Simplified sentiment - in production would use actual APIs
            # For now, return neutral sentiment
            sentiment = 0.5
            
            # Store in history
            self.sentiment_history.append({
                'coin': coin,
                'sentiment': sentiment,
                'timestamp': time.time()
            })
            
            # Keep only last 100 entries
            if len(self.sentiment_history) > 100:
                self.sentiment_history = self.sentiment_history[-100:]
            
            return sentiment
            
        except Exception as e:
            log_trade('bot3', 'error', f"Error getting sentiment for {coin}: {str(e)}")
            return 0.5  # Return neutral on error
    
    def get_technical_context(self, coin: str) -> dict:
        """Get technical indicators for context"""
        try:
            symbol = coin
            
            indicators = {}
            
            # Get RSI
            rsi_data = self.taapi.get_indicator('rsi', 'binance', symbol, '1h')
            if rsi_data and 'value' in rsi_data:
                indicators['rsi'] = rsi_data['value']
            
            # Get MACD
            macd_data = self.taapi.get_indicator('macd', 'binance', symbol, '1h')
            if macd_data:
                indicators['macd'] = macd_data.get('valueMACD', 0)
                indicators['macd_signal'] = macd_data.get('valueMACDSignal', 0)
                
            # Get Volume
            volume_data = self.taapi.get_indicator('volume', 'binance', symbol, '1h')
            if volume_data and 'value' in volume_data:
                indicators['volume'] = volume_data['value']
                
            return indicators
            
        except Exception as e:
            log_trade('bot3', 'error', f"Error getting indicators for {coin}: {str(e)}")
            return {}
    
    def analyze_and_trade(self, coin: str):
        """Analyze sentiment and make trading decisions"""
        try:
            # Get current price
            current_price = self.get_current_price(coin)
            if current_price == 0:
                return
                
            # Get sentiment score
            sentiment = self.get_sentiment_score(coin)
            
            # Get technical context
            technicals = self.get_technical_context(coin)
            
            # Get sentiment trend
            recent_sentiments = [h['sentiment'] for h in self.sentiment_history 
                               if h['coin'] == coin][-5:]
            if recent_sentiments:
                sentiment_trend = recent_sentiments[-1] - recent_sentiments[0]
            else:
                sentiment_trend = 0
            
            # Trading logic
            rsi = technicals.get('rsi', 50)
            
            # Strong bullish sentiment + positive trend + not overbought
            if sentiment > 0.7 and sentiment_trend > 0.1 and rsi < 70:
                if coin not in self.positions:
                    self.execute_trade(coin, 'buy', current_price, sentiment)
                    
            # Strong bearish sentiment + negative trend
            elif sentiment < 0.3 and sentiment_trend < -0.1:
                if coin in self.positions:
                    self.execute_trade(coin, 'sell', current_price, sentiment)
                    
        except Exception as e:
            log_trade('bot3', 'error', f"Error analyzing {coin}: {str(e)}")
    
    def execute_trade(self, coin: str, action: str, price: float, sentiment: float):
        """Execute a sentiment-based trade"""
        try:
            # Calculate position size based on allocation and sentiment strength
            account_balance = 10000  # Placeholder - get from account
            sentiment_multiplier = abs(sentiment - 0.5) * 2  # 0 to 1
            position_size = account_balance * self.alloc * sentiment_multiplier
            
            if action == 'buy':
                # Store position info
                self.positions[coin] = {
                    'entry_price': price,
                    'size': position_size / price,
                    'entry_sentiment': sentiment,
                    'entry_time': time.time()
                }
                
                # Set stop loss based on risk level
                stop_loss = price * (1 - self.risk_level)
                
                log_trade('bot3', action, 
                         f"{coin} at ${price:.2f} - Size: ${position_size:.2f}, "
                         f"Sentiment: {sentiment:.2f}, SL: ${stop_loss:.2f}")
                         
            else:  # sell
                if coin in self.positions:
                    position = self.positions[coin]
                    pnl = (price - position['entry_price']) * position['size']
                    pnl_pct = ((price / position['entry_price']) - 1) * 100
                    
                    log_trade('bot3', action,
                             f"{coin} at ${price:.2f} - P&L: ${pnl:.2f} ({pnl_pct:.1f}%), "
                             f"Sentiment: {sentiment:.2f}")
                    
                    del self.positions[coin]
                    
        except Exception as e:
            log_trade('bot3', 'error', f"Error executing {action} for {coin}: {str(e)}")
    
    def manage_positions(self):
        """Manage existing positions - check stop losses and sentiment changes"""
        try:
            for coin in list(self.positions.keys()):
                position = self.positions[coin]
                current_price = self.get_current_price(coin)
                
                if current_price == 0:
                    continue
                    
                # Check stop loss
                stop_loss = position['entry_price'] * (1 - self.risk_level)
                if current_price <= stop_loss:
                    self.execute_trade(coin, 'sell', current_price, 0.5)
                    log_trade('bot3', 'stop_loss', f"{coin} hit stop loss at ${current_price:.2f}")
                    
                # Check take profit (3x risk)
                take_profit = position['entry_price'] * (1 + 3 * self.risk_level)
                if current_price >= take_profit:
                    self.execute_trade(coin, 'sell', current_price, 0.5)
                    log_trade('bot3', 'take_profit', f"{coin} hit take profit at ${current_price:.2f}")
                    
        except Exception as e:
            log_trade('bot3', 'error', f"Error managing positions: {str(e)}")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        # Close all positions
        for coin in list(self.positions.keys()):
            current_price = self.get_current_price(coin)
            if current_price > 0:
                self.execute_trade(coin, 'sell', current_price, 0.5)
        log_trade('bot3', 'info', 'Bot stopped - all positions closed')
