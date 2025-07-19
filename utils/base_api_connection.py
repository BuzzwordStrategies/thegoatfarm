"""
Base API Connection Pattern
All API connections MUST use this pattern for consistency
"""
import os
import logging
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAPIConnection:
    """
    Base class for ALL API connections.
    Ensures consistent pattern across the entire codebase.
    """
    
    def __init__(self, api_name: str):
        """Initialize API connection with environment variables only"""
        self.api_name = api_name.upper()
        
        # Load API credentials from environment
        self.api_key = os.getenv(f'{self.api_name}_API_KEY')
        self.api_secret = os.getenv(f'{self.api_name}_API_SECRET')
        self.base_url = os.getenv(f'{self.api_name}_BASE_URL')
        
        # Session for connection pooling
        self.session = requests.Session()
        
        # Test connection on initialization
        self.is_connected = self.test_connection()
        
    def test_connection(self) -> bool:
        """
        Test API connection. Must be implemented by subclasses.
        MUST return True/False and log specific error.
        """
        raise NotImplementedError("Subclasses must implement test_connection()")
        
    def _log_error(self, error_msg: str, exception: Optional[Exception] = None):
        """Standardized error logging"""
        full_msg = f"{self.api_name} connection failed: {error_msg}"
        if exception:
            full_msg += f" - Exception: {str(exception)}"
        logger.error(full_msg)
        
    def _log_success(self, success_msg: str):
        """Standardized success logging"""
        logger.info(f"{self.api_name} connection successful: {success_msg}")
        
    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests"""
        return {
            'User-Agent': 'GOAT-Farm-Trading-Bot/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make standardized API request with error handling"""
        if not self.is_connected:
            self._log_error("Cannot make request - connection not established")
            return None
            
        try:
            url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}
        except Exception as e:
            self._log_error(f"Request failed for {endpoint}", e)
            return None


class CoinbaseConnection(BaseAPIConnection):
    """Coinbase-specific API connection"""
    
    def __init__(self):
        # Check for CDP keys first
        self.cdp_key_name = os.getenv('COINBASE_API_KEY_NAME')
        self.cdp_private_key = os.getenv('COINBASE_API_KEY_PRIVATE_KEY')
        
        if self.cdp_key_name and self.cdp_private_key:
            self.auth_type = 'CDP'
        else:
            self.auth_type = 'Legacy'
            
        super().__init__('COINBASE')
        
    def test_connection(self) -> bool:
        """Test Coinbase connection"""
        try:
            if self.auth_type == 'CDP':
                # CDP uses JWT authentication
                if self.cdp_key_name:
                    self._log_success(f"CDP keys found: {self.cdp_key_name[:20]}...")
                    return True
                else:
                    self._log_error("CDP key name not found")
                    return False
            else:
                # Legacy authentication
                if self.api_key and self.api_secret:
                    from coinbase.rest import RESTClient
                    self.client = RESTClient(api_key=self.api_key, api_secret=self.api_secret)
                    self._log_success("Legacy authentication successful")
                    return True
                else:
                    self._log_error("No API keys found")
                    return False
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False


class TaapiConnection(BaseAPIConnection):
    """TAAPI-specific API connection"""
    
    def __init__(self):
        # TAAPI uses TAAPI_SECRET env var
        self.api_key = os.getenv('TAAPI_SECRET')
        self.base_url = 'https://api.taapi.io'
        super().__init__('TAAPI')
        
    def test_connection(self) -> bool:
        """Test TAAPI connection"""
        try:
            if not self.api_key:
                self._log_error("No API key found")
                return False
                
            # Test with RSI endpoint
            params = {
                'secret': self.api_key,
                'exchange': 'binance',
                'symbol': 'BTC/USDT',
                'interval': '1h'
            }
            
            response = self.session.get(f"{self.base_url}/rsi", params=params)
            if response.status_code == 200:
                data = response.json()
                self._log_success(f"Connected - RSI: {data.get('value', 'N/A')}")
                return True
            else:
                self._log_error(f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False
            
    def get_indicator(self, indicator: str, exchange: str, symbol: str, interval: str, **params) -> Optional[Dict]:
        """Get technical indicator from TAAPI"""
        if not self.is_connected:
            return None
            
        endpoint = f"/{indicator}"
        params.update({
            'secret': self.api_key,
            'exchange': exchange,
            'symbol': symbol,
            'interval': interval
        })
        
        return self.make_request('GET', endpoint, params=params)


class TwitterConnection(BaseAPIConnection):
    """Twitter API connection"""
    
    def __init__(self):
        # Try multiple env var names
        self.api_key = os.getenv('TWITTER_API_KEY') or os.getenv('TWITTERAPI_KEY')
        self.base_url = os.getenv('TWITTER_API_BASE_URL', 'https://api.twitterapi.io/v1')
        super().__init__('TWITTER')
        
    def test_connection(self) -> bool:
        """Test Twitter connection"""
        try:
            if not self.api_key:
                self._log_error("No API key found")
                return False
                
            self._log_success(f"API key found: {self.api_key[:10]}...")
            return True
        except Exception as e:
            self._log_error("Connection test failed", e)
            return False
            
    def get_headers(self) -> Dict[str, str]:
        """Override headers for Twitter API"""
        headers = super().get_headers()
        if self.api_key:
            headers['x-api-key'] = self.api_key
        return headers


# Factory function to get API connection
def get_api_connection(api_name: str) -> BaseAPIConnection:
    """Factory function to get the appropriate API connection"""
    connections = {
        'COINBASE': CoinbaseConnection,
        'TAAPI': TaapiConnection,
        'TWITTER': TwitterConnection,
    }
    
    api_class = connections.get(api_name.upper())
    if api_class:
        return api_class()
    else:
        # Generic connection for other APIs
        return BaseAPIConnection(api_name) 