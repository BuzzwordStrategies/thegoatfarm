"""
WebSocket client for real-time Coinbase data feeds
Implements reconnection logic and error handling
"""
import websocket
import json
import threading
import time
from typing import List, Callable, Optional, Dict, Any
from utils.db import log_trade
from utils.rate_limiter import rate_limiter

class CoinbaseWebSocket:
    """Real-time WebSocket connection to Coinbase"""
    
    def __init__(self, products: List[str] = None, channels: List[str] = None):
        self.url = "wss://ws-feed.exchange.coinbase.com"
        self.products = products or ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD']
        self.channels = channels or ['ticker', 'level2', 'matches']
        self.ws = None
        self.running = False
        self.callbacks = {}
        self.reconnect_count = 0
        self.max_reconnect_attempts = 10
        self.reconnect_interval = 5
        
        # Price cache for latest prices
        self.price_cache = {}
        
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            # Handle different message types
            if msg_type == 'ticker':
                self._handle_ticker(data)
            elif msg_type == 'l2update':
                self._handle_level2(data)
            elif msg_type == 'match':
                self._handle_match(data)
            elif msg_type == 'error':
                log_trade('websocket', 'error', f"Coinbase WS error: {data.get('message')}")
                
            # Call registered callbacks
            if msg_type in self.callbacks:
                for callback in self.callbacks[msg_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        log_trade('websocket', 'error', f"Callback error: {str(e)}")
                        
        except json.JSONDecodeError as e:
            log_trade('websocket', 'error', f"JSON decode error: {str(e)}")
        except Exception as e:
            log_trade('websocket', 'error', f"Message handling error: {str(e)}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        log_trade('websocket', 'error', f"WebSocket error: {str(error)}")
        
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        log_trade('websocket', 'info', f"WebSocket closed: {close_status_code} - {close_msg}")
        self.running = False
        
        # Attempt reconnection if not manually closed
        if self.reconnect_count < self.max_reconnect_attempts:
            self.reconnect_count += 1
            log_trade('websocket', 'info', f"Reconnecting... attempt {self.reconnect_count}")
            time.sleep(self.reconnect_interval * self.reconnect_count)
            self.connect()
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        log_trade('websocket', 'info', "WebSocket connected")
        self.reconnect_count = 0
        
        # Subscribe to channels
        subscribe_message = {
            "type": "subscribe",
            "product_ids": self.products,
            "channels": self.channels
        }
        
        ws.send(json.dumps(subscribe_message))
        log_trade('websocket', 'info', f"Subscribed to {self.products} channels: {self.channels}")
    
    def _handle_ticker(self, data: Dict[str, Any]):
        """Handle ticker updates"""
        product_id = data.get('product_id')
        price = float(data.get('price', 0))
        
        if product_id and price > 0:
            self.price_cache[product_id] = {
                'price': price,
                'time': data.get('time'),
                'best_bid': float(data.get('best_bid', 0)),
                'best_ask': float(data.get('best_ask', 0)),
                'volume_24h': float(data.get('volume_24h', 0))
            }
    
    def _handle_level2(self, data: Dict[str, Any]):
        """Handle level 2 order book updates"""
        # Process order book updates for advanced strategies
        pass
    
    def _handle_match(self, data: Dict[str, Any]):
        """Handle trade matches"""
        # Process executed trades for market analysis
        pass
    
    def register_callback(self, msg_type: str, callback: Callable):
        """Register a callback for specific message types"""
        if msg_type not in self.callbacks:
            self.callbacks[msg_type] = []
        self.callbacks[msg_type].append(callback)
    
    def get_price(self, product_id: str) -> Optional[float]:
        """Get latest cached price for a product"""
        if product_id in self.price_cache:
            return self.price_cache[product_id]['price']
        return None
    
    def get_ticker(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get full ticker data for a product"""
        return self.price_cache.get(product_id)
    
    def connect(self):
        """Connect to WebSocket"""
        self.running = True
        
        websocket.enableTrace(False)  # Disable debug output
        
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Run in separate thread
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
        log_trade('websocket', 'info', "WebSocket thread started")
    
    def disconnect(self):
        """Disconnect WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
            log_trade('websocket', 'info', "WebSocket disconnected")
    
    def add_products(self, products: List[str]):
        """Add products to subscription"""
        if self.ws and self.running:
            subscribe_message = {
                "type": "subscribe",
                "product_ids": products,
                "channels": self.channels
            }
            self.ws.send(json.dumps(subscribe_message))
            self.products.extend(products)

# Global WebSocket instance
coinbase_ws = CoinbaseWebSocket()

def start_websocket():
    """Start the global WebSocket connection"""
    coinbase_ws.connect()

def stop_websocket():
    """Stop the global WebSocket connection"""
    coinbase_ws.disconnect()

def get_realtime_price(symbol: str) -> Optional[float]:
    """Get real-time price from WebSocket"""
    # Convert symbol format (BTC/USD -> BTC-USD)
    product_id = symbol.replace('/', '-')
    return coinbase_ws.get_price(product_id) 