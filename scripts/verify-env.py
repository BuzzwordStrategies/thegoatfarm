#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

print("Verifying .env file...")
print("=" * 40)

# Load .env file
load_dotenv()

# Check all required keys
required_keys = {
    'COINBASE_KEY_NAME': 'Coinbase Key Name',
    'COINBASE_PRIVATE_KEY': 'Coinbase Private Key',
    'TAAPI_API_KEY': 'TAAPI Key',
    'ANTHROPIC_API_KEY': 'Anthropic/Claude Key',
    'GROK_API_KEY': 'Grok Key',
    'PERPLEXITY_API_KEY': 'Perplexity Key',
    'TWITTERAPIIO_API_KEY': 'TwitterAPI.io Key',
    'COINDESK_API_KEY': 'CoinDesk Key',
    'SCRAPINGBEE_API_KEY': 'ScrapingBee Key'
}

found = 0
missing = []

for key, name in required_keys.items():
    value = os.getenv(key)
    if value and not value.startswith('your_'):
        print(f"[OK] {name}: Found")
        found += 1
    else:
        print(f"[X] {name}: Missing or invalid")
        missing.append(key)

print("=" * 40)
print(f"Found: {found}/{len(required_keys)} keys")

if missing:
    print("\nMissing keys:")
    for key in missing:
        print(f"  - {key}")

# Also check for MASTER_PASSWORD
master_pass = os.getenv('MASTER_PASSWORD')
if master_pass:
    print("\n[OK] MASTER_PASSWORD is set")
else:
    print("\n[!] MASTER_PASSWORD not found - using default")
