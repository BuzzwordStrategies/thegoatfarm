#!/usr/bin/env python3
"""
Simple API test script - no master password required.
Tests all API connections using environment variables directly.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.simple_env import get_api_key, get_coinbase_keys, check_required_keys

def test_apis():
    """Test all API connections."""
    print("🧪 Testing API Connections...\n")
    
    # Check for missing keys first
    missing = check_required_keys()
    if missing:
        print("⚠️  Missing API keys:")
        for key in missing:
            print(f"  ❌ {key}")
        print("\n📝 Please add these keys to your .env file")
        return False
    
    print("✅ All required API keys found!\n")
    
    # Test Coinbase
    print("Testing Coinbase...")
    keys = get_coinbase_keys()
    if keys:
        if keys['type'] == 'cdp':
            print(f"  ✅ CDP keys found: {keys['key_name'][:20]}...")
        else:
            print(f"  ✅ Legacy keys found: {keys['api_key'][:20]}...")
    else:
        print("  ❌ No Coinbase keys found")
    
    # Test other APIs
    apis = {
        'Twitter': 'TWITTER_API_KEY',
        'TAAPI': 'TAAPI_SECRET',
        'ScrapingBee': 'SCRAPINGBEE_API_KEY',
        'XAI/Grok': 'XAI_API_KEY',
        'Perplexity': 'PERPLEXITY_API_KEY',
        'Anthropic': 'ANTHROPIC_API_KEY'
    }
    
    print("\nTesting other APIs...")
    for name, key in apis.items():
        value = get_api_key(key)
        if value:
            print(f"  ✅ {name}: {value[:20]}...")
        else:
            print(f"  ❌ {name}: Not found")
    
    print("\n✨ API test complete!")
    return True

if __name__ == "__main__":
    # Test the APIs
    success = test_apis()
    
    if success:
        print("\n🎉 All APIs are ready to use!")
        print("You can now run your bots without a master password.")
    else:
        print("\n⚠️  Some APIs are missing. Please check your .env file.")
        
    # Show example usage
    print("\n📖 Example usage in your code:")
    print("```python")
    print("from utils.simple_env import get_api_key, get_coinbase_keys")
    print("")
    print("# Get any API key")
    print("twitter_key = get_api_key('TWITTER_API_KEY')")
    print("")
    print("# Get Coinbase keys (handles both CDP and legacy)")
    print("coinbase = get_coinbase_keys()")
    print("```") 