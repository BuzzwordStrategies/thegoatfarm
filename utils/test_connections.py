#!/usr/bin/env python3
"""Test all API connections to ensure they're working"""

import sys
import asyncio
from datetime import datetime
from colorama import init, Fore, Style
import requests
import json

# Initialize colorama for Windows compatibility
init()

# Import our env loader
from env_loader import env_loader

class APIConnectionTester:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
    
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text:^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    def print_result(self, api_name, success, message):
        if success:
            print(f"{Fore.GREEN}✓ {api_name:20} {message}{Style.RESET_ALL}")
            self.passed += 1
        else:
            print(f"{Fore.RED}✗ {api_name:20} {message}{Style.RESET_ALL}")
            self.failed += 1
        
        self.results[api_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_coinbase(self):
        """Test Coinbase Advanced Trade API"""
        try:
            from coinbase.rest import RESTClient
            
            api_key = env_loader.get_encrypted('COINBASE_API_KEY')
            api_secret = env_loader.get_encrypted('COINBASE_API_SECRET')
            
            if not api_key or not api_secret:
                raise Exception("Missing Coinbase credentials")
            
            client = RESTClient(api_key=api_key, api_secret=api_secret)
            
            # Test by getting accounts
            accounts = client.get_accounts()
            
            if accounts and hasattr(accounts, 'accounts'):
                account_count = len(accounts.accounts) if accounts.accounts else 0
                self.print_result("Coinbase API", True, f"Connected! Found {account_count} accounts")
            else:
                raise Exception("Invalid response from Coinbase")
                
        except Exception as e:
            self.print_result("Coinbase API", False, f"Error: {str(e)}")
    
    def test_taapi(self):
        """Test TAAPI.io connection"""
        try:
            secret = env_loader.get_encrypted('TAAPI_SECRET')
            if not secret:
                raise Exception("Missing TAAPI secret")
            
            # Test with RSI endpoint
            url = "https://api.taapi.io/rsi"
            params = {
                'secret': secret,
                'exchange': 'binance',
                'symbol': 'BTC/USDT',
                'interval': '1h'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and 'value' in data:
                self.print_result("TAAPI.io", True, f"Connected! RSI: {data['value']:.2f}")
            else:
                raise Exception(data.get('error', 'Unknown error'))
                
        except Exception as e:
            self.print_result("TAAPI.io", False, f"Error: {str(e)}")
    
    def test_twitterapi(self):
        """Test TwitterAPI.io connection"""
        try:
            api_key = env_loader.get_encrypted('TWITTERAPI_KEY')
            if not api_key:
                raise Exception("Missing TwitterAPI key")
            
            # Test endpoint (adjust based on actual API)
            headers = {'Authorization': f'Bearer {api_key}'}
            url = "https://twitterapi.io/api/v1/account/verify"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.print_result("TwitterAPI.io", True, "Connected successfully!")
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            self.print_result("TwitterAPI.io", False, f"Error: {str(e)}")
    
    def test_scrapingbee(self):
        """Test ScrapingBee connection"""
        try:
            from scrapingbee import ScrapingBeeClient
            
            api_key = env_loader.get_encrypted('SCRAPINGBEE_API_KEY')
            if not api_key:
                raise Exception("Missing ScrapingBee key")
            
            client = ScrapingBeeClient(api_key=api_key)
            
            # Test with a simple request
            response = client.get('https://httpbin.org/anything')
            
            if response.status_code == 200:
                self.print_result("ScrapingBee", True, "Connected successfully!")
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            self.print_result("ScrapingBee", False, f"Error: {str(e)}")
    
    def test_grok(self):
        """Test Grok (xAI) API connection"""
        try:
            from openai import OpenAI
            
            api_key = env_loader.get_encrypted('XAI_API_KEY')
            if not api_key:
                raise Exception("Missing xAI API key")
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": "Say 'API Connected'"}],
                max_tokens=10
            )
            
            if response and response.choices:
                self.print_result("Grok API", True, "Connected successfully!")
            else:
                raise Exception("Invalid response")
                
        except Exception as e:
            self.print_result("Grok API", False, f"Error: {str(e)}")
    
    def test_perplexity(self):
        """Test Perplexity AI connection"""
        try:
            from openai import OpenAI
            
            api_key = env_loader.get_encrypted('PERPLEXITY_API_KEY')
            if not api_key:
                raise Exception("Missing Perplexity API key")
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai"
            )
            
            # Test with a simple query
            response = client.chat.completions.create(
                model="sonar-small-online",
                messages=[{"role": "user", "content": "What is 2+2?"}],
                max_tokens=10
            )
            
            if response and response.choices:
                self.print_result("Perplexity AI", True, "Connected successfully!")
            else:
                raise Exception("Invalid response")
                
        except Exception as e:
            self.print_result("Perplexity AI", False, f"Error: {str(e)}")
    
    def test_anthropic(self):
        """Test Anthropic Claude API connection"""
        try:
            import anthropic
            
            api_key = env_loader.get_encrypted('ANTHROPIC_API_KEY')
            if not api_key:
                raise Exception("Missing Anthropic API key")
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # Test with a simple message
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Connected'"}]
            )
            
            if response and response.content:
                self.print_result("Anthropic Claude", True, "Connected successfully!")
            else:
                raise Exception("Invalid response")
                
        except Exception as e:
            self.print_result("Anthropic Claude", False, f"Error: {str(e)}")
    
    def test_coindesk(self):
        """Test CoinDesk API (free, no auth)"""
        try:
            url = env_loader.get('COINDESK_API_URL', 'https://api.coindesk.com/v1/bpi/currentprice.json')
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and 'bpi' in data and 'USD' in data['bpi']:
                price = data['bpi']['USD']['rate']
                self.print_result("CoinDesk API", True, f"Connected! BTC: ${price}")
            else:
                raise Exception("Invalid response format")
                
        except Exception as e:
            self.print_result("CoinDesk API", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all API connection tests"""
        self.print_header("TESTING API CONNECTIONS")
        
        # Validate environment first
        if not env_loader.validate_required_keys():
            print(f"{Fore.YELLOW}Some API keys are missing. Tests will fail for those APIs.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please ensure all keys are configured in .env file{Style.RESET_ALL}\n")
        
        # Run tests
        self.test_coinbase()
        self.test_taapi()
        self.test_twitterapi()
        self.test_scrapingbee()
        self.test_grok()
        self.test_perplexity()
        self.test_anthropic()
        self.test_coindesk()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        print(f"Total APIs tested: {self.passed + self.failed}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        
        # Save results
        results_file = 'api_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
        return self.failed == 0

if __name__ == "__main__":
    tester = APIConnectionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1) 