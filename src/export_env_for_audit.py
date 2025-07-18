#!/usr/bin/env python3
"""
Export environment variables from Python setup to .env file for Node.js audit system
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from utils.env_loader import get_env_key, get_master_password
from utils.db import init_db, get_key

# Load Python environment
load_dotenv()

def export_env_for_audit():
    """Export all API keys to .env format for Node.js audit"""
    
    # Get master password
    master_pass = get_master_password()
    
    # Initialize database
    init_db()
    
    # Mapping of Python key names to Node.js expected env var names
    key_mappings = [
        ('coinbase_api_key', 'COINBASE_API_KEY'),
        ('coinbase_secret', 'COINBASE_API_SECRET'),
        ('taapi_key', 'TAAPI_API_KEY'),
        ('grok_api_key', 'GROK_API_KEY'),
        ('perplexity_api_key', 'PERPLEXITY_API_KEY'),
        ('claude_api_key', 'ANTHROPIC_API_KEY'),
        ('coindesk_api_key', 'COINDESK_API_KEY'),
    ]
    
    env_lines = []
    
    # Export existing environment variables
    env_lines.append("# Exported from Python environment")
    env_lines.append(f"NODE_ENV=development")
    env_lines.append(f"MASTER_ENCRYPTION_KEY={master_pass}")
    env_lines.append("")
    
    # Export API keys
    for py_key, node_key in key_mappings:
        # Try to get from environment first, then database
        value = get_env_key(py_key)
        if not value:
            value = get_key(py_key, master_pass)
        
        if value:
            env_lines.append(f"{node_key}={value}")
            print(f"✓ Exported {node_key}")
        else:
            env_lines.append(f"# {node_key}=<not_found>")
            print(f"✗ {node_key} not found")
    
    # Add placeholder for Coinbase passphrase if not present
    if not any('COINBASE_API_PASSPHRASE' in line for line in env_lines):
        env_lines.append("COINBASE_API_PASSPHRASE=your_passphrase_here")
    
    # Write to .env file in src directory
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_file_path, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"\n✅ Environment exported to {env_file_path}")
    print("You can now run: npm run audit")

if __name__ == "__main__":
    export_env_for_audit() 