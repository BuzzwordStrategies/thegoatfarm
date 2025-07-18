import sqlite3
import os
from datetime import datetime
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.db')

def init_db():
    """Initialize the database and create tables if they don't exist."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create api_keys table for storing encrypted API keys
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            key_type TEXT UNIQUE,
            encrypted_value BLOB
        )
    ''')
    
    # Create trade_logs table for recording all trading activities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_logs (
            id INTEGER PRIMARY KEY,
            bot_id TEXT,
            timestamp DATETIME,
            action TEXT,
            details TEXT
        )
    ''')
    
    # Create bot_params table for storing bot configuration parameters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_params (
            id INTEGER PRIMARY KEY,
            bot_id TEXT,
            param_name TEXT,
            value TEXT
        )
    ''')
    
    # Create api_calls table for tracking daily API usage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_calls (
            api_type TEXT,
            date DATE,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (api_type, date)
        )
    ''')
    
    conn.commit()
    conn.close()

def _derive_key(master_pass: str) -> bytes:
    """Derive an encryption key from master password."""
    # Use a fixed salt for simplicity (in production, store this securely)
    salt = b'crypto_trading_salt_v1'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_pass.encode()))
    return key

def encrypt_key(key: str, master_pass: str) -> bytes:
    """Encrypt an API key using the master password."""
    fernet_key = _derive_key(master_pass)
    f = Fernet(fernet_key)
    encrypted = f.encrypt(key.encode())
    return encrypted

def decrypt_key(key_type: str, master_pass: str) -> Optional[str]:
    """Decrypt an API key from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT encrypted_value FROM api_keys WHERE key_type = ?', (key_type,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    fernet_key = _derive_key(master_pass)
    f = Fernet(fernet_key)
    decrypted = f.decrypt(result[0])
    return decrypted.decode()

def store_key(key_type: str, value: str, master_pass: str):
    """Store an encrypted API key in the database."""
    encrypted = encrypt_key(value, master_pass)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO api_keys (key_type, encrypted_value)
        VALUES (?, ?)
    ''', (key_type, encrypted))
    
    conn.commit()
    conn.close()

def get_key(key_type: str, master_pass: str) -> Optional[str]:
    """Retrieve and decrypt an API key from the database."""
    # First try to get from database
    db_key = decrypt_key(key_type, master_pass)
    if db_key:
        return db_key
    
    # If not in database, try environment variables
    from .env_loader import get_env_key
    env_key = get_env_key(key_type)
    if env_key:
        return env_key
    
    return None

def log_trade(bot_id: str, action: str, details: str):
    """Log a trading action to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO trade_logs (bot_id, timestamp, action, details)
        VALUES (?, ?, ?, ?)
    ''', (bot_id, datetime.utcnow(), action, details))
    
    conn.commit()
    conn.close()

def get_params(bot_id: str) -> dict:
    """Get all parameters for a specific bot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT param_name, value FROM bot_params WHERE bot_id = ?', (bot_id,))
    results = cursor.fetchall()
    conn.close()
    
    return {param: value for param, value in results}

def set_param(bot_id: str, param_name: str, value: str):
    """Set a parameter value for a specific bot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO bot_params (bot_id, param_name, value)
        VALUES (?, ?, ?)
    ''', (bot_id, param_name, value))
    
    conn.commit()
    conn.close()

def increment_api_call(api_type: str):
    """Increment the daily API call counter for a specific API type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO api_calls (api_type, date, count)
        VALUES (?, date('now'), 
                COALESCE((SELECT count FROM api_calls 
                         WHERE api_type = ? AND date = date('now')), 0) + 1)
    ''', (api_type, api_type))
    
    conn.commit()
    conn.close()

def get_api_call_count(api_type: str) -> int:
    """Get today's API call count for a specific API type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT count FROM api_calls 
        WHERE api_type = ? AND date = date('now')
    ''', (api_type,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0

# Example usage:
# master_pass = 'user-provided'
# store_key('coinbase_api', 'actual_key', master_pass)
# api_key = get_key('coinbase_api', master_pass)
# log_trade('bot1', 'BUY', 'Bought 0.1 BTC at $45000')
# set_param('bot1', 'risk_level', '0.05')
# params = get_params('bot1')
# increment_api_call('coinbase')
# count = get_api_call_count('coinbase') 