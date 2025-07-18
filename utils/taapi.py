import requests
import time
from typing import Dict, List, Optional, Any
from utils.db import get_key, increment_api_call, log_trade

# TAAPI base URL
BASE_URL = 'https://api.taapi.io'

# Rate limiting
last_request_time = 0
MIN_REQUEST_INTERVAL = 1.0  # 1 second between requests (increased from 0.5)
MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # 5 seconds initial backoff for 429 errors

def _rate_limit():
    """Ensure we don't exceed rate limits"""
    global last_request_time
    current_time = time.time()
    elapsed = current_time - last_request_time
    
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    
    last_request_time = time.time()

def _handle_request_with_retry(url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
    """Handle API request with exponential backoff for rate limits"""
    backoff = INITIAL_BACKOFF
    
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()
            
            if method == 'GET':
                response = requests.get(url, **kwargs)
            else:
                response = requests.post(url, **kwargs)
            
            if response.status_code == 429:
                # Rate limit hit - exponential backoff
                wait_time = backoff * (2 ** attempt)
                print(f"TAAPI rate limit hit. Waiting {wait_time} seconds...")
                log_trade('taapi', 'rate_limit', f'429 error, waiting {wait_time}s')
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 401:
                print("Invalid TAAPI key—check .env")
                log_trade('taapi', 'auth_error', 'Invalid API key')
                return None
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                print(f"TAAPI request failed after {MAX_RETRIES} attempts: {str(e)}")
                log_trade('taapi', 'error', f'Request failed: {str(e)}')
            else:
                time.sleep(backoff * (2 ** attempt))
    
    return None

def get_indicator(indicator: str, params: Dict[str, Any], master_pass: str = '') -> Optional[Dict]:
    """
    Get a single indicator from TAAPI using Direct GET endpoint.
    
    Args:
        indicator: Indicator name (rsi, macd, sma, etc.)
        params: Parameters for the indicator (symbol, interval, etc.)
        master_pass: Master password for decrypting API key
        
    Returns:
        JSON response from TAAPI or None if error
    """
    try:
        # Get API key
        api_key = get_key('taapi_key', master_pass)
        if not api_key:
            print("TAAPI key not found in database - returning default 0.0")
            # Return default values
            if indicator == 'rsi':
                return {'value': 0.0}
            elif indicator == 'macd':
                return {
                    'value': 0.0,
                    'signal': 0.0,
                    'histogram': 0.0
                }
            else:
                return {'value': 0.0}
        
        # Add secret to params
        params['secret'] = api_key
        
        # Make request with retry logic
        url = f"{BASE_URL}/{indicator}"
        response = _handle_request_with_retry(url, params=params, timeout=10)
        
        if response:
            # Increment API call counter on success
            increment_api_call('taapi')
            return response.json()
        else:
            # Return default values on failure
            if indicator == 'rsi':
                return {'value': 0.0}
            elif indicator == 'macd':
                return {'value': 0.0, 'signal': 0.0, 'histogram': 0.0}
            else:
                return {'value': 0.0}
        
    except Exception as e:
        print(f"Error getting TAAPI indicator {indicator}: {str(e)}")
        log_trade('taapi', 'error', f'{indicator} error: {str(e)}')
        return None

def get_bulk(queries: List[Dict[str, Any]], master_pass: str = '') -> Optional[Dict]:
    """
    Get multiple indicators in a single request (more efficient).
    Max 20 indicators per request, max 3 symbols per request.
    
    Args:
        queries: List of query dicts with indicator configs
        master_pass: Master password for decrypting API key
        
    Returns:
        JSON response with results for all queries
    """
    try:
        # Get API key
        api_key = get_key('taapi_key', master_pass)
        if not api_key:
            print("TAAPI key not found in database")
            return None
        
        # Make request with retry logic
        url = f"{BASE_URL}/bulk"
        headers = {'Content-Type': 'application/json'}
        params = {'secret': api_key}
        
        response = _handle_request_with_retry(
            url, 
            method='POST',
            json={'requests': queries}, 
            params=params, 
            headers=headers, 
            timeout=30
        )
        
        if response:
            increment_api_call('taapi')
            return response.json()
        
        return None
        
    except Exception as e:
        print(f"Error getting TAAPI bulk data: {str(e)}")
        log_trade('taapi', 'error', f'Bulk request error: {str(e)}')
        return None

def get_pattern(symbol: str, interval: str, exchange: str = 'coinbase', master_pass: str = '') -> Optional[Dict]:
    """
    Get candlestick pattern recognition for a symbol.
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        interval: Time interval (1h, 4h, 1d, etc.)
        exchange: Exchange name (default: coinbase)
        master_pass: Master password for decrypting API key
        
    Returns:
        Dict with pattern values (e.g., {'valueCDLHAMMER': 100} for bullish hammer)
    """
    params = {
        'exchange': exchange,
        'symbol': symbol,
        'interval': interval
    }
    
    return get_indicator('candle', params, master_pass)

def get_historical(symbol: str, interval: str, backtracks: int = 50, exchange: str = 'coinbase', master_pass: str = '') -> Optional[List]:
    """
    Get historical candles for backtesting.
    Limited to 50 candles to avoid rate limits (was 300).
    
    Args:
        symbol: Trading pair
        interval: Time interval
        backtracks: Number of candles to fetch (max 50 to avoid 429)
        exchange: Exchange name
        master_pass: Master password
        
    Returns:
        List of OHLCV candles
    """
    params = {
        'exchange': exchange,
        'symbol': symbol,
        'interval': interval,
        'backtracks': min(backtracks, 50)  # Reduced from 300 to 50
    }
    
    result = get_indicator('candles', params, master_pass)
    if result and 'value' in result:
        return result['value']
    return None

def build_bulk_query(indicators: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Build bulk queries respecting TAAPI limits:
    - Max 20 indicators per request
    - Max 3 symbols per request
    
    Args:
        indicators: List of indicator configs
        
    Returns:
        List of bulk query batches
    """
    # Group by symbol
    symbol_groups = {}
    for ind in indicators:
        symbol = ind.get('symbol', '')
        if symbol not in symbol_groups:
            symbol_groups[symbol] = []
        symbol_groups[symbol].append(ind)
    
    # Build batches
    batches = []
    current_batch = []
    current_symbols = set()
    
    for symbol, symbol_indicators in symbol_groups.items():
        for ind in symbol_indicators:
            # Check if we need a new batch
            if len(current_batch) >= 20 or (symbol not in current_symbols and len(current_symbols) >= 3):
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                current_symbols = set()
            
            current_batch.append(ind)
            current_symbols.add(symbol)
    
    # Add last batch
    if current_batch:
        batches.append(current_batch)
    
    return batches 