# 🚨 IMMEDIATE ACTIONS REQUIRED - The GOAT Farm

## CRITICAL (Fix within 24 hours)

### 1. Replace CCXT with Coinbase Advanced Trade SDK
```python
# Current (WRONG):
import ccxt
self.exchange = ccxt.coinbase({...})

# Replace with:
from coinbase import RESTClient
client = RESTClient(api_key=cdp_key, api_secret=private_key)
```

**Files to modify:**
- `/bots/bot1.py` (lines 32-43)
- `/bots/bot2.py` (lines 34-45)
- `/bots/bot3.py` (similar pattern)
- `/bots/bot4.py` (similar pattern)

### 2. Remove Hardcoded Default Password
**File**: `/utils/secure_config.py` (line 48)
```python
# REMOVE THIS:
password = os.environ.get('SYSTEM_SECRET', 'default-goat-farm-2025').encode()

# REPLACE WITH:
password = os.environ.get('SYSTEM_SECRET')
if not password:
    raise ValueError("SYSTEM_SECRET environment variable is required")
password = password.encode()
```

### 3. Add Input Sanitization to Dashboard
**File**: `/dashboard/app.py`
```python
# Import at top:
from utils.security_fixes import sanitize_decorator, setup_security

# Add to create_app() or main:
setup_security(app)

# Add to all routes that accept user input:
@app.route('/update_params', methods=['POST'])
@sanitize_decorator
def update_params():
    # existing code
```

## HIGH PRIORITY (Fix within 48 hours)

### 4. Implement WebSocket for Real-time Data
```python
# In main.py, add:
from utils.websocket_client import start_websocket

# In if __name__ == '__main__':
start_websocket()  # Start before bots
```

### 5. Update Bot Trading Logic
Replace polling prices with WebSocket:
```python
# Instead of:
ticker = self.exchange.fetch_ticker(coin)
current_price = ticker['last']

# Use:
from utils.websocket_client import get_realtime_price
current_price = get_realtime_price(coin)
```

### 6. Add ECDSA Key Support
1. Generate keys:
```bash
node scripts/generate-ecdsa-keys.js
```

2. Add to .env:
```
COINBASE_ECDSA_PRIVATE_KEY=<generated_private_key>
COINBASE_ECDSA_PUBLIC_KEY=<generated_public_key>
```

### 7. Enable Security Headers
In `/dashboard/app.py`, add:
```python
from utils.security_fixes import add_security_headers

@app.after_request
def apply_security(response):
    return add_security_headers(response)
```

## MEDIUM PRIORITY (Fix within 1 week)

### 8. Add Comprehensive Error Handling
- Wrap all API calls in try-except blocks
- Implement exponential backoff for retries
- Add circuit breaker pattern

### 9. Implement Proper Logging
- Replace print() statements with proper logging
- Add log rotation
- Implement centralized error tracking

### 10. Add Monitoring and Alerts
- Health check endpoints
- Performance metrics
- Alert on critical errors

## Testing Checklist

After implementing fixes:

- [ ] Run `python check_phase1.py` - All tests should pass
- [ ] Run `python test_apis.py` - All APIs should connect
- [ ] Start application: `python main.py` - No errors
- [ ] Check dashboard: http://localhost:5000 - Loads correctly
- [ ] Verify WebSocket: Check for real-time price updates
- [ ] Test trading: Place a small test order
- [ ] Security scan: Run OWASP ZAP or similar

## Quick Start Commands

```bash
# 1. Install new dependencies
pip install coinbase-advanced-py websocket-client elliptic

# 2. Generate ECDSA keys
node scripts/generate-ecdsa-keys.js

# 3. Update .env file with keys

# 4. Apply security fixes
python -c "from utils.security_fixes import setup_security; print('Security module loaded')"

# 5. Start with WebSocket
python main.py
```

## Support Resources

- Coinbase CDP Docs: https://docs.cdp.coinbase.com/
- ECDSA Implementation: https://github.com/coinbase/coinbase-advanced-py
- Security Best Practices: https://owasp.org/www-project-top-ten/

---
**Remember**: Never commit API keys or private keys to version control! 