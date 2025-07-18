# Crypto Trading Dashboard - Phase 3

## Overview

This is a real-time cryptocurrency trading dashboard that provides:

- 📊 **Live Market Data**: Real-time price updates and charts
- 📰 **News Feed**: Aggregated crypto news from multiple sources
- 🐦 **Social Monitoring**: Twitter and Reddit sentiment tracking
- 📈 **Trading Signals**: AI-powered buy/sell recommendations
- 🏥 **API Health Status**: Monitor all connected services

## Features

### 1. Real-time WebSocket Updates
- Live price data streaming
- Instant news alerts
- Real-time API status monitoring
- Push notifications for important events

### 2. Multi-Tab Interface
- **Overview**: Market summary, charts, and recent activity
- **News Feed**: Searchable, filterable crypto news
- **Social Bucket**: Twitter and Reddit monitoring
- **Trading Signals**: AI-generated trading recommendations
- **API Status**: Health monitoring for all services

### 3. Interactive Components
- Price charts with Chart.js
- Sentiment analysis visualization
- Customizable social media feeds
- Responsive design for all devices

## Quick Start

### 1. Export Environment Variables
```bash
npm run export-env
```

### 2. Start the Dashboard Server
```bash
npm start
```

### 3. Open Dashboard
Navigate to: http://localhost:3001

## Architecture

```
┌─────────────────────────┐
│   Dashboard (HTML/JS)   │
├─────────────────────────┤
│    WebSocket Client     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   Express Server        │
├─────────────────────────┤
│   WebSocket Server      │
├─────────────────────────┤
│   Unified API Manager   │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│   External APIs         │
│  - Coinbase             │
│  - CoinDesk             │
│  - TAAPI                │
│  - ScrapingBee          │
│  - AI Services          │
└─────────────────────────┘
```

## WebSocket Events

### Client → Server
```javascript
// Subscribe to updates
{ type: 'subscribe', channels: ['all'] }

// Request current status
{ type: 'get-status' }

// Request market data
{ type: 'get-market-data', symbol: 'BTC/USD' }
```

### Server → Client
```javascript
// API status update
{ type: 'api-status', payload: { ... } }

// Market data update
{ type: 'market-update', payload: { ... } }

// News update
{ type: 'news-update', payload: [...] }

// Trading signal
{ type: 'signal', payload: { ... } }

// Alert/notification
{ type: 'alert', payload: { message: '...', type: 'error|success|info' } }
```

## Dashboard Components

### 1. Header
- Connection status indicator
- Refresh button
- Notification bell with badge
- Settings (future enhancement)

### 2. Overview Tab
- BTC/USD price with 24h change
- Market sentiment gauge
- Active APIs counter
- Latest trading signal
- Price chart
- Recent news feed

### 3. News Feed Tab
- Real-time news aggregation
- Search functionality
- Source filtering
- Sentiment badges (Bullish/Bearish)
- External links

### 4. Social Bucket Tab
- Twitter feed monitoring
- Reddit post tracking
- Add/remove accounts and subreddits
- Engagement metrics
- Direct links to sources

### 5. Trading Signals Tab
- AI-generated signals
- Confidence levels
- Price at signal time
- Detailed recommendations
- Historical signals

### 6. API Status Tab
- Individual API health
- Response times
- Success rates
- Circuit breaker status
- Last check timestamps

## Customization

### Adding New Social Accounts
1. Click the "+ Add Account" button in the Social tab
2. Enter username (Twitter) or subreddit name (Reddit)
3. Data will start flowing within the next update cycle

### Modifying Update Intervals
Edit `src/server/index.js`:
```javascript
// Market data updates (default: 1 minute)
setInterval(async () => { ... }, 60000);

// API status updates (default: 30 seconds)
setInterval(() => { ... }, 30000);

// News monitoring (default: 10 minutes)
await apiManager.startNewsMonitoring(600000);

// Social monitoring (default: 30 minutes)
await apiManager.startSocialMonitoring({ interval: 1800000 });
```

### Styling
The dashboard uses:
- Tailwind CSS (via CDN)
- Custom CSS in `styles.css`
- Dark theme by default

## API Endpoints

### REST API
- `GET /` - Serve dashboard
- `GET /api/health` - Health check
- `GET /api/dashboard/initial` - Initial data load
- `GET /api/market/:symbol` - Get market data
- `GET /api/signal/:symbol` - Get trading signal
- `POST /api/social/twitter/add` - Add Twitter account
- `POST /api/social/reddit/add` - Add subreddit

### WebSocket
- `ws://localhost:3002` - Real-time updates

## Security Considerations

1. **API Keys**: Never exposed to frontend
2. **CORS**: Configured for cross-origin requests
3. **WebSocket**: Authentication can be added
4. **Rate Limiting**: Implemented via circuit breakers

## Troubleshooting

### Dashboard Not Loading
1. Check server is running: `npm start`
2. Verify port 3001 is available
3. Check browser console for errors

### No Data Showing
1. Verify API keys are configured
2. Check server logs for errors
3. Ensure APIs are accessible

### WebSocket Disconnected
1. Check WebSocket port 3002
2. Look for firewall issues
3. Server auto-reconnects after 5 seconds

## Future Enhancements

1. **User Authentication**: Login system
2. **Persistent Settings**: Save preferences
3. **Multiple Portfolios**: Track different accounts
4. **Advanced Charts**: More technical indicators
5. **Trade Execution**: Place orders from dashboard
6. **Mobile App**: React Native version
7. **Alerts**: Email/SMS notifications
8. **Backtesting**: Historical strategy testing

## Development

### File Structure
```
src/
├── components/
│   └── dashboard/
│       ├── index.html      # Main dashboard
│       ├── dashboard.js    # JavaScript logic
│       └── styles.css      # Custom styles
└── server/
    └── index.js           # Express + WebSocket server
```

### Adding New Features
1. Update WebSocket message types
2. Add event handlers in dashboard.js
3. Create new API endpoints if needed
4. Update UI components

### Debugging
- Enable debug mode: `DEBUG=true npm start`
- Check browser DevTools Network tab
- Monitor WebSocket messages
- Review server console logs 