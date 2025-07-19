#!/usr/bin/env python3
"""Initial setup script for The GOAT Farm"""

import os
import sys
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet

def main():
    print("\n🐐 THE GOAT FARM - Initial Setup 🐐\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Install requirements
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check for .env file
    if not Path('.env').exists():
        print("\n⚠️  No .env file found!")
        
        # Copy template
        if Path('.env.template').exists():
            print("📋 Copying .env.template to .env...")
            import shutil
            shutil.copy('.env.template', '.env')
            
            # Generate encryption key
            print("🔐 Generating encryption key...")
            key = Fernet.generate_key().decode()
            
            # Update .env with key
            with open('.env', 'r') as f:
                content = f.read()
            
            content = content.replace('your_generated_encryption_key_here', key)
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ Created .env file with encryption key")
            print("\n⚠️  IMPORTANT: Edit .env and add your API keys!")
        else:
            print("❌ No .env.template found!")
            sys.exit(1)
    
    # Create necessary directories
    dirs = ['logs', 'data', 'backups']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    
    print("\n✅ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python utils/test_connections.py")
    print("3. If all tests pass, proceed to Phase 2")

if __name__ == "__main__":
    main() 