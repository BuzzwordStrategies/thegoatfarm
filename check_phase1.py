#!/usr/bin/env python3
"""
Quick validation script for Phase 1 setup
Checks that all components are properly configured
"""

import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init()

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if exists else f"{Fore.RED}✗{Style.RESET_ALL}"
    print(f"{status} {description:<40} {filepath}")
    return exists

def check_env_var(var_name: str) -> bool:
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    exists = bool(value)
    status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if exists else f"{Fore.YELLOW}○{Style.RESET_ALL}"
    masked_value = f"{value[:20]}..." if value and len(value) > 20 else value
    print(f"{status} {var_name:<35} {'Set' if exists else 'Not set'}")
    return exists

def main():
    print(f"\n{Fore.CYAN}{'='*60}")
    print("PHASE 1 VALIDATION - The GOAT Farm")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Check files
    print(f"{Fore.CYAN}Checking Required Files:{Style.RESET_ALL}")
    files_ok = all([
        check_file_exists("requirements.txt", "Dependencies"),
        check_file_exists("utils/secure_config.py", "Secure Config Module"),
        check_file_exists("utils/rate_limiter.py", "Rate Limiter Module"),
        check_file_exists("test_apis.py", "API Test Suite"),
        check_file_exists(".env.template", "Environment Template"),
        check_file_exists(".env", "Environment File"),
        check_file_exists(".gitignore", "Git Ignore File"),
    ])
    
    # Check environment variables
    print(f"\n{Fore.CYAN}Checking API Keys in .env:{Style.RESET_ALL}")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    api_vars = {
        "Coinbase CDP": ["COINBASE_CDP_API_KEY_NAME", "COINBASE_CDP_API_KEY_SECRET", 
                         "COINBASE_ORGANIZATION_ID", "COINBASE_API_KEY_ID"],
        "TAAPI": ["TAAPI_API_KEY"],
        "TwitterAPI": ["TWITTERAPI_API_KEY"],
        "ScrapingBee": ["SCRAPINGBEE_API_KEY"],
        "Grok": ["GROK_API_KEY"],
        "Perplexity": ["PERPLEXITY_API_KEY"],
        "Anthropic": ["ANTHROPIC_API_KEY"],
        "System": ["SYSTEM_SECRET", "FLASK_SECRET_KEY"],
    }
    
    api_status = {}
    for api_name, vars in api_vars.items():
        print(f"\n{api_name}:")
        all_set = all(check_env_var(var) for var in vars)
        api_status[api_name] = all_set
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    if files_ok:
        print(f"{Fore.GREEN}✓ All required files are present{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Some files are missing{Style.RESET_ALL}")
    
    configured_apis = sum(1 for configured in api_status.values() if configured)
    total_apis = len(api_status)
    
    print(f"\nAPIs Configured: {configured_apis}/{total_apis}")
    for api_name, configured in api_status.items():
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if configured else f"{Fore.YELLOW}○{Style.RESET_ALL}"
        print(f"  {status} {api_name}")
    
    print(f"\n{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
    if configured_apis < total_apis:
        print("1. Add missing API keys to .env file")
        print("2. Run: python test_apis.py")
    else:
        print("1. Run: pip install -r requirements.txt")
        print("2. Run: python test_apis.py")
        print("3. If all tests pass, proceed to Phase 2")
    
    print(f"\n{Fore.CYAN}Phase 1 Status: {'READY' if files_ok and configured_apis > 0 else 'INCOMPLETE'}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main() 