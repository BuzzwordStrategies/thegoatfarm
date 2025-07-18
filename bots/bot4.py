import threading
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from utils.db import get_key, log_trade, get_params, set_param
from utils.sentiment import get_combined_sentiment
from anthropic import Anthropic
from utils.taapi import get_indicator, get_pattern, get_bulk, get_historical, build_bulk_query

class Bot4(threading.Thread):
    """
    Bot 4: Machine-Learning-Powered Range Scalper with Sentiment and Volume Surge
    Uses Random Forest to predict range-bound conditions
    Targets 5-8% daily returns with tight risk management
    """
    
    def __init__(self, master_pass):
        """Initialize Bot 4 with ML model and parameters"""
        super().__init__()
        self.master_pass = master_pass
        self.running = True
        
        # Load parameters from database
        self.params = get_params('bot4')
        if not self.params:
            self.params = {
                'risk_level': 0.5,  # 0.5% stop-loss
                'allocation': 7.0,  # 7% portfolio allocation
                'retrain_interval': 604800,  # 1 week in seconds
                'trade_freq': 60  # Trade frequency in seconds
            }
        
        # Set trade frequency (was missing)
        self.trade_freq = int(self.params.get('trade_freq', 60))
        self.risk_level = float(self.params.get('risk_level', 0.5)) / 100
        self.allocation = float(self.params.get('allocation', 7.0)) / 100
        
        # Initialize exchange connection (V1 API)
        try:
            self.exchange = ccxt.coinbase({
                'apiKey': get_key('coinbase_api_key', master_pass),
                'secret': get_key('coinbase_secret', master_pass),
                'enableRateLimit': True,
                'rateLimit': 1000,
                'options': {
                    'defaultType': 'spot',
                    'version': 'v1'  # Use Coinbase V1 API
                }
            })
        except Exception as e:
            log_trade('bot4', 'error', f'Failed to initialize exchange: {str(e)}')
            self.exchange = None
        
        # Train ML model on initialization
        self.model = self._train_model()
        self.last_retrain = time.time()
        
        # Trading pairs for range scalping
        self.pairs = ['ADA/USD', 'SOL/USD']
        
    def _train_model(self):
        """
        Train Random Forest model to predict range-bound conditions
        Features: RSI(14), MACD(12,26,9), volume delta
        Label: 1 if price within 2% of SMA50, else 0
        """
        try:
            # Fetch historical data from TAAPI for training
            taapi_data = get_historical('ADA/USDT', '1h', 50, 'coinbase', self.master_pass)
            
            if not taapi_data or len(taapi_data) < 50:
                # Fallback to CCXT if TAAPI fails
                data = self._fetch_historical('ADA/USD', '1h', 1000)
                
                if data is None or len(data) < 100:
                    log_trade('bot4', 'warning', 'Insufficient data for training, using default model')
                    return RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                # Convert TAAPI data to DataFrame
                data = pd.DataFrame(taapi_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Extract features
            features = self._extract_features(data)
            
            # Create labels: 1 if price is within 2% of SMA50 (range-bound)
            sma50 = data['close'].rolling(50).mean()
            price_deviation = np.abs(data['close'] - sma50) / sma50
            labels = (price_deviation < 0.02).astype(int)
            
            # Remove NaN values
            valid_indices = ~np.isnan(features).any(axis=1) & ~np.isnan(labels)
            features = features[valid_indices]
            labels = labels[valid_indices]
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            model.fit(features, labels)
            
            log_trade('bot4', 'ml_training', f'Model trained with {len(features)} samples')
            return model
            
        except Exception as e:
            log_trade('bot4', 'error', f'Error training ML model: {str(e)}')
            return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def _fetch_historical(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Fetch historical data from exchange via CCXT"""
        try:
            if not self.exchange:
                return None
                
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            log_trade('bot4', 'error', f'Error fetching historical data: {str(e)}')
            return None
    
    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract ML features from price data"""
        try:
            # Calculate RSI
            rsi = self._calculate_rsi(data['close'], period=14)
            
            # Calculate MACD
            macd_line, signal_line, histogram = self._calculate_macd(data['close'])
            
            # Calculate volume delta
            volume_delta = data['volume'].pct_change()
            
            # Calculate volatility (ATR)
            atr = self._calculate_atr(data['high'], data['low'], data['close'], period=14)
            
            # Combine features
            features = np.column_stack([rsi, macd_line, signal_line, histogram, volume_delta, atr])
            
            return features
        except Exception as e:
            log_trade('bot4', 'error', f'Error extracting features: {str(e)}')
            return np.array([])
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> np.ndarray:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.values
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> np.ndarray:
        """Calculate Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr.values
    
    def predict_range_condition(self, symbol: str) -> float:
        """Predict if market is range-bound using ML model"""
        try:
            # Get current indicators from TAAPI
            rsi_data = get_indicator('rsi', {
                'exchange': 'coinbase',
                'symbol': symbol.replace('/', ''),
                'interval': '1h',
                'period': 14
            }, self.master_pass)
            
            macd_data = get_indicator('macd', {
                'exchange': 'coinbase',
                'symbol': symbol.replace('/', ''),
                'interval': '1h'
            }, self.master_pass)
            
            # Get current price data for volume calculation
            if self.exchange:
                ticker = self.exchange.fetch_ticker(symbol)
                volume_24h = ticker.get('quoteVolume', 0)
            else:
                volume_24h = 0
            
            # Default values if API fails
            rsi = rsi_data.get('value', 50) if rsi_data else 50
            macd = macd_data.get('value', 0) if macd_data else 0
            signal = macd_data.get('signal', 0) if macd_data else 0
            histogram = macd_data.get('histogram', 0) if macd_data else 0
            
            # Create feature vector
            features = np.array([[rsi, macd, signal, histogram, 0, 0]])  # Simplified for real-time
            
            # Predict range condition
            if hasattr(self.model, 'predict_proba'):
                probability = self.model.predict_proba(features)[0][1]  # Probability of range-bound
                return probability
            else:
                return 0.5  # Default if model not trained
                
        except Exception as e:
            log_trade('bot4', 'error', f'Error predicting range condition: {str(e)}')
            return 0.5
    
    def calculate_position_size(self, symbol: str, entry_price: float) -> float:
        """Calculate position size based on risk management"""
        try:
            if not self.exchange:
                return 0.0
                
            balance = self.exchange.fetch_balance()
            usd_balance = balance.get('USD', {}).get('free', 0)
            
            # Portfolio allocation for this bot
            allocated_capital = usd_balance * self.allocation
            
            # Position size based on risk level
            position_value = allocated_capital * 0.2  # Use 20% of allocated capital per trade
            position_size = position_value / entry_price
            
            return position_size
            
        except Exception as e:
            log_trade('bot4', 'error', f'Error calculating position size: {str(e)}')
            return 0.0
    
    def execute_trade(self, symbol: str, side: str, amount: float, price: float = None):
        """Execute a trade with proper error handling"""
        try:
            if not self.exchange:
                log_trade('bot4', 'error', 'Exchange not initialized')
                return None
                
            # Create order
            if price:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                order = self.exchange.create_market_order(symbol, side, amount)
            
            # Log trade
            log_trade('bot4', f'{side}_order', f'{symbol}: {amount} @ {price or "market"}')
            
            return order
            
        except Exception as e:
            log_trade('bot4', 'error', f'Trade execution failed: {str(e)}')
            return None
    
    def run(self):
        """Main bot loop"""
        log_trade('bot4', 'start', 'Bot 4 ML Range Scalper started')
        
        while self.running:
            try:
                # Check if it's time to retrain model
                if time.time() - self.last_retrain > float(self.params.get('retrain_interval', 604800)):
                    self.model = self._train_model()
                    self.last_retrain = time.time()
                
                # Check each trading pair
                for symbol in self.pairs:
                    try:
                        # Predict if market is range-bound
                        range_probability = self.predict_range_condition(symbol)
                        
                        # Get sentiment score
                        sentiment = get_combined_sentiment(symbol.split('/')[0], self.master_pass)
                        
                        # Get current price
                        if self.exchange:
                            ticker = self.exchange.fetch_ticker(symbol)
                            current_price = ticker['last']
                        else:
                            current_price = 0
                        
                        # Trading logic
                        if range_probability > 0.7 and sentiment['average'] > 0.2:
                            # High probability of range + positive sentiment = BUY at support
                            rsi_data = get_indicator('rsi', {
                                'exchange': 'coinbase',
                                'symbol': symbol.replace('/', ''),
                                'interval': '15m',
                                'period': 14
                            }, self.master_pass)
                            
                            rsi = rsi_data.get('value', 50) if rsi_data else 50
                            
                            if rsi < 35:  # Oversold in range
                                amount = self.calculate_position_size(symbol, current_price)
                                if amount > 0:
                                    self.execute_trade(symbol, 'buy', amount)
                                    
                        elif range_probability > 0.7 and sentiment['average'] < -0.2:
                            # Range-bound + negative sentiment = SELL at resistance
                            rsi_data = get_indicator('rsi', {
                                'exchange': 'coinbase',
                                'symbol': symbol.replace('/', ''),
                                'interval': '15m',
                                'period': 14
                            }, self.master_pass)
                            
                            rsi = rsi_data.get('value', 50) if rsi_data else 50
                            
                            if rsi > 65:  # Overbought in range
                                amount = self.calculate_position_size(symbol, current_price)
                                if amount > 0:
                                    self.execute_trade(symbol, 'sell', amount)
                    
                    except Exception as e:
                        log_trade('bot4', 'error', f'Error processing {symbol}: {str(e)}')
                        continue
                
                # Sleep for trade frequency
                time.sleep(self.trade_freq)
                
            except Exception as e:
                log_trade('bot4', 'error', f'Bot loop error: {str(e)}')
                time.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        log_trade('bot4', 'stop', 'Bot 4 stopped')
