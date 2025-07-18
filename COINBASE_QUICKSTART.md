# 🚀 Coinbase Migration Quick Start

## You're 3 Steps Away from Using the New Coinbase API!

### Step 1: Get Your Keys (2 minutes)
1. Go to https://portal.cdp.coinbase.com/
2. Sign in and navigate to **API Keys**
3. Create a new key or use existing
4. Copy:
   - **Key Name** (looks like: `8f68***6d3c`)
   - **Private Key** (download the file)

### Step 2: Configure Keys (1 minute)

#### Option A: Use Setup Script (Recommended)
```bash
node scripts/setup-coinbase-keys.js
```

#### Option B: Manual Setup
Add to your `.env` file:
```
COINBASE_KEY_NAME=8f68***6d3c
COINBASE_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIJX+87jFJRMqFJBVwAe5Intel3I7o1tGijVBa0qIeTKXqoAoGCCqGSM49
AwEHoUQDQgAEG3J5/fkpxT6N/DUVlFG1XpE/2kBkQcjBGNAGLBqfpuJQhXhJ4kUG
ImrTQ6yoL3/Yt7JLp3R2eVJvHxFYxiLacA==
-----END EC PRIVATE KEY-----
```

### Step 3: Test Connection (30 seconds)
```bash
node src/utils/security/api-key-audit.js
```

You should see:
```
🔍 Auditing Coinbase Advanced Trade API...
✅ Status: Active
```

## 🎉 That's It! You're Done!

Your trading bots will continue working with the new API. The migration maintains backward compatibility for all common operations.

## Need Help?
- Full guide: `docs/COINBASE_MIGRATION_GUIDE.md`
- Summary: `COINBASE_MIGRATION_SUMMARY.md`
- Troubleshooting: Check if your key has proper permissions at https://portal.cdp.coinbase.com/ 