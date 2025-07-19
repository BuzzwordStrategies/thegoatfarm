import threading
import pandas as pd
import numpy as np
import time
import os
import sys
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.base_api_connection import CoinbaseConnection, TaapiConnection
from utils.db import log_trade, get_params, set_param

class Bot4(threading.Thread):
    """
    Bot 4: Machine Learning Bot with pattern recognition
    Targets 2-4% daily returns using ML predictions
    Uses technical indicators + price patterns for prediction
    """
    
    def __init__(self):
        """Initialize Bot 4 with parameters from database"""
        super().__init__()
        
        # Load parameters from database
        self.params = get_params('bot4')
        self.risk_level = float(self.params.get('risk', '1.5')) / 100  # Default 1.5% risk
        self.alloc = float(self.params.get('alloc', '15')) / 100  # Default 15% allocation
        self.trade_freq = int(self.params.get('freq', '1800'))  # Default 30 minutes
        
        # Trading pairs
        self.coins = ['BTC/USD', 'ETH/USD']
        self.running = True
        
        # ML model components
        self.scaler = StandardScaler()
        self.model = LogisticRegression()
        self.is_trained = False
        self.training_data = []
        
        # Initialize API connections using new pattern
        self.coinbase = CoinbaseConnection()
        self.taapi = TaapiConnection()
        
        # Verify connections
        if not self.coinbase.is_connected:
            log_trade('bot4', 'error', 'Coinbase connection failed')
            raise ValueError("Coinbase connection failed")
            
        if not self.taapi.is_connected:
            log_trade('bot4', 'error', 'TAAPI connection failed')
            raise ValueError("TAAPI connection failed")
            
        # Store client for compatibility
        if hasattr(self.coinbase, 'client'):
            self.exchange = self.coinbase.client
        else:
            log_trade('bot4', 'warning', 'Using CDP authentication - legacy methods may not work')
            self.exchange = None
            
        log_trade('bot4', 'info', 'Bot initialized successfully')
        
    def run(self):
        """Main bot loop: collect data, train model, make predictions"""
        while self.running:
            # Check if bot is active
            if self.is_active():
                # Collect training data initially
                if len(self.training_data) < 100:
                    self.collect_training_data()
                    
                # Train model when we have enough data
                elif not self.is_trained and len(self.training_data) >= 100:
                    self.train_model()
                    
                # Make predictions and trade
                elif self.is_trained:
                    for coin in self.coins:
                        self.predict_and_trade(coin)
            
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
                    log_trade('bot4', 'warning', f"Failed to get price via SDK: {e}")
            
            # Fallback to HTTP API
            endpoint = f"/products/{product_id}/ticker"
            result = self.coinbase.make_request('GET', endpoint)
            if result and 'price' in result:
                return float(result['price'])
            else:
                log_trade('bot4', 'error', f"No price data for {coin}")
                return 0.0
                
        except Exception as e:
            log_trade('bot4', 'error', f"Error getting price for {coin}: {str(e)}")
            return 0.0
    
    def get_features(self, coin: str) -> dict:
        """Get technical indicator features for ML model"""
        try:
            symbol = coin
            features = {}
            
            # Get RSI
            rsi_data = self.taapi.get_indicator('rsi', 'binance', symbol, '30m')
            if rsi_data and 'value' in rsi_data:
                features['rsi'] = rsi_data['value']
            
            # Get MACD
            macd_data = self.taapi.get_indicator('macd', 'binance', symbol, '30m')
            if macd_data:
                features['macd'] = macd_data.get('valueMACD', 0)
                features['macd_signal'] = macd_data.get('valueMACDSignal', 0)
                features['macd_hist'] = features['macd'] - features['macd_signal']
            
            # Get Bollinger Bands
            bb_data = self.taapi.get_indicator('bbands', 'binance', symbol, '30m')
            if bb_data:
                features['bb_upper'] = bb_data.get('valueUpperBand', 0)
                features['bb_middle'] = bb_data.get('valueMiddleBand', 0)
                features['bb_lower'] = bb_data.get('valueLowerBand', 0)
                
                # Calculate BB position (where price is relative to bands)
                current_price = self.get_current_price(coin)
                if current_price > 0 and features['bb_upper'] > features['bb_lower']:
                    features['bb_position'] = (current_price - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
                else:
                    features['bb_position'] = 0.5
            
            # Get Stochastic
            stoch_data = self.taapi.get_indicator('stoch', 'binance', symbol, '30m')
            if stoch_data:
                features['stoch_k'] = stoch_data.get('valueK', 50)
                features['stoch_d'] = stoch_data.get('valueD', 50)
            
            # Get ATR for volatility
            atr_data = self.taapi.get_indicator('atr', 'binance', symbol, '30m')
            if atr_data and 'value' in atr_data:
                features['atr'] = atr_data['value']
                
            return features
            
        except Exception as e:
            log_trade('bot4', 'error', f"Error getting features for {coin}: {str(e)}")
            return {}
    
    def collect_training_data(self):
        """Collect features and labels for training"""
        try:
            for coin in self.coins:
                features = self.get_features(coin)
                if len(features) >= 5:  # Ensure we have enough features
                    # Get current price
                    current_price = self.get_current_price(coin)
                    
                    # Store with timestamp for future labeling
                    self.training_data.append({
                        'coin': coin,
                        'features': features,
                        'price': current_price,
                        'timestamp': time.time()
                    })
                    
            # Clean old data (keep last 500 samples)
            if len(self.training_data) > 500:
                self.training_data = self.training_data[-500:]
                
            log_trade('bot4', 'info', f"Collected training data - {len(self.training_data)} samples")
            
        except Exception as e:
            log_trade('bot4', 'error', f"Error collecting training data: {str(e)}")
    
    def train_model(self):
        """Train ML model on collected data"""
        try:
            # Need at least 30 minutes of future data to label
            labeled_data = []
            
            for i in range(len(self.training_data) - 10):
                current = self.training_data[i]
                future = self.training_data[i + 10]  # 30 min future (with 3 min intervals)
                
                if current['coin'] == future['coin']:
                    # Label: 1 if price went up by > 0.5%, 0 otherwise
                    price_change = (future['price'] - current['price']) / current['price']
                    label = 1 if price_change > 0.005 else 0
                    
                    labeled_data.append({
                        'features': list(current['features'].values()),
                        'label': label
                    })
            
            if len(labeled_data) >= 50:
                # Prepare data for training
                X = np.array([d['features'] for d in labeled_data])
                y = np.array([d['label'] for d in labeled_data])
                
                # Handle any NaN values
                X = np.nan_to_num(X)
                
                # Scale features
                X_scaled = self.scaler.fit_transform(X)
                
                # Train model
                self.model.fit(X_scaled, y)
                
                # Calculate training accuracy
                accuracy = self.model.score(X_scaled, y)
                
                self.is_trained = True
                log_trade('bot4', 'info', f"Model trained - Accuracy: {accuracy:.2%}")
            else:
                log_trade('bot4', 'info', "Not enough labeled data for training yet")
                
        except Exception as e:
            log_trade('bot4', 'error', f"Error training model: {str(e)}")
    
    def predict_and_trade(self, coin: str):
        """Make prediction and execute trade if confident"""
        try:
            # Get current features
            features = self.get_features(coin)
            if len(features) < 5:
                return
                
            # Prepare features for prediction
            X = np.array([list(features.values())])
            X = np.nan_to_num(X)
            X_scaled = self.scaler.transform(X)
            
            # Get prediction and probability
            prediction = self.model.predict(X_scaled)[0]
            probability = self.model.predict_proba(X_scaled)[0]
            
            # Get confidence (how sure the model is)
            confidence = max(probability)
            
            # Only trade if confidence > 70%
            if confidence > 0.7:
                current_price = self.get_current_price(coin)
                
                if prediction == 1:  # Buy signal
                    self.execute_trade(coin, 'buy', current_price, confidence)
                else:  # Potential sell signal (if we have position)
                    # In a real implementation, check if we have open position
                    pass
                    
        except Exception as e:
            log_trade('bot4', 'error', f"Error in prediction for {coin}: {str(e)}")
    
    def execute_trade(self, coin: str, action: str, price: float, confidence: float):
        """Execute ML-based trade"""
        try:
            # Calculate position size based on allocation and confidence
            account_balance = 10000  # Placeholder - get from account
            confidence_multiplier = (confidence - 0.7) / 0.3  # Scale 0.7-1.0 to 0-1
            position_size = account_balance * self.alloc * confidence_multiplier
            
            # Set stop loss and take profit based on confidence
            if action == 'buy':
                stop_loss = price * (1 - self.risk_level)
                take_profit = price * (1 + 2 * self.risk_level)  # 2:1 risk reward
                
                log_trade('bot4', action,
                         f"{coin} at ${price:.2f} - Size: ${position_size:.2f}, "
                         f"Confidence: {confidence:.1%}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
                
                # Here you would add actual trade execution
                
        except Exception as e:
            log_trade('bot4', 'error', f"Error executing {action} for {coin}: {str(e)}")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        log_trade('bot4', 'info', 'Bot stopped')
