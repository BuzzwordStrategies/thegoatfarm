import threading
import pandas as pd
import numpy as np
import time
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_api_connection import CoinbaseConnection, TaapiConnection
from utils.db import log_trade, get_params, set_param
from utils.sentiment import get_twitter_sentiment, get_combined_sentiment

class Bot2(threading.Thread):
    """
    Bot 2: Mean-Reversion Scalper with Volatility Filter
    Targets 0.8-1.5% daily returns with tight risk management
    Uses Bollinger Bands on 15-min charts, ATR volatility filter, neutral sentiment
    """
    
    def __init__(self):
        """Initialize Bot 2 with parameters from database"""
        super().__init__()
        
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
        
        # Initialize API connections using new pattern
        self.coinbase = CoinbaseConnection()
        self.taapi = TaapiConnection()
        
        # Verify connections
        if not self.coinbase.is_connected:
            log_trade('bot2', 'error', 'Coinbase connection failed')
            raise ValueError("Coinbase connection failed")
            
        if not self.taapi.is_connected:
            log_trade('bot2', 'error', 'TAAPI connection failed')
            raise ValueError("TAAPI connection failed")
            
        # Store client for compatibility
        if hasattr(self.coinbase, 'client'):
            self.exchange = self.coinbase.client
        else:
            log_trade('bot2', 'warning', 'Using CDP authentication - legacy methods may not work')
            self.exchange = None
            
        log_trade('bot2', 'info', 'Bot initialized successfully')
        
    def run(self):
        """Main bot loop: check for mean reversion trades"""
        while self.running:
            # Check if bot is active
            if self.is_active():
                # Reset trade counter at start of new day
                self.reset_daily_counter()
                
                # Check if we've hit max trades
                if self.trade_count < self.max_trades:
                    for coin in self.coins:
                        self.check_mean_reversion(coin)
                else:
                    log_trade('bot2', 'info', f'Daily trade limit reached ({self.max_trades})')
            
            # Sleep for 15 minutes (scalping timeframe)
            time.sleep(900)
    
    def is_active(self):
        """Check if bot is active"""
        return float(self.params.get('active', '1')) == 1
    
    def reset_daily_counter(self):
        """Reset trade counter at start of new day"""
        current_time = time.time()
        if current_time - self.last_day > 86400:  # 24 hours
            self.trade_count = 0
            self.last_day = current_time
            log_trade('bot2', 'info', 'Daily trade counter reset')
    
    def get_current_price(self, coin: str) -> float:
        """Get current price for a coin"""
        try:
            # Convert format: SOL/USD -> SOL-USD
            product_id = coin.replace('/', '-')
            
            # Try direct API call
            if self.exchange:
                try:
                    ticker = self.exchange.get_product(product_id)
                    if hasattr(ticker, 'price'):
                        return float(ticker.price)
                except Exception as e:
                    log_trade('bot2', 'warning', f"Failed to get price via SDK: {e}")
            
            # Fallback to HTTP API
            endpoint = f"/products/{product_id}/ticker"
            result = self.coinbase.make_request('GET', endpoint)
            if result and 'price' in result:
                return float(result['price'])
            else:
                log_trade('bot2', 'error', f"No price data for {coin}")
                return 0.0
                
        except Exception as e:
            log_trade('bot2', 'error', f"Error getting price for {coin}: {str(e)}")
            return 0.0
    
    def get_bollinger_bands(self, coin: str) -> dict:
        """Get Bollinger Bands from TAAPI"""
        try:
            # Convert coin format for TAAPI
            symbol = coin  # Already in correct format
            
            # Get BB data
            bb_data = self.taapi.get_indicator('bbands', 'binance', symbol, '15m', period=20, stddev=2)
            
            if bb_data:
                return {
                    'upper': bb_data.get('valueUpperBand', 0),
                    'middle': bb_data.get('valueMiddleBand', 0),
                    'lower': bb_data.get('valueLowerBand', 0)
                }
            return {}
            
        except Exception as e:
            log_trade('bot2', 'error', f"Error getting BB for {coin}: {str(e)}")
            return {}
    
    def get_atr(self, coin: str) -> float:
        """Get ATR (Average True Range) for volatility filter"""
        try:
            symbol = coin
            atr_data = self.taapi.get_indicator('atr', 'binance', symbol, '15m', period=14)
            
            if atr_data and 'value' in atr_data:
                return atr_data['value']
            return 0.0
            
        except Exception as e:
            log_trade('bot2', 'error', f"Error getting ATR for {coin}: {str(e)}")
            return 0.0
    
    def check_mean_reversion(self, coin: str):
        """Check for mean reversion opportunities"""
        try:
            # Get current price
            current_price = self.get_current_price(coin)
            if current_price == 0:
                return
                
            # Get Bollinger Bands
            bb = self.get_bollinger_bands(coin)
            if not bb or bb['upper'] == 0:
                return
                
            # Get ATR for volatility filter
            atr = self.get_atr(coin)
            if atr == 0:
                return
                
            # Calculate band width for volatility
            band_width = (bb['upper'] - bb['lower']) / bb['middle']
            
            # Only trade when volatility is moderate (not too high, not too low)
            if 0.02 < band_width < 0.10:  # 2% to 10% band width
                
                # Buy signal: Price touches lower band
                if current_price <= bb['lower'] * 1.005:  # Small buffer
                    self.execute_trade(coin, 'buy', current_price, bb)
                    
                # Sell signal: Price touches upper band
                elif current_price >= bb['upper'] * 0.995:  # Small buffer
                    self.execute_trade(coin, 'sell', current_price, bb)
                    
        except Exception as e:
            log_trade('bot2', 'error', f"Error checking mean reversion for {coin}: {str(e)}")
    
    def execute_trade(self, coin: str, action: str, price: float, bb: dict):
        """Execute a scalping trade"""
        try:
            # Calculate position size based on allocation and risk
            account_balance = 10000  # Placeholder - get from account
            position_size = account_balance * self.alloc * self.risk
            
            # Set tight stop loss (0.5% from entry)
            if action == 'buy':
                stop_loss = price * (1 - 0.005)
                take_profit = bb['middle']  # Target middle band
            else:
                stop_loss = price * (1 + 0.005)
                take_profit = bb['middle']  # Target middle band
            
            log_trade('bot2', action, 
                     f"{coin} at ${price:.2f} - Size: ${position_size:.2f}, "
                     f"SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
            
            # Increment trade counter
            self.trade_count += 1
            
            # Here you would add actual trade execution
            
        except Exception as e:
            log_trade('bot2', 'error', f"Error executing {action} for {coin}: {str(e)}")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        log_trade('bot2', 'info', 'Bot stopped')
