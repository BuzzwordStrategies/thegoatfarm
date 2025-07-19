"""
Simple environment variable access for API keys.
No encryption, no master password - just direct environment variable access.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_api_key(key_name: str) -> str:
    """Get API key from environment variable."""
    # Direct mappings to environment variables
    env_mappings = {
        # Coinbase
        'COINBASE_CDP_API_KEY_NAME': 'COINBASE_API_KEY_NAME',
        'COINBASE_CDP_API_KEY_SECRET': 'COINBASE_API_KEY_PRIVATE_KEY',
        'COINBASE_API_KEY': 'COINBASE_API_KEY',
        'COINBASE_API_SECRET': 'COINBASE_API_SECRET',
        
        # Twitter
        'TWITTER_API_KEY': 'TWITTER_API_KEY',
        'TWITTERAPI_KEY': 'TWITTERAPI_KEY',
        
        # TAAPI
        'TAAPI_SECRET': 'TAAPI_SECRET',
        
        # ScrapingBee
        'SCRAPINGBEE_API_KEY': 'SCRAPINGBEE_API_KEY',
        
        # AI APIs
        'XAI_API_KEY': 'XAI_API_KEY',
        'PERPLEXITY_API_KEY': 'PERPLEXITY_API_KEY',
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        
        # Other
        'COINDESK_API_URL': 'COINDESK_API_URL',
        'DB_ENCRYPTION_KEY': 'DB_ENCRYPTION_KEY',
    }
    
    # Try direct key name first
    value = os.getenv(key_name)
    if value:
        return value
    
    # Try mapped name
    mapped_name = env_mappings.get(key_name)
    if mapped_name:
        value = os.getenv(mapped_name)
        if value:
            return value
    
    # Return empty string if not found
    return ''

def get_coinbase_keys():
    """Get Coinbase API keys (CDP or legacy format)."""
    # Try CDP format first
    key_name = get_api_key('COINBASE_API_KEY_NAME')
    private_key = get_api_key('COINBASE_API_KEY_PRIVATE_KEY')
    
    if key_name and private_key:
        return {'type': 'cdp', 'key_name': key_name, 'private_key': private_key}
    
    # Fall back to legacy format
    api_key = get_api_key('COINBASE_API_KEY')
    api_secret = get_api_key('COINBASE_API_SECRET')
    
    if api_key and api_secret:
        return {'type': 'legacy', 'api_key': api_key, 'api_secret': api_secret}
    
    return None

def check_required_keys():
    """Check if all required API keys are present."""
    required = [
        ('Coinbase', ['COINBASE_API_KEY', 'COINBASE_API_KEY_NAME']),
        ('Twitter', ['TWITTER_API_KEY', 'TWITTERAPI_KEY']),
        ('TAAPI', ['TAAPI_SECRET']),
        ('ScrapingBee', ['SCRAPINGBEE_API_KEY']),
        ('XAI/Grok', ['XAI_API_KEY']),
        ('Perplexity', ['PERPLEXITY_API_KEY']),
        ('Anthropic', ['ANTHROPIC_API_KEY']),
    ]
    
    missing = []
    for service, keys in required:
        found = False
        for key in keys:
            if get_api_key(key):
                found = True
                break
        if not found:
            missing.append(f"{service} ({' or '.join(keys)})")
    
    return missing 