#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('í´§ GOAT FARM COMPLETE FIX SCRIPT');
console.log('================================\n');

// Fix 1: Reinstall axios-retry correctly
console.log('í³¦ Fixing Node.js dependencies...');
try {
  execSync('npm uninstall axios-retry', { stdio: 'inherit' });
  execSync('npm install axios-retry@3.8.0', { stdio: 'inherit' });
  console.log('âœ… Fixed axios-retry\n');
} catch (e) {
  console.log('âš ï¸  Could not fix axios-retry automatically\n');
}

// Fix 2: Update Python bot key names
console.log('í´§ Fixing Python bot API key names...');

// Read main.py and update the key names
const mainPyPath = path.join(process.cwd(), 'main.py');
let mainPyContent = fs.readFileSync(mainPyPath, 'utf8');

// Update the key checking section
mainPyContent = mainPyContent.replace(
  /required_keys = \[.*?\]/s,
  `required_keys = [
        'COINBASE_KEY_NAME',      # Updated for new API
        'COINBASE_PRIVATE_KEY',   # Updated for new API
        'TAAPI_API_KEY',
        'ANTHROPIC_API_KEY'
    ]`
);

fs.writeFileSync(mainPyPath, mainPyContent);
console.log('âœ… Updated main.py key names\n');

// Fix 3: Update utils/env_loader.py to map old names to new ones
console.log('í´§ Creating key mapping for backward compatibility...');

const keyMappingCode = `
# Add key mapping at the top of get_env_key function
def get_env_key(key_type):
    """Get API key from environment variables with backward compatibility."""
    
    # Map old key names to new ones
    key_mapping = {
        'coinbase_api_key': 'COINBASE_KEY_NAME',
        'coinbase_secret': 'COINBASE_PRIVATE_KEY',
        'taapi_key': 'TAAPI_API_KEY',
        'claude_api_key': 'ANTHROPIC_API_KEY',
        'twitter_bearer': 'TWITTERAPIIO_API_KEY',
        'grok_api_key': 'GROK_API_KEY',
        'perplexity_api_key': 'PERPLEXITY_API_KEY',
        'news_api_key': 'COINDESK_API_KEY'
    }
    
    # Try the mapped name first
    env_key = key_mapping.get(key_type, key_type.upper())
    
    # Try to get from environment
    value = os.getenv(env_key)
    if value and value != 'your_' + env_key.lower():
        return value
    
    # Try the original key type as uppercase
    value = os.getenv(key_type.upper())
    if value and value != 'your_' + key_type:
        return value
        
    # Try exact match
    value = os.getenv(key_type)
    if value and value != 'your_' + key_type:
        return value
    
    return None
`;

const envLoaderPath = path.join(process.cwd(), 'utils', 'env_loader.py');
let envLoaderContent = fs.readFileSync(envLoaderPath, 'utf8');

// Replace the get_env_key function
envLoaderContent = envLoaderContent.replace(
  /def get_env_key\(key_type\):.*?return None/s,
  keyMappingCode.trim()
);

fs.writeFileSync(envLoaderPath, envLoaderContent);
console.log('âœ… Updated env_loader.py with key mapping\n');

// Fix 4: Create launch script with proper PYTHONPATH
console.log('í´§ Creating improved launch script...');

const improvedBatchScript = `@echo off
title GOAT Farm Trading Platform

echo ========================================
echo    GOAT FARM TRADING PLATFORM v1.0
echo ========================================
echo.

:: Set Python path to include project root
set PYTHONPATH=%CD%;%PYTHONPATH%

:: Check for .env file
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env from env.example
    pause
    exit /b 1
)

:: Load environment variables from .env
echo Loading environment variables...
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%b"=="" (
        set "%%a=%%b"
    )
)

:: Try to start Redis (optional)
echo Checking for Redis...
where redis-server >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Starting Redis...
    start /B redis-server 2>nul
    timeout /t 2 >nul
) else (
    echo Redis not found - continuing without it
)

:: Start Python trading bots
echo.
echo Starting Trading Bots...
start /B python main.py

:: Wait a moment
timeout /t 3 >nul

:: Start Flask dashboard with proper path
echo Starting Flask Dashboard...
cd dashboard
start /B python app.py
cd ..

:: Wait a moment
timeout /t 3 >nul

:: Start Node.js dashboard
echo Starting Node.js Dashboard...
start /B node src\\server\\index.js

:: Wait for everything to start
timeout /t 5 >nul

echo.
echo ========================================
echo    GOAT FARM IS NOW RUNNING!
echo ========================================
echo.
echo Dashboards:
echo  - Flask: http://localhost:5000
echo  - Node.js: http://localhost:3001
echo.
echo Trading Bots:
echo  - Bot 1: Trend-Following (BTC/ETH)
echo  - Bot 2: Mean-Reversion (SOL/ADA)
echo  - Bot 3: News-Driven (Multi-pair)
echo  - Bot 4: ML-Powered (Top 10)
echo.
echo Press Ctrl+C to stop all services
echo.

:: Keep window open
pause >nul
`;

fs.writeFileSync('launch-goat-farm-fixed.bat', improvedBatchScript);
console.log('âœ… Created launch-goat-farm-fixed.bat\n');

// Fix 5: Update bot files to use new Coinbase client
console.log('í´§ Updating bot files for new Coinbase API...');

const botFiles = ['bot1.py', 'bot2.py', 'bot3.py', 'bot4.py'];
botFiles.forEach(botFile => {
  const botPath = path.join(process.cwd(), 'bots', botFile);
  if (fs.existsSync(botPath)) {
    let content = fs.readFileSync(botPath, 'utf8');
    
    // Update the exchange initialization
    content = content.replace(
      /self\.exchange = ccxt\.coinbase\(\{[\s\S]*?\}\)/m,
      `self.exchange = ccxt.coinbase({
            'apiKey': get_key('COINBASE_KEY_NAME', master_pass) or get_key('coinbase_api_key', master_pass),
            'secret': get_key('COINBASE_PRIVATE_KEY', master_pass) or get_key('coinbase_secret', master_pass),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'version': 'v3'  # Use new Advanced Trade API
            }
        })`
    );
    
    fs.writeFileSync(botPath, content);
    console.log(`âœ… Updated ${botFile}`);
  }
});

console.log('\nâœ… ALL FIXES APPLIED!\n');
console.log('Next steps:');
console.log('1. Run: launch-goat-farm-fixed.bat');
console.log('2. The system should now start correctly');
console.log('3. Your API keys will be recognized');
console.log('\nNote: Redis is optional. The system will work without it.');
