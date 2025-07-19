"""
Base bot class that uses simple environment variable access.
No master password required - just environment variables.
"""
import os
import sys
from abc import ABC, abstractmethod
from threading import Thread

# Add utils to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.simple_env import get_api_key, get_coinbase_keys
from utils.db import log_trade

class BaseBot(Thread, ABC):
    """Base class for all trading bots."""
    
    def __init__(self, bot_name: str):
        super().__init__()
        self.bot_name = bot_name
        self.running = False
        
    def start_bot(self):
        """Start the bot."""
        self.running = True
        self.start()
        
    def stop_bot(self):
        """Stop the bot."""
        self.running = False
        
    @abstractmethod
    def run(self):
        """Main bot loop - must be implemented by subclasses."""
        pass
        
    def log(self, action: str, details: str):
        """Log bot activity."""
        log_trade(self.bot_name, action, details)
        print(f"[{self.bot_name}] {action}: {details}")
        
    def get_coinbase_client(self):
        """Get Coinbase client based on available keys."""
        keys = get_coinbase_keys()
        if not keys:
            raise ValueError("No Coinbase API keys found in environment")
            
        if keys['type'] == 'cdp':
            # Use CDP SDK
            from coinbase.rest import RESTClient
            return RESTClient(
                api_key=keys['key_name'],
                api_secret=keys['private_key']
            )
        else:
            # Use legacy SDK
            from coinbase.rest import RESTClient
            return RESTClient(
                api_key=keys['api_key'],
                api_secret=keys['api_secret']
            )
            
    def get_api_key(self, key_name: str) -> str:
        """Get API key from environment."""
        return get_api_key(key_name) 