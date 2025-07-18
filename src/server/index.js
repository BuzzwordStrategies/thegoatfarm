const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const UnifiedAPIManager = require('../api/api-manager');
const securityMiddleware = require('../utils/security/security-middleware');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../../.env') });

const app = express();
const PORT = process.env.PORT || 3001;

// Apply security middleware
app.use(securityMiddleware.requestLogger);
app.use(securityMiddleware.helmet);
app.use(securityMiddleware.cors);
app.use(securityMiddleware.rateLimiter);
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Serve static files from dashboard
app.use(express.static(path.join(__dirname, '../components/dashboard')));

// Initialize API Manager
const apiManager = new UnifiedAPIManager();

// WebSocket Server
const wss = new WebSocket.Server({ port: 3002 });

const broadcast = (data) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
};

// Initialize and start services
(async () => {
  try {
    await apiManager.initialize();
    
    // Set up API Manager event listeners
    apiManager.on('api-critical', (data) => {
      broadcast({ type: 'alert', payload: { 
        message: `API Critical: ${data.api}`, 
        type: 'error' 
      }});
    });
    
    apiManager.on('important-news', (data) => {
      broadcast({ type: 'news-update', payload: data.articles });
    });
    
    apiManager.on('sentiment-update', (data) => {
      broadcast({ type: 'sentiment-update', payload: data });
    });
    
    apiManager.on('social-update', (data) => {
      broadcast({ type: 'social-update', payload: data });
    });
    
    // Start monitoring services
    await apiManager.startNewsMonitoring(600000); // 10 minutes
    await apiManager.startSocialMonitoring({
      twitterAccounts: ['elonmusk', 'VitalikButerin', 'aantonop'],
      redditSubreddits: ['cryptocurrency', 'bitcoin', 'ethereum'],
      interval: 1800000 // 30 minutes
    });
    
    // Periodic market data updates
    setInterval(async () => {
      try {
        const marketData = await apiManager.getAggregatedMarketData('BTC/USD');
        broadcast({ type: 'market-update', payload: marketData });
        
        const signal = await apiManager.generateTradingSignal('BTC/USD');
        broadcast({ type: 'signal', payload: signal });
      } catch (error) {
        console.error('Market update error:', error);
      }
    }, 60000); // 1 minute
    
    // Periodic API status updates
    setInterval(() => {
      const status = apiManager.getStatus();
      broadcast({ type: 'api-status', payload: status });
    }, 30000); // 30 seconds
    
    console.log('✅ All services initialized and running');
    
  } catch (error) {
    console.error('Failed to initialize services:', error);
    process.exit(1);
  }
})();

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('New WebSocket connection');
  
  // Send initial status
  ws.send(JSON.stringify({
    type: 'connected',
    payload: { message: 'Connected to trading dashboard' }
  }));
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      handleWebSocketMessage(ws, data);
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});

const handleWebSocketMessage = async (ws, data) => {
  switch (data.type) {
    case 'subscribe':
      // Handle subscription to specific channels
      ws.channels = data.channels;
      break;
      
    case 'get-status':
      ws.send(JSON.stringify({
        type: 'api-status',
        payload: apiManager.getStatus()
      }));
      break;
      
    case 'get-market-data':
      const marketData = await apiManager.getAggregatedMarketData(data.symbol || 'BTC/USD');
      ws.send(JSON.stringify({
        type: 'market-update',
        payload: marketData
      }));
      break;
      
    default:
      console.log('Unknown WebSocket message type:', data.type);
  }
};

// REST API Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/dashboard/initial', async (req, res) => {
  try {
    const [apiStatus, marketData] = await Promise.all([
      apiManager.getStatus(),
      apiManager.getAggregatedMarketData('BTC/USD')
    ]);
    
    let news = [];
    let signals = [];
    
    try {
      news = await apiManager.clients.scrapingbee.scrapeCryptoNews();
    } catch (error) {
      console.error('Failed to fetch news:', error);
    }
    
    try {
      const signal = await apiManager.generateTradingSignal('BTC/USD');
      signals = [signal];
    } catch (error) {
      console.error('Failed to generate signal:', error);
    }
    
    res.json({
      apiStatus,
      marketData,
      news: news.slice(0, 20),
      socialData: { twitter: {}, reddit: {} },
      signals
    });
  } catch (error) {
    console.error('Initial data load error:', error);
    res.status(500).json({ error: 'Failed to load dashboard data' });
  }
});

app.post('/api/social/twitter/add', async (req, res) => {
  const { username } = req.body;
  // Add logic to add Twitter account to monitoring
  res.json({ success: true, username });
});

app.post('/api/social/reddit/add', async (req, res) => {
  const { subreddit } = req.body;
  // Add logic to add subreddit to monitoring
  res.json({ success: true, subreddit });
});

app.get('/api/market/:symbol', async (req, res) => {
  try {
    const data = await apiManager.getAggregatedMarketData(req.params.symbol);
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/signal/:symbol', async (req, res) => {
  try {
    const signal = await apiManager.generateTradingSignal(req.params.symbol);
    res.json(signal);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Serve dashboard on root
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../components/dashboard/index.html'));
});

// Apply API key validation to protected routes
app.use('/api/market', securityMiddleware.validateAPIKey, securityMiddleware.apiRateLimiter);
app.use('/api/signal', securityMiddleware.validateAPIKey, securityMiddleware.apiRateLimiter);

// Error handling (must be last)
app.use(securityMiddleware.errorHandler);

// Start server
const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📡 WebSocket server running on port 3002`);
  console.log(`🌐 Dashboard available at http://localhost:${PORT}`);
  console.log(`🔒 Security middleware enabled`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await apiManager.shutdown();
  process.exit(0);
}); 