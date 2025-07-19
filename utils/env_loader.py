import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import json

class EnvLoader:
    """Secure environment variable loader with encryption support"""
    
    def __init__(self):
        self.env_path = Path(__file__).parent.parent / '.env'
        self.encrypted_keys_path = Path(__file__).parent.parent / '.encrypted_keys.json'
        load_dotenv(self.env_path)
        
        # Initialize encryption
        self.encryption_key = os.getenv('DB_ENCRYPTION_KEY')
        if self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode())
        else:
            print("WARNING: DB_ENCRYPTION_KEY not set. API keys will not be encrypted.")
            self.cipher = None
    
    def get(self, key, default=None):
        """Get environment variable"""
        return os.getenv(key, default)
    
    def get_encrypted(self, key):
        """Get and decrypt an API key"""
        encrypted_value = os.getenv(key)
        if encrypted_value and self.cipher and encrypted_value.startswith('enc:'):
            try:
                return self.cipher.decrypt(encrypted_value[4:].encode()).decode()
            except:
                return encrypted_value
        return encrypted_value
    
    def set_encrypted(self, key, value):
        """Encrypt and save an API key"""
        if self.cipher:
            encrypted = 'enc:' + self.cipher.encrypt(value.encode()).decode()
            os.environ[key] = encrypted
            # Also save to file for persistence
            self._save_encrypted_key(key, encrypted)
        else:
            os.environ[key] = value
    
    def _save_encrypted_key(self, key, encrypted_value):
        """Save encrypted key to file"""
        if self.encrypted_keys_path.exists():
            with open(self.encrypted_keys_path, 'r') as f:
                keys = json.load(f)
        else:
            keys = {}
        
        keys[key] = encrypted_value
        
        with open(self.encrypted_keys_path, 'w') as f:
            json.dump(keys, f, indent=2)
    
    def validate_required_keys(self):
        """Validate all required API keys are present"""
        required_keys = [
            'COINBASE_API_KEY',
            'COINBASE_API_SECRET',
            'TAAPI_SECRET',
            'TWITTERAPI_KEY',
            'SCRAPINGBEE_API_KEY',
            'XAI_API_KEY',
            'PERPLEXITY_API_KEY',
            'ANTHROPIC_API_KEY',
            'DB_ENCRYPTION_KEY'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"WARNING: Missing required environment variables: {', '.join(missing_keys)}")
            print("Please copy .env.template to .env and fill in all values")
            return False
        
        return True

# Global instance
env_loader = EnvLoader() 

# Backward compatibility functions
def get_env_key(key_type: str) -> str:
    """Get API key from environment variables (backward compatibility)"""
    env_mappings = {
        'coinbase_api_key': 'COINBASE_API_KEY',
        'coinbase_secret': 'COINBASE_API_SECRET',
        'COINBASE_CDP_API_KEY_NAME': 'COINBASE_API_KEY_NAME',
        'COINBASE_CDP_API_KEY_SECRET': 'COINBASE_API_KEY_PRIVATE_KEY',
        'COINBASE_API_KEY': 'COINBASE_API_KEY',
        'COINBASE_API_SECRET': 'COINBASE_API_SECRET',
        'taapi_key': 'TAAPI_SECRET',
        'TAAPI_SECRET': 'TAAPI_SECRET',
        'grok_api_key': 'XAI_API_KEY',
        'XAI_API_KEY': 'XAI_API_KEY',
        'perplexity_api_key': 'PERPLEXITY_API_KEY',
        'PERPLEXITY_API_KEY': 'PERPLEXITY_API_KEY',
        'claude_api_key': 'ANTHROPIC_API_KEY',
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        'coindesk_api_key': 'COINDESK_API_URL',
        'twitterapi_key': 'TWITTERAPI_KEY',
        'TWITTERAPI_KEY': 'TWITTERAPI_KEY',
        'TWITTER_API_KEY': 'TWITTER_API_KEY',
        'scrapingbee_api_key': 'SCRAPINGBEE_API_KEY',
        'SCRAPINGBEE_API_KEY': 'SCRAPINGBEE_API_KEY',
    }
    
    env_var = env_mappings.get(key_type)
    if env_var:
        return env_loader.get_encrypted(env_var) or ''
    return ''

def get_master_password() -> str:
    """Get master password from environment"""
    password = env_loader.get('MASTER_PASSWORD')
    if not password:
        raise ValueError("MASTER_PASSWORD environment variable is required but not set")
    return password

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
