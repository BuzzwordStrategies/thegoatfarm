# The GOAT Farm - Crypto Trading Platform

A sophisticated cryptocurrency trading platform featuring 4 parallel trading bots, comprehensive API integration layer, and real-time monitoring dashboard.

## 🚀 New Features (v2.0)

### Phase 1: API Integration Audit System ✅
- Comprehensive API key validation and testing
- Secure key storage with AES-256 encryption
- Real-time health monitoring with alerts
- Detailed audit reports

### Phase 2: Robust API Integration Layer ✅
- 8 API clients with retry logic and circuit breakers
- WebSocket support for real-time data
- Automated news and social media monitoring
- AI-powered trading signals

### Phase 3: Real-time Trading Dashboard ✅
- Modern web interface with WebSocket updates
- Live price charts and market data
- News feed with sentiment analysis
- Social media monitoring (Twitter/Reddit)
- Trading signal visualization

## Features

- **4 Parallel Trading Bots**: Each bot implements different trading strategies
  - Bot1: Momentum trading with BTC/ETH focus
  - Bot2: Scalping strategy for quick trades
  - Bot3: Technical analysis-based trading
  - Bot4: Diversified portfolio approach

- **Dual Dashboard System**: 
  - Python Flask Dashboard: http://localhost:5000 (original)
  - Node.js Real-time Dashboard: http://localhost:3001 (new)
  
- **Enhanced API Integrations**: 
  - Trading: Coinbase (REST + WebSocket)
  - Market Data: CoinDesk
  - Technical Analysis: TAAPI.io (20+ indicators)
  - AI Services: Grok, Perplexity, Claude
  - Web Scraping: ScrapingBee
  - Social Media: TwitterAPI.io
  
- **Enterprise Features**:
  - Circuit breaker pattern for fault tolerance
  - Automatic retry with exponential backoff
  - Real-time health monitoring
  - Secure encrypted key storage
  - Event-driven architecture

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm 7+
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/BuzzwordStrategies/thegoatfarm.git
cd thegoatfarm
```

2. Install Python dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

4. Create a `.env` file in the root directory with your API keys:
```env
# Trading API
COINBASE_API_KEY=your_key_here
COINBASE_SECRET=your_secret_here

# Technical Analysis
TAAPI_KEY=your_key_here

# AI & Sentiment
GROK_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here

# Research & News
PERPLEXITY_API_KEY=your_key_here
COINDESK_API_KEY=your_key_here

# Master Password
MASTER_PASSWORD=your_secure_password
```

### Running the Platform

#### Option 1: Original Python System
```bash
# Verify setup
python test_env_keys.py

# Start trading bots and Flask dashboard
python main.py

# Access at http://localhost:5000
```

#### Option 2: New Real-time Dashboard
```bash
# Export environment variables
npm run export-env

# Start the dashboard server
npm start

# Access at http://localhost:3001
```

#### Option 3: Run Everything
```bash
# Terminal 1: Python bots
python main.py

# Terminal 2: Node.js dashboard
npm start
```

### Quick Commands
```bash
npm run audit          # Run API key audit
npm run test-api       # Test API integrations
npm run test-dashboard # Test dashboard server
npm run export-env     # Export Python env to Node.js
```

## Security Notice

- Never commit your `.env` file or API keys
- The `.gitignore` file is configured to exclude sensitive data
- Database files in `data/` directory are also excluded from version control

## Project Structure

```
The GOAT Farm/
├── bots/                      # Python trading bot implementations
├── dashboard/                 # Original Flask web interface
├── utils/                     # Python utility modules
├── src/                       # Node.js API integration layer
│   ├── api/                   # API client implementations
│   │   ├── base/             # Base client with retry/circuit breaker
│   │   └── integrations/     # Individual API clients
│   ├── components/           # Dashboard components
│   │   └── dashboard/        # HTML/JS/CSS dashboard files
│   ├── server/               # Express + WebSocket server
│   ├── utils/                # Node.js utilities
│   │   ├── security/         # API key management
│   │   └── monitoring/       # Health monitoring
│   └── test-*.js            # Test scripts
├── data/                     # Database storage (gitignored)
├── node_modules/             # Node.js dependencies (gitignored)
├── .env                      # Environment variables (gitignored)
├── main.py                   # Python app entry point
├── package.json              # Node.js dependencies
├── requirements.txt          # Python dependencies
├── PHASE2_QUICK_REFERENCE.md # API integration guide
└── PHASE3_QUICK_REFERENCE.md # Dashboard guide
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes (ensure no API keys are included)
4. Push to the branch
5. Create a Pull Request

## Documentation

- [Phase 2 Quick Reference](PHASE2_QUICK_REFERENCE.md) - API integration guide
- [Phase 3 Quick Reference](PHASE3_QUICK_REFERENCE.md) - Dashboard guide
- [Phase 4 & 5 Documentation](PHASE4_5_DOCUMENTATION.md) - Testing and deployment guide
- [API Integration README](src/README-API-INTEGRATION.md) - Detailed API docs
- [Dashboard README](src/README-DASHBOARD.md) - Dashboard documentation
- [Project Summary](PROJECT_SUMMARY.md) - Complete project overview

## Recent Updates (v2.0)

### What's New
1. **Enterprise-grade API Integration**
   - 8 API clients with automatic retry and circuit breakers
   - WebSocket support for real-time data
   - Performance metrics and health monitoring

2. **Real-time Trading Dashboard**
   - Live market data with price charts
   - News aggregation with sentiment analysis
   - Social media monitoring (Twitter/Reddit)
   - Trading signal visualization

3. **Enhanced Security**
   - AES-256 encryption for API keys
   - Secure key rotation capabilities
   - Audit trail for all API usage

4. **Monitoring & Alerts**
   - Real-time API health status
   - Automatic failure detection
   - WebSocket push notifications

## License

This project is proprietary software. All rights reserved.
