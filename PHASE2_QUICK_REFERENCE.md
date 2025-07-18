# Phase 2 Quick Reference - API Integration Layer

## 🚀 Quick Start

### 1. Export Python Environment (if needed)
```bash
npm run export-env
```

### 2. Test API Integration
```bash
npm run test-api
```

This will:
- Initialize all API clients
- Test connectivity
- Fetch market data
- Generate trading signals
- Start monitoring

## 📊 Key Features Implemented

### Base API Client (`src/api/base/api-client.js`)
- ✅ Automatic retry with exponential backoff
- ✅ Circuit breaker pattern (Opossum)
- ✅ Request/response interceptors
- ✅ Performance metrics tracking
- ✅ Enhanced error handling

### API Clients Created
1. **Coinbase** - Trading, WebSocket feeds, technical analysis
2. **CoinDesk** - Price data, news, indices
3. **TAAPI** - 20+ technical indicators
4. **ScrapingBee** - Web scraping, sentiment analysis
5. **Perplexity** - AI analysis
6. **Grok** - Trend analysis
7. **Anthropic** - Claude integration
8. **Twitter** - Social sentiment

### Unified API Manager (`src/api/api-manager.js`)
- 🔄 Aggregates data from all sources
- 📈 Generates trading signals
- 📰 Automated news monitoring
- 🐦 Social media monitoring
- 🏥 Health status tracking

## 💻 Code Examples

### Get Market Data
```javascript
const UnifiedAPIManager = require('./src/api/api-manager');
const apiManager = new UnifiedAPIManager();
await apiManager.initialize();

// Get aggregated market data
const data = await apiManager.getAggregatedMarketData('BTC/USD');
console.log('BTC Price:', data.averagePrice);
console.log('Sentiment:', data.sentiment.recommendation);
```

### Generate Trading Signal
```javascript
const signal = await apiManager.generateTradingSignal('BTC/USD', '1h');
console.log('Signal:', signal.signal); // BUY/SELL/HOLD
console.log('Confidence:', signal.confidence);
```

### Access Individual APIs
```javascript
// Coinbase
const coinbase = apiManager.getClient('coinbase');
const ticker = await coinbase.getProductTicker('BTC-USD');

// TAAPI
const taapi = apiManager.getClient('taapi');
const rsi = await taapi.getRSI('binance', 'BTC/USDT', '1h');

// ScrapingBee
const scraper = apiManager.getClient('scrapingbee');
const news = await scraper.scrapeCryptoNews();
```

### Monitor Events
```javascript
// API failures
apiManager.on('api-critical', (data) => {
  console.error(`${data.api} is down!`);
});

// Important news
apiManager.on('important-news', (data) => {
  console.log('Breaking:', data.articles);
});

// Sentiment changes
apiManager.on('sentiment-update', (data) => {
  console.log('Market sentiment:', data.recommendation);
});
```

## 🔧 Circuit Breaker States

- **Closed** ✅ - Normal operation
- **Open** 🚫 - Too many failures, rejecting requests
- **Half-Open** ⚡ - Testing if service recovered

## 📈 Metrics Available

```javascript
const metrics = apiManager.getClient('coinbase').getMetrics();
// Returns:
// - totalRequests
// - successRate
// - averageResponseTime
// - errors (last 100)
// - circuitBreakerState
```

## 🛡️ Error Handling

All errors include:
- `error.api` - Which API failed
- `error.status` - HTTP status code
- `error.data` - Response body
- `error.message` - Error description

## 📁 File Structure

```
src/
├── api/
│   ├── base/
│   │   └── api-client.js
│   ├── integrations/
│   │   ├── coinbase-client.js
│   │   ├── coindesk-client.js
│   │   ├── taapi-client.js
│   │   ├── scrapingbee-client.js
│   │   └── [other clients]
│   └── api-manager.js
├── test-api-integration.js
└── README-API-INTEGRATION.md
```

## 🔍 Troubleshooting

### API Key Issues
```bash
# Re-export from Python environment
npm run export-env

# Check current keys
cat src/.env
```

### Circuit Breaker Open
- Wait 30 seconds for reset
- Check API credentials
- Review error logs

### High Latency
- Check network connection
- Verify API rate limits
- Monitor circuit breaker metrics

## 📚 Documentation

- Full docs: `src/README-API-INTEGRATION.md`
- API examples: `src/test-api-integration.js`
- Phase 1 audit: `src/README-API-AUDIT.md` 