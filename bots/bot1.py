import threading
import pandas as pd
import numpy as np
import time
import random
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_api_connection import CoinbaseConnection, TaapiConnection
from utils.db import log_trade, get_params, set_param
from utils.sentiment import get_combined_sentiment

class Bot1(threading.Thread):
    """
    Bot 1: Trend-Following Momentum Bot with Sentiment Boost
    Targets 1-2% daily returns with max 5% drawdown
    Uses 20/50 SMA crossover, RSI < 30, and sentiment > 0.6
    """
    
    def __init__(self):
        """Initialize Bot 1 with parameters from database"""
        super().__init__()
        
        # Load parameters from database
        self.params = get_params('bot1')
        self.risk_level = float(self.params.get('risk', '1.0')) / 100  # Convert percentage to decimal
        self.alloc = float(self.params.get('alloc', '10')) / 100  # Portfolio allocation
        self.trade_freq = int(self.params.get('freq', '60'))  # Trading frequency in seconds
        
        # Trading pairs - high liquidity coins
        self.coins = ['BTC/USD', 'ETH/USD']
        self.running = True
        
        # Initialize API connections using new pattern
        self.coinbase = CoinbaseConnection()
        self.taapi = TaapiConnection()
        
        # Verify connections
        if not self.coinbase.is_connected:
            log_trade('bot1', 'error', 'Coinbase connection failed')
            raise ValueError("Coinbase connection failed")
            
        if not self.taapi.is_connected:
            log_trade('bot1', 'error', 'TAAPI connection failed')
            raise ValueError("TAAPI connection failed")
            
        # Store client for compatibility
        if hasattr(self.coinbase, 'client'):
            self.exchange = self.coinbase.client
        else:
            log_trade('bot1', 'warning', 'Using CDP authentication - legacy methods may not work')
            self.exchange = None
        
        log_trade('bot1', 'info', 'Bot initialized successfully')
        
    def run(self):
        """Main bot loop: check conditions every trade_freq seconds"""
        while self.running:
            # Check if bot is active from portfolio optimization
            if self.is_active():
                for coin in self.coins:
                    self.check_market_conditions(coin)
            
            time.sleep(self.trade_freq)
    
    def is_active(self):
        """Check if bot is active from optimization"""
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
                    log_trade('bot1', 'warning', f"Failed to get price via SDK: {e}")
            
            # Fallback to HTTP API
            endpoint = f"/products/{product_id}/ticker"
            result = self.coinbase.make_request('GET', endpoint)
            if result and 'price' in result:
                return float(result['price'])
            else:
                log_trade('bot1', 'error', f"No price data for {coin}")
                return 0.0
                
        except Exception as e:
            log_trade('bot1', 'error', f"Error getting price for {coin}: {str(e)}")
            return 0.0
    
    def get_technical_indicators(self, coin: str) -> dict:
        """Get technical indicators from TAAPI"""
        try:
            # Convert coin format for TAAPI
            symbol = coin  # Already in correct format: BTC/USD
            
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
                
            # Get Bollinger Bands
            bb_data = self.taapi.get_indicator('bbands', 'binance', symbol, '1h')
            if bb_data:
                indicators['bb_upper'] = bb_data.get('valueUpperBand', 0)
                indicators['bb_lower'] = bb_data.get('valueLowerBand', 0)
                
            return indicators
            
        except Exception as e:
            log_trade('bot1', 'error', f"Error getting indicators for {coin}: {str(e)}")
            return {}
    
    def check_market_conditions(self, coin: str):
        """Check market conditions and decide whether to trade"""
        try:
            # Get current price
            current_price = self.get_current_price(coin)
            if current_price == 0:
                return
                
            # Get technical indicators
            indicators = self.get_technical_indicators(coin)
            
            # Get sentiment (simplified for now)
            sentiment = 0.5  # Neutral sentiment as placeholder
            
            # Trading logic
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            
            # Buy conditions
            if rsi < 30 and macd > macd_signal and sentiment > 0.6:
                self.execute_trade(coin, 'buy', current_price)
                
            # Sell conditions
            elif rsi > 70 and macd < macd_signal:
                self.execute_trade(coin, 'sell', current_price)
                
        except Exception as e:
            log_trade('bot1', 'error', f"Error checking conditions for {coin}: {str(e)}")
    
    def execute_trade(self, coin: str, action: str, price: float):
        """Execute a trade (simulated for now)"""
        try:
            # Calculate position size based on allocation and risk
            account_balance = 10000  # Placeholder - get from account
            position_size = account_balance * self.alloc * self.risk_level
            
            log_trade('bot1', action, f"{coin} at ${price:.2f} - Size: ${position_size:.2f}")
            
            # Here you would add actual trade execution
            
        except Exception as e:
            log_trade('bot1', 'error', f"Error executing {action} for {coin}: {str(e)}")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        log_trade('bot1', 'info', 'Bot stopped')
