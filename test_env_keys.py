#!/usr/bin/env python3
"""
Test script to verify .env file is properly configured and working
"""

import os
from dotenv import load_dotenv
from utils.db import init_db, get_key
from utils.env_loader import get_env_key, get_master_password, load_all_env_keys

# Load environment variables
load_dotenv()

def test_env_configuration():
    """Test if environment variables are properly configured"""
    print("=== Testing Environment Configuration ===\n")
    
    # Get master password
    master_pass = get_master_password()
    print(f"✓ Master Password: {'Set from environment' if os.getenv('MASTER_PASSWORD') else 'Using default (March3392!)'}")
    
    # Initialize database
    init_db()
    print("✓ Database initialized\n")
    
    # List of all required API keys
    required_keys = [
        ('coinbase_api_key', 'Coinbase API Key'),
        ('coinbase_secret', 'Coinbase Secret'),
        ('taapi_key', 'TAAPI.io Key'),
        ('grok_api_key', 'Grok API Key'),
        ('perplexity_api_key', 'Perplexity API Key'),
        ('claude_api_key', 'Claude API Key'),
        ('coindesk_api_key', 'CoinDesk API Key (Optional)'),
    ]
    
    print("Checking API Keys:")
    print("-" * 50)
    
    all_keys_found = True
    keys_found = 0
    
    for key_type, display_name in required_keys:
        # Check environment variable
        env_value = get_env_key(key_type)
        
        # Check using get_key (which checks DB first, then env)
        final_value = get_key(key_type, master_pass)
        
        if final_value:
            source = "Environment" if env_value else "Database"
            # Show only first/last 4 chars for security
            if len(final_value) > 8:
                masked = f"{final_value[:4]}...{final_value[-4:]}"
            else:
                masked = "****"
            print(f"✓ {display_name:<25} Found ({source}) - {masked}")
            keys_found += 1
        else:
            print(f"✗ {display_name:<25} NOT FOUND")
            if 'Optional' not in display_name:
                all_keys_found = False
    
    print("-" * 50)
    print(f"\nTotal keys found: {keys_found}/{len(required_keys)}")
    
    # Test bot initialization
    print("\nTesting Bot Initialization:")
    print("-" * 50)
    
    try:
        from bots.bot1 import Bot1
        bot = Bot1(master_pass)
        print("✓ Bot1 initialized successfully")
        
        # Check if exchange is configured
        if bot.exchange.apiKey:
            print("✓ Coinbase exchange configured")
        else:
            print("✗ Coinbase exchange not configured")
            
    except Exception as e:
        print(f"✗ Bot1 initialization failed: {str(e)}")
    
    # Summary
    print("\n" + "="*50)
    if all_keys_found:
        print("✅ All required API keys are configured!")
        print("✅ Your .env file is working correctly!")
        print("\nYou can now run the main application with:")
        print("  python main.py")
    else:
        print("⚠️  Some required API keys are missing.")
        print("\nPlease check your .env file and ensure all keys are added.")
        print("Format example:")
        print("  COINBASE_API_KEY=your-actual-key-here")
        print("  COINBASE_SECRET=your-actual-secret-here")

if __name__ == "__main__":
    test_env_configuration() 