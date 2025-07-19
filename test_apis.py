"""
API Connection Test Suite
Tests all 8 APIs to ensure proper authentication and connectivity
"""
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import requests
from colorama import Fore, Style, init
from coinbase import RESTClient
from coinbase.rest import accounts
import anthropic

# Initialize colorama for Windows
init()

# Import our secure config
sys.path.append('.')
from utils.secure_config import config_manager

class APITester:
    """Test all API connections"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def print_header(self):
        """Print test header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"THE GOAT FARM - API CONNECTION TEST SUITE")
        print(f"Testing 8 API Integrations")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def print_result(self, api_name: str, success: bool, message: str, details: str = ""):
        """Print formatted test result"""
        status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if success else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
        print(f"{status} {api_name:15} | {message}")
        if details and not success:
            print(f"  {Fore.YELLOW}→ {details}{Style.RESET_ALL}")
    
    def test_coinbase(self) -> Tuple[bool, str, str]:
        """Test Coinbase Advanced Trade API"""
        try:
            config = config_manager.get_config('coinbase')
            if not config:
                return False, "No configuration found", "Add Coinbase CDP keys to .env"
            
            # Initialize Coinbase client
            client = RESTClient(
                api_key=config.key,
                api_secret=config.secret,
                verbose=False
            )
            
            # Test account access
            accounts_response = client.get_accounts()
            if hasattr(accounts_response, 'accounts'):
                account_count = len(accounts_response.accounts)
                return True, f"Connected - Found {account_count} accounts", ""
            else:
                return False, "Could not retrieve accounts", str(accounts_response)
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_taapi(self) -> Tuple[bool, str, str]:
        """Test TAAPI.io Technical Analysis API"""
        try:
            config = config_manager.get_config('taapi')
            if not config:
                return False, "No configuration found", "Add TAAPI key to .env"
            
            # Test RSI endpoint
            response = requests.get(
                f"{config.base_url}/rsi",
                params={
                    "secret": config.key,
                    "exchange": "binance",
                    "symbol": "BTC/USDT",
                    "interval": "1h"
                },
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'value' in data:
                    return True, f"Connected - RSI: {data['value']:.2f}", ""
                else:
                    return False, "Invalid response format", json.dumps(data)
            else:
                return False, f"HTTP {response.status_code}", response.text
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_twitter(self) -> Tuple[bool, str, str]:
        """Test TwitterAPI.io"""
        try:
            config = config_manager.get_config('twitter')
            if not config:
                return False, "No configuration found", "Add TwitterAPI key to .env"
            
            # Test trending endpoint
            response = requests.get(
                f"{config.base_url}/trends/place.json",
                headers={"Authorization": f"Bearer {config.key}"},
                params={"id": "1"},  # Worldwide trends
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                return True, "Connected - Trends API working", ""
            elif response.status_code == 401:
                return False, "Authentication failed", "Check API key"
            else:
                return False, f"HTTP {response.status_code}", response.text[:100]
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_scrapingbee(self) -> Tuple[bool, str, str]:
        """Test ScrapingBee API"""
        try:
            config = config_manager.get_config('scrapingbee')
            if not config:
                return False, "No configuration found", "Add ScrapingBee key to .env"
            
            # Test account endpoint
            response = requests.get(
                f"{config.base_url}/",
                params={
                    "api_key": config.key,
                    "url": "https://httpbin.org/user-agent"
                },
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                return True, "Connected - Web scraping working", ""
            elif response.status_code == 401:
                return False, "Authentication failed", "Check API key"
            else:
                return False, f"HTTP {response.status_code}", response.text[:100]
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_grok(self) -> Tuple[bool, str, str]:
        """Test Grok API"""
        try:
            config = config_manager.get_config('grok')
            if not config:
                return False, "No configuration found", "Add Grok API key to .env"
            
            # Test models endpoint
            response = requests.get(
                f"{config.base_url}/models",
                headers={"Authorization": f"Bearer {config.key}"},
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                models = response.json().get('data', [])
                return True, f"Connected - {len(models)} models available", ""
            elif response.status_code == 401:
                return False, "Authentication failed", "Check API key"
            else:
                return False, f"HTTP {response.status_code}", response.text[:100]
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_perplexity(self) -> Tuple[bool, str, str]:
        """Test Perplexity AI API"""
        try:
            config = config_manager.get_config('perplexity')
            if not config:
                return False, "No configuration found", "Add Perplexity key to .env"
            
            # Test models endpoint
            response = requests.get(
                f"{config.base_url}/models",
                headers={"Authorization": f"Bearer {config.key}"},
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                return True, "Connected - Models endpoint working", ""
            elif response.status_code == 401:
                return False, "Authentication failed", "Check API key format (pplx-...)"
            else:
                return False, f"HTTP {response.status_code}", response.text[:100]
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_anthropic(self) -> Tuple[bool, str, str]:
        """Test Anthropic Claude API"""
        try:
            config = config_manager.get_config('anthropic')
            if not config:
                return False, "No configuration found", "Add Anthropic key to .env"
            
            # Initialize client
            client = anthropic.Anthropic(api_key=config.key)
            
            # Test with simple completion
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'API connected'"}]
            )
            
            if response.content:
                return True, "Connected - Claude responding", ""
            else:
                return False, "No response received", ""
                
        except anthropic.AuthenticationError:
            return False, "Authentication failed", "Check API key format (sk-ant-...)"
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def test_coindesk(self) -> Tuple[bool, str, str]:
        """Test CoinDesk API (no auth required)"""
        try:
            config = config_manager.get_config('coindesk')
            
            # Test current price endpoint
            response = requests.get(
                f"{config.base_url}/currentprice.json",
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                btc_price = data.get('bpi', {}).get('USD', {}).get('rate', 'Unknown')
                return True, f"Connected - BTC: ${btc_price}", ""
            else:
                return False, f"HTTP {response.status_code}", response.text[:100]
                
        except Exception as e:
            return False, "Connection failed", str(e)
    
    def run_all_tests(self):
        """Run all API tests"""
        self.print_header()
        
        # Define test functions
        tests = [
            ("Coinbase", self.test_coinbase),
            ("TAAPI", self.test_taapi),
            ("TwitterAPI", self.test_twitter),
            ("ScrapingBee", self.test_scrapingbee),
            ("Grok", self.test_grok),
            ("Perplexity", self.test_perplexity),
            ("Anthropic", self.test_anthropic),
            ("CoinDesk", self.test_coindesk)
        ]
        
        # Run tests
        passed = 0
        failed = 0
        
        for api_name, test_func in tests:
            success, message, details = test_func()
            self.results[api_name] = success
            self.print_result(api_name, success, message, details)
            
            if success:
                passed += 1
            else:
                failed += 1
        
        # Print summary
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"TEST SUMMARY")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Passed: {Fore.GREEN}{passed}{Style.RESET_ALL} | Failed: {Fore.RED}{failed}{Style.RESET_ALL}")
        
        if failed == 0:
            print(f"\n{Fore.GREEN}✓ ALL APIS CONNECTED SUCCESSFULLY!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠ Some APIs need configuration. Check .env file.{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        return passed, failed

if __name__ == "__main__":
    tester = APITester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1) 