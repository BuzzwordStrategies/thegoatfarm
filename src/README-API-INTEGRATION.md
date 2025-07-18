# API Integration Layer - Phase 2

## Overview

This robust API integration layer provides enterprise-grade connectivity to cryptocurrency and AI APIs with:

- 🔄 **Automatic Retry Logic**: Intelligent retry with exponential backoff
- 🚦 **Circuit Breakers**: Prevent cascading failures with Opossum
- 📊 **Real-time Metrics**: Track performance and error rates
- 🔐 **Secure Key Management**: Integrated with Phase 1 security layer
- 📡 **WebSocket Support**: Real-time data streaming from exchanges
- 🧠 **AI Integration**: Connect to Perplexity, Grok, and Claude

## Architecture

```
┌─────────────────────────────────────┐
│      Unified API Manager            │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐          │
│  │ Health  │  │  Key    │          │
│  │ Monitor │  │ Manager │          │
│  └─────────┘  └─────────┘          │
├─────────────────────────────────────┤
│         Base API Client             │
│  • Retry Logic                      │
│  • Circuit Breaker                  │
│  • Metrics Collection               │
├─────────────────────────────────────┤
│  API Clients                        │
│  ┌──────────┐ ┌──────────┐         │
│  │ Coinbase │ │ CoinDesk │         │
│  └──────────┘ └──────────┘         │
│  ┌──────────┐ ┌──────────┐         │
│  │  TAAPI   │ │ScrapingBee│        │
│  └──────────┘ └──────────┘         │
│  ┌──────────┐ ┌──────────┐         │
│  │   AI     │ │ Twitter  │         │
│  └──────────┘ └──────────┘         │
└─────────────────────────────────────┘
```

## Features

### 1. Base API Client

All API clients inherit from a robust base client that provides:

- **Automatic Retries**: 3 attempts with exponential backoff
- **Circuit Breakers**: Opens after 50% error rate
- **Request/Response Interceptors**: For auth and metrics
- **Performance Tracking**: Response times and success rates
- **Error Enhancement**: Detailed error information

### 2. API Clients

#### Coinbase Client
- Full trading API support
- WebSocket feed subscriptions
- Built-in technical indicators (MA, RSI)
- Order validation and management

#### CoinDesk Client
- Real-time price data
- Historical prices
- News and sentiment analysis
- Market indices

#### TAAPI Client
- 20+ technical indicators
- Pattern recognition
- Multi-indicator analysis
- Trading signal generation

#### ScrapingBee Client
- Crypto news aggregation
- Reddit sentiment analysis
- Google search integration
- Market sentiment scoring

### 3. Unified API Manager

The central coordinator that provides:

- **Aggregated Market Data**: Combine data from all sources
- **Trading Signal Generation**: Technical + sentiment analysis
- **Automated Monitoring**: News and social media
- **Health Management**: Real-time API status
- **Event-Driven Architecture**: React to market changes

## Usage

### Quick Start

```javascript
const UnifiedAPIManager = require('./src/api/api-manager');

async function main() {
  // Initialize the manager
  const apiManager = new UnifiedAPIManager();
  await apiManager.initialize();
  
  // Get aggregated market data
  const marketData = await apiManager.getAggregatedMarketData('BTC/USD');
  console.log('BTC Price:', marketData.averagePrice);
  
  // Generate trading signal
  const signal = await apiManager.generateTradingSignal('BTC/USD', '1h');
  console.log('Signal:', signal.signal);
  console.log('Confidence:', signal.confidence);
  
  // Start monitoring
  await apiManager.startNewsMonitoring();
  await apiManager.startSocialMonitoring({
    redditSubreddits: ['bitcoin', 'cryptocurrency'],
    twitterAccounts: ['elonmusk']
  });
}
```

### Individual Client Usage

```javascript
// Access specific API client
const coinbaseClient = apiManager.getClient('coinbase');

// Get account info
const accounts = await coinbaseClient.getAccounts();

// Place an order
const order = await coinbaseClient.placeOrder({
  side: 'buy',
  product_id: 'BTC-USD',
  type: 'limit',
  price: '50000',
  size: '0.01'
});

// Subscribe to WebSocket feed
const ws = await coinbaseClient.subscribeToFeed(
  ['BTC-USD'],
  ['ticker', 'level2'],
  (message) => console.log('Update:', message),
  (error) => console.error('Error:', error)
);
```

### Technical Indicators

```javascript
// Get RSI
const taapi = apiManager.getClient('taapi');
const rsi = await taapi.getRSI('binance', 'BTC/USDT', '1h');

// Get multiple indicators at once
const indicators = await taapi.getMultipleIndicators('binance', 'BTC/USDT', '1h');
console.log('RSI:', indicators.rsi.value);
console.log('MACD:', indicators.macd);
console.log('Bollinger Bands:', indicators.bbands);

// Generate complete trading signal
const signal = await taapi.getTradingSignal('binance', 'BTC/USDT', '1h');
```

### News and Sentiment

```javascript
// Scrape crypto news
const scrapingBee = apiManager.getClient('scrapingbee');
const news = await scrapingBee.scrapeCryptoNews(['coindesk', 'cointelegraph']);

// Analyze sentiment
const sentiment = await scrapingBee.analyzeCryptoSentiment('bitcoin');
console.log('Sentiment:', sentiment.recommendation); // BULLISH/BEARISH/NEUTRAL

// Monitor Reddit
const redditPosts = await scrapingBee.scrapeReddit('bitcoin', 'hot', 25);
```

## Event System

The API Manager emits various events:

```javascript
// Critical API failure
apiManager.on('api-critical', (data) => {
  console.error(`API ${data.api} is down!`);
  // Implement fallback logic
});

// Important news detected
apiManager.on('important-news', (data) => {
  console.log('Breaking news:', data.articles);
  // React to market-moving news
});

// Sentiment shift
apiManager.on('sentiment-update', (data) => {
  if (data.score > 50) {
    console.log('Market sentiment turning bullish');
  }
});

// Social media updates
apiManager.on('social-update', (data) => {
  // Process social signals
});
```

## Circuit Breaker Configuration

Each API client has configurable circuit breaker settings:

```javascript
new CoinbaseClient(keyManager, {
  circuitBreakerTimeout: 30000,      // Request timeout
  errorThresholdPercentage: 50,       // Open circuit at 50% errors
  resetTimeout: 30000,                // Try again after 30s
  volumeThreshold: 10                 // Minimum requests before opening
});
```

## Metrics and Monitoring

Get real-time metrics for any API:

```javascript
const metrics = coinbaseClient.getMetrics();
console.log('Success Rate:', metrics.successRate);
console.log('Avg Response Time:', metrics.averageResponseTime);
console.log('Total Requests:', metrics.totalRequests);
console.log('Recent Errors:', metrics.errors);
```

## Error Handling

All errors are enhanced with additional context:

```javascript
try {
  await coinbaseClient.getAccount('invalid-id');
} catch (error) {
  console.error('API:', error.api);           // 'Coinbase'
  console.error('Status:', error.status);     // 404
  console.error('Message:', error.message);   // Original error message
  console.error('Data:', error.data);         // Response body
}
```

## Testing

Run the comprehensive test suite:

```bash
# Test the entire API integration layer
npm run test-api

# Test individual components
npm run test-key-manager
npm run test-health-monitor
```

## Production Deployment

1. **Environment Variables**: Ensure all API keys are properly configured
2. **Circuit Breaker Tuning**: Adjust thresholds based on API reliability
3. **Monitoring Intervals**: Set appropriate intervals for news/social monitoring
4. **Error Logging**: Implement proper logging for production
5. **Rate Limiting**: Be aware of API rate limits

## Security Considerations

- All API keys are encrypted at rest
- Keys are never logged or exposed
- Circuit breakers prevent abuse during outages
- Sanitized headers in debug logs
- Secure WebSocket authentication

## Troubleshooting

### Circuit Breaker Open
- Check API health status
- Review error logs for patterns
- Verify API credentials
- Check network connectivity

### High Error Rate
- Monitor specific error types
- Check for API changes
- Verify rate limits
- Review retry configuration

### WebSocket Disconnections
- Check network stability
- Verify authentication
- Monitor message volume
- Implement reconnection logic

## Future Enhancements

- GraphQL support for efficient queries
- More AI model integrations
- Advanced caching strategies
- Multi-region failover
- Custom indicator development 