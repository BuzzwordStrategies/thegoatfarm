# Phase 3 Quick Reference - Crypto Trading Dashboard

## 🚀 Quick Start

```bash
# 1. Export environment variables
npm run export-env

# 2. Start the dashboard server
npm start

# 3. Open browser
http://localhost:3001
```

## 📁 File Structure

```
src/
├── components/dashboard/
│   ├── index.html       # Main dashboard UI
│   ├── dashboard.js     # Dashboard logic
│   └── styles.css       # Custom styles
├── server/
│   └── index.js         # Express + WebSocket server
└── README-DASHBOARD.md  # Full documentation
```

## 🌐 Server Endpoints

### WebSocket
- **URL**: `ws://localhost:3002`
- **Auto-reconnect**: Yes (5 seconds)

### REST API
```bash
GET  /                          # Dashboard UI
GET  /api/health               # Health check
GET  /api/dashboard/initial    # Initial data
GET  /api/market/:symbol       # Market data
GET  /api/signal/:symbol       # Trading signal
POST /api/social/twitter/add   # Add Twitter account
POST /api/social/reddit/add    # Add subreddit
```

## 📊 Dashboard Features

### 1. Overview Tab
- Live BTC/USD price
- Market sentiment gauge
- API health status
- Latest trading signal
- Price chart (Chart.js)
- Recent news feed

### 2. News Feed Tab
- Real-time crypto news
- Search functionality
- Source filtering
- Sentiment badges
- External links

### 3. Social Bucket Tab
- Twitter monitoring
- Reddit tracking
- Add/remove accounts
- Engagement metrics

### 4. Trading Signals Tab
- AI-powered signals
- Confidence levels
- Price history
- Recommendations

### 5. API Status Tab
- Individual API health
- Response times
- Success rates
- Circuit breaker status

## 🔄 WebSocket Events

### Client → Server
```javascript
// Subscribe to all updates
{ type: 'subscribe', channels: ['all'] }

// Get current status
{ type: 'get-status' }

// Get market data
{ type: 'get-market-data', symbol: 'BTC/USD' }
```

### Server → Client
```javascript
// API status
{ type: 'api-status', payload: {...} }

// Market update
{ type: 'market-update', payload: {...} }

// News update
{ type: 'news-update', payload: [...] }

// Trading signal
{ type: 'signal', payload: {...} }

// Alert
{ type: 'alert', payload: { message: '...', type: 'error' } }
```

## ⚙️ Configuration

### Update Intervals (src/server/index.js)
```javascript
// Market data: 1 minute
setInterval(updateMarket, 60000);

// API status: 30 seconds
setInterval(updateStatus, 30000);

// News: 10 minutes
startNewsMonitoring(600000);

// Social: 30 minutes
startSocialMonitoring({ interval: 1800000 });
```

## 🎨 UI Customization

### Dark Theme (Default)
- Tailwind CSS via CDN
- Custom styles in styles.css
- Chart.js for visualizations

### Adding Social Accounts
1. Go to Social Bucket tab
2. Click "+ Add Account"
3. Enter username/subreddit
4. Data flows automatically

## 🛠️ Troubleshooting

### No Data Showing
```bash
# Check API keys
npm run export-env

# Verify server running
npm start

# Check browser console
F12 → Console tab
```

### WebSocket Disconnected
- Auto-reconnects in 5 seconds
- Check port 3002 availability
- Review firewall settings

### Dashboard Not Loading
- Verify port 3001 is free
- Check server logs
- Clear browser cache

## 📈 Performance Tips

1. **Limit Social Accounts**: 5-10 max per platform
2. **Adjust Intervals**: Increase for lower load
3. **Monitor Memory**: Check server resource usage
4. **Use Chrome/Firefox**: Best WebSocket support

## 🔧 Development

### Add New Feature
1. Update WebSocket events
2. Add handler in dashboard.js
3. Create API endpoint
4. Update UI component

### Debug Mode
```bash
DEBUG=true npm start
```

### Monitor WebSocket
```javascript
// Browser console
dashboard.ws.addEventListener('message', e => console.log(JSON.parse(e.data)));
```

## 📋 NPM Scripts

```bash
npm start         # Start dashboard server
npm run server    # Same as start
npm run dev       # Same as start
npm run export-env # Export Python env vars
npm run audit     # Run API audit
npm run test-api  # Test API integration
```

## 🚨 Important Notes

1. **API Keys**: Never commit .env file
2. **Ports**: 3001 (HTTP), 3002 (WebSocket)
3. **Security**: Add authentication for production
4. **CORS**: Configured for local development
5. **Rate Limits**: Handled by circuit breakers

## 💡 Pro Tips

- Use multiple browser tabs for testing
- Monitor Network tab for WebSocket frames
- Check Application → Local Storage for settings
- Use responsive mode to test mobile view
- Export console logs for debugging

---

**Full Documentation**: src/README-DASHBOARD.md 