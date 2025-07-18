import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_key(key_type: str) -> str:
    """Get API key from environment variables"""
    # Mapping of database key names to environment variable names
    env_mappings = {
        'coinbase_api_key': 'COINBASE_API_KEY',
        'coinbase_secret': 'COINBASE_SECRET',
        'taapi_key': 'TAAPI_KEY',
        'grok_api_key': 'GROK_API_KEY',
        'perplexity_api_key': 'PERPLEXITY_API_KEY',
        'claude_api_key': 'CLAUDE_API_KEY',
        'coindesk_api_key': 'COINDESK_API_KEY',
    }
    
    env_var = env_mappings.get(key_type)
    if env_var:
        return os.getenv(env_var, '')
    return ''

def get_master_password() -> str:
    """Get master password from environment or use default"""
    return os.getenv('MASTER_PASSWORD', 'March3392!')

def load_all_env_keys() -> dict:
    """Load all API keys from environment variables"""
    keys = {}
    key_types = [
        'coinbase_api_key',
        'coinbase_secret',
        'taapi_key',
        'grok_api_key',
        'perplexity_api_key',
        'claude_api_key',
        'coindesk_api_key',
    ]
    
    for key_type in key_types:
        value = get_env_key(key_type)
        if value:
            keys[key_type] = value
    
    return keys

def has_env_keys() -> bool:
    """Check if any API keys are configured in environment"""
    return bool(load_all_env_keys()) 