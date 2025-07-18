# Coinbase API Migration Guide

## Overview
This system has been updated to use the new Coinbase Advanced Trade API instead of the deprecated Coinbase Pro API.

## Key Changes

### 1. Authentication
- **Old**: HMAC-based auth with API Key, Secret, and Passphrase
- **New**: JWT-based auth with Key Name and Private Key (ECDSA)

### 2. Required Environment Variables

**Remove these old variables:**
```
COINBASE_API_KEY
COINBASE_API_SECRET
COINBASE_API_PASSPHRASE
```

**Add these new variables:**
```
COINBASE_KEY_NAME=your_key_name_from_developer_platform
COINBASE_PRIVATE_KEY=your_private_key_in_pem_format
```

### 3. Getting Your Keys

1. Go to [Coinbase Developer Platform](https://portal.cdp.coinbase.com/)
2. Navigate to API Keys section
3. Create a new API key or use existing
4. Copy the **Key Name** (e.g., `8f68***6d3c`)
5. Download or copy the **Private Key**

### 4. Private Key Format

The private key can be in one of these formats:

**PEM Format (Recommended):**
```
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIJX+87jFJRMqFJBVwAe5Intel3I7o1tGijVBa0qIeTKXqoAoGCCqGSM49
AwEHoUQDQgAEG3J5/fkpxT6N/DUVlFG1XpE/2kBkQcjBGNAGLBqfpuJQhXhJ4kUG
ImrTQ6yoL3/Yt7JLp3R2eVJvHxFYxiLacA==
-----END EC PRIVATE KEY-----
```

**Raw Base64 (will be auto-converted):**
```
MHcCAQEEIJX+87jFJRMqFJBVwAe5Intel3I7o1tGijVBa0qIeTKXqoAoGCCqGSM49AwEHoUQDQgAEG3J5/fkpxT6N/DUVlFG1XpE/2kBkQcjBGNAGLBqfpuJQhXhJ4kUGImrTQ6yoL3/Yt7JLp3R2eVJvHxFYxiLacA==
```

### 5. API Endpoints

All endpoints have changed:
- **Old Base URL**: `https://api.pro.coinbase.com`
- **New Base URL**: `https://api.coinbase.com`

### 6. Order Management

Order structure has changed significantly:

**Old Order Format:**
```javascript
{
  side: 'buy',
  product_id: 'BTC-USD',
  type: 'limit',
  price: '50000',
  size: '0.01'
}
```

**New Order Format:**
```javascript
{
  product_id: 'BTC-USD',
  side: 'BUY',
  order_configuration: {
    limit_limit_gtc: {
      base_size: '0.01',
      limit_price: '50000',
      post_only: false
    }
  }
}
```

### 7. WebSocket Changes

- **Old URL**: `wss://ws-feed.pro.coinbase.com`
- **New URL**: `wss://advanced-trade-ws.coinbase.com`
- Authentication now uses JWT instead of API key

## Testing Your Migration

1. Update your `.env` file with new credentials
2. Run the API audit tool:
   ```bash
   node src/utils/security/api-key-audit.js
   ```
3. Test basic connectivity:
   ```bash
   npm test -- coinbase
   ```

## Troubleshooting

### Common Issues

1. **"Invalid JWT" Error**
   - Ensure your private key is properly formatted
   - Check that the key name matches exactly
   - Verify the key has proper permissions

2. **"Unauthorized" Error**
   - Make sure the API key is enabled in Coinbase Developer Platform
   - Check that the key has the required permissions (view, trade, etc.)

3. **"Invalid Signature" Error**
   - Your private key format might be incorrect
   - Try wrapping raw keys with PEM headers

## Support

For more information, see:
- [Coinbase Advanced Trade API Docs](https://docs.cloud.coinbase.com/advanced-trade-api/docs/welcome)
- [Authentication Guide](https://docs.cloud.coinbase.com/advanced-trade-api/docs/auth) 