# Crypto API Integration Audit and Dashboard System

## Overview

This comprehensive system provides real-time monitoring, security, and management for cryptocurrency API integrations. It includes:

- 🔍 **API Key Auditor**: Validates and tests all API connections
- 🔐 **Secure Key Manager**: Encrypts and manages API keys securely
- 🏥 **Health Monitor**: Real-time monitoring of API health and performance
- 📊 **Integration Dashboard**: Unified view of all API statuses

## Prerequisites

- Node.js >= 18.0.0
- Python 3.x (for integration with existing Python codebase)
- npm or yarn

## Installation

1. Install Node.js dependencies:
```bash
npm install
```

2. Export Python environment variables (if using existing Python setup):
```bash
npm run export-env
```

## Usage

### Quick Start - Run Complete Dashboard

```bash
npm run dashboard
```

This will:
1. Audit all configured API keys
2. Initialize secure key storage
3. Start real-time health monitoring
4. Generate comprehensive reports

### Individual Components

#### API Key Audit Only
```bash
npm run audit
```

#### Export Python Environment
```bash
npm run export-env
```

## API Configuration

The system supports the following APIs:

| API | Required Keys | Purpose |
|-----|--------------|---------|
| Coinbase | API_KEY, API_SECRET, PASSPHRASE | Crypto trading |
| CoinDesk | API_KEY | Price data |
| TAAPI.io | API_KEY | Technical indicators |
| Perplexity | API_KEY | AI analysis |
| Grok | API_KEY | AI insights |
| Claude (Anthropic) | API_KEY | AI assistance |
| ScrapingBee | API_KEY | Web scraping |
| Twitter | API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET | Social sentiment |

## Environment Variables

Create a `.env` file in the `src` directory:

```env
# API Keys
COINBASE_API_KEY=your_key_here
COINBASE_API_SECRET=your_secret_here
COINBASE_API_PASSPHRASE=your_passphrase_here
TAAPI_API_KEY=your_key_here
GROK_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
COINDESK_API_KEY=your_key_here
SCRAPINGBEE_API_KEY=your_key_here

# Twitter API
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_ACCESS_TOKEN=your_token_here
TWITTER_ACCESS_SECRET=your_secret_here

# Security
MASTER_ENCRYPTION_KEY=your_master_key_here
```

## Features

### 1. API Key Auditor

- Validates API key formats
- Tests live connections
- Generates comprehensive audit reports
- Identifies missing or invalid keys

### 2. Secure Key Manager

- AES-256 encryption for all keys
- Key rotation support
- Usage tracking and analytics
- Secure storage with `.secure-keys` file

### 3. Health Monitor

- Real-time API health checks
- Response time monitoring
- Error rate tracking
- Alert thresholds:
  - Error rate > 10%
  - Response time > 5 seconds
  - 3 consecutive failures = critical

### 4. Integration Dashboard

- Unified monitoring interface
- Real-time status updates
- Automated recommendations
- JSON report generation

## Output Files

| File | Description |
|------|-------------|
| `audit-results.json` | Complete API audit results |
| `dashboard-report.json` | Dashboard execution summary |
| `final-health-report.json` | Health monitoring results |
| `.secure-keys` | Encrypted key storage (do not commit!) |

## Security Best Practices

1. **Never commit API keys** - Add `.env` and `.secure-keys` to `.gitignore`
2. **Use strong master encryption key** - Change default in production
3. **Rotate keys regularly** - Use the key rotation feature
4. **Monitor access logs** - Check usage statistics regularly
5. **Enable 2FA** - On all API provider accounts

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Run `npm run export-env` to export from Python environment
   - Check `.env` file exists and contains keys

2. **"Connection failed"**
   - Verify API endpoints are accessible
   - Check firewall/proxy settings
   - Validate API key formats

3. **"Module not found"**
   - Run `npm install` to install dependencies
   - Ensure Node.js >= 18.0.0

## Integration with Python Codebase

The system integrates seamlessly with the existing Python crypto trading platform:

1. Export keys from Python:
```bash
python src/export_env_for_audit.py
```

2. Run the dashboard:
```bash
npm run dashboard
```

3. View results in generated JSON reports

## Contributing

To add support for a new API:

1. Add configuration in `api-key-audit.js`:
```javascript
newapi: {
  name: 'New API',
  requiredKeys: ['NEW_API_KEY'],
  endpoints: {
    test: 'https://api.newapi.com/test'
  },
  headers: (keys) => ({
    'Authorization': `Bearer ${keys.NEW_API_KEY}`
  })
}
```

2. Add to key mappings in `export_env_for_audit.py`
3. Update documentation

## License

This system is part of The GOAT Farm crypto trading platform. 