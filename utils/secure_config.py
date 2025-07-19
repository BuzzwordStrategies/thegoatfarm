"""
Secure configuration management with encryption for API keys
Meta: Type-safe configuration pattern
Coinbase: Secure key storage with encryption
Apple: Clean separation of concerns
"""
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """Structured API configuration"""
    name: str
    key: Optional[str] = None
    secret: Optional[str] = None
    passphrase: Optional[str] = None
    org_id: Optional[str] = None
    key_id: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 10
    timeout: int = 30

class SecureConfigManager:
    """Manages encrypted API configurations"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
        self.configs = self._load_configs()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create encryption master key"""
        key_file = '.encryption_key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key from machine ID
        password = os.environ.get('SYSTEM_SECRET', 'default-goat-farm-2025').encode()
        salt = b'goat-farm-salt-2025'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        with open(key_file, 'wb') as f:
            f.write(key)
        
        return key
    
    def _load_configs(self) -> Dict[str, APIConfig]:
        """Load API configurations from environment"""
        configs = {}
        
        # Coinbase Advanced Trade API
        if os.getenv('COINBASE_CDP_API_KEY_NAME'):
            configs['coinbase'] = APIConfig(
                name='coinbase',
                key=os.getenv('COINBASE_CDP_API_KEY_NAME'),
                secret=self._encrypt(os.getenv('COINBASE_CDP_API_KEY_SECRET', '')),
                org_id=os.getenv('COINBASE_ORGANIZATION_ID'),
                key_id=os.getenv('COINBASE_API_KEY_ID'),
                base_url='https://api.coinbase.com/api/v3',
                rate_limit=30,
                timeout=10
            )
        
        # TAAPI.io
        if os.getenv('TAAPI_API_KEY'):
            configs['taapi'] = APIConfig(
                name='taapi',
                key=self._encrypt(os.getenv('TAAPI_API_KEY', '')),
                base_url='https://api.taapi.io',
                rate_limit=15,
                timeout=30
            )
        
        # TwitterAPI.io
        if os.getenv('TWITTERAPI_API_KEY'):
            configs['twitter'] = APIConfig(
                name='twitter',
                key=self._encrypt(os.getenv('TWITTERAPI_API_KEY', '')),
                base_url='https://api.twitterapi.io/v1',
                rate_limit=100,
                timeout=10
            )
        
        # ScrapingBee
        if os.getenv('SCRAPINGBEE_API_KEY'):
            configs['scrapingbee'] = APIConfig(
                name='scrapingbee',
                key=self._encrypt(os.getenv('SCRAPINGBEE_API_KEY', '')),
                base_url='https://app.scrapingbee.com/api/v1',
                rate_limit=10,
                timeout=60
            )
        
        # Grok API
        if os.getenv('GROK_API_KEY'):
            configs['grok'] = APIConfig(
                name='grok',
                key=self._encrypt(os.getenv('GROK_API_KEY', '')),
                base_url='https://api.x.ai/v1',
                rate_limit=20,
                timeout=30
            )
        
        # Perplexity AI
        if os.getenv('PERPLEXITY_API_KEY'):
            configs['perplexity'] = APIConfig(
                name='perplexity',
                key=self._encrypt(os.getenv('PERPLEXITY_API_KEY', '')),
                base_url='https://api.perplexity.ai',
                rate_limit=20,
                timeout=60
            )
        
        # Anthropic Claude
        if os.getenv('ANTHROPIC_API_KEY'):
            configs['anthropic'] = APIConfig(
                name='anthropic',
                key=self._encrypt(os.getenv('ANTHROPIC_API_KEY', '')),
                base_url='https://api.anthropic.com/v1',
                rate_limit=50,
                timeout=60
            )
        
        # CoinDesk (no auth required)
        configs['coindesk'] = APIConfig(
            name='coindesk',
            base_url='https://api.coindesk.com/v1/bpi',
            rate_limit=100,
            timeout=10
        )
        
        return configs
    
    def _encrypt(self, value: str) -> str:
        """Encrypt sensitive value"""
        if not value:
            return ''
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, value: str) -> str:
        """Decrypt sensitive value"""
        if not value:
            return ''
        return self.cipher.decrypt(value.encode()).decode()
    
    def get_config(self, api_name: str) -> Optional[APIConfig]:
        """Get decrypted API configuration"""
        config = self.configs.get(api_name)
        if not config:
            return None
        
        # Create copy with decrypted values
        decrypted_config = APIConfig(
            name=config.name,
            key=config.key,  # CDP key name is not encrypted
            secret=self._decrypt(config.secret) if config.secret else None,
            passphrase=config.passphrase,
            org_id=config.org_id,
            key_id=config.key_id,
            base_url=config.base_url,
            rate_limit=config.rate_limit,
            timeout=config.timeout
        )
        
        # Decrypt other keys
        if api_name != 'coinbase' and config.key:
            decrypted_config.key = self._decrypt(config.key)
        
        return decrypted_config
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """Validate all API configurations"""
        results = {}
        for name, config in self.configs.items():
            if name == 'coindesk':
                results[name] = True  # No auth required
            elif name == 'coinbase':
                results[name] = bool(config.key and config.secret and config.org_id)
            else:
                results[name] = bool(config.key)
        return results

# Global instance
config_manager = SecureConfigManager() 