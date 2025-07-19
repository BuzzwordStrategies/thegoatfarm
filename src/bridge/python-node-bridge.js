const express = require('express');
const WebSocket = require('ws');
const dotenv = require('dotenv');
const cors = require('cors');

dotenv.config();

// Import API clients
const CoinbaseClient = require('../api/integrations/coinbase-client');
const TaapiClient = require('../api/integrations/taapi-client');
const TwitterClient = require('../api/integrations/twitter-client');
const CoindeskClient = require('../api/integrations/coindesk-client');
const ScrapingBeeClient = require('../api/integrations/scrapingbee-client');
const AnthropicClient = require('../api/integrations/anthropic-client');
const PerplexityClient = require('../api/integrations/perplexity-client');
const GrokClient = require('../api/integrations/grok-client');

// Create Express app
const app = express();
app.use(cors());
app.use(express.json());

// WebSocket server
const wss = new WebSocket.Server({ port: 3002 });

// Mock key manager that uses environment variables
const keyManager = {
  getKey: async (service, keyName) => {
    const keyMap = {
      'coinbase': {
        'COINBASE_KEY_NAME': process.env.COINBASE_API_KEY_NAME,
        'COINBASE_PRIVATE_KEY': process.env.COINBASE_API_KEY_PRIVATE_KEY
      },
      'taapi': {
        'TAAPI_API_KEY': process.env.TAAPI_SECRET
      },
      'twitterapiio': {
        'TWITTERAPIIO_API_KEY': process.env.TWITTER_API_KEY || process.env.TWITTERAPI_KEY
      },
      'coindesk': {
        'COINDESK_API_KEY': process.env.COINDESK_API_KEY
      },
      'scrapingbee': {
        'SCRAPINGBEE_API_KEY': process.env.SCRAPINGBEE_API_KEY
      },
      'anthropic': {
        'ANTHROPIC_API_KEY': process.env.ANTHROPIC_API_KEY
      },
      'perplexity': {
        'PERPLEXITY_API_KEY': process.env.PERPLEXITY_API_KEY
      },
      'grok': {
        'GROK_API_KEY': process.env.XAI_API_KEY
      }
    };
    return keyMap[service]?.[keyName];
  }
};

// Initialize API clients
const apiClients = {
  coinbase: new CoinbaseClient(keyManager),
  taapi: new TaapiClient(keyManager),
  twitter: new TwitterClient(keyManager),
  coindesk: new CoindeskClient(keyManager),
  scrapingbee: new ScrapingBeeClient(keyManager),
  anthropic: new AnthropicClient(keyManager),
  perplexity: new PerplexityClient(keyManager),
  grok: new GrokClient(keyManager)
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    uptime: process.uptime(),
    apis: Object.keys(apiClients)
  });
});

// Coinbase endpoints
app.get('/api/coinbase/products', async (req, res) => {
  try {
    const products = await apiClients.coinbase.getProducts();
    res.json({ success: true, data: products });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/coinbase/product/:productId', async (req, res) => {
  try {
    const product = await apiClients.coinbase.getProduct(req.params.productId);
    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/coinbase/candles/:productId', async (req, res) => {
  try {
    const { granularity = 300, limit = 100 } = req.query;
    const candles = await apiClients.coinbase.getCandles(
      req.params.productId,
      parseInt(granularity),
      parseInt(limit)
    );
    res.json({ success: true, data: candles });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// TAAPI endpoints
app.get('/api/taapi/rsi', async (req, res) => {
  try {
    const { exchange, symbol, interval } = req.query;
    const rsi = await apiClients.taapi.getRSI(exchange, symbol, interval);
    res.json({ success: true, data: rsi });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/taapi/macd', async (req, res) => {
  try {
    const { exchange, symbol, interval } = req.query;
    const macd = await apiClients.taapi.getMACD(exchange, symbol, interval);
    res.json({ success: true, data: macd });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/taapi/bbands', async (req, res) => {
  try {
    const { exchange, symbol, interval } = req.query;
    const bbands = await apiClients.taapi.getBBands(exchange, symbol, interval);
    res.json({ success: true, data: bbands });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Twitter endpoints
app.get('/api/twitter/tweets', async (req, res) => {
  try {
    const { query, count = 10 } = req.query;
    const tweets = await apiClients.twitter.searchTweets(query, parseInt(count));
    res.json({ success: true, data: tweets });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/twitter/sentiment', async (req, res) => {
  try {
    const { symbol } = req.query;
    const sentiment = await apiClients.twitter.getCryptoSentiment(symbol);
    res.json({ success: true, data: sentiment });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// AI endpoints
app.post('/api/ai/analyze', async (req, res) => {
  try {
    const { provider, prompt, context } = req.body;
    let response;
    
    switch (provider) {
      case 'anthropic':
        response = await apiClients.anthropic.analyzeMarket(prompt, context);
        break;
      case 'perplexity':
        response = await apiClients.perplexity.searchNews(prompt);
        break;
      case 'grok':
        response = await apiClients.grok.analyzeSentiment(prompt);
        break;
      default:
        throw new Error('Invalid AI provider');
    }
    
    res.json({ success: true, data: response });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// WebSocket connections for real-time data
wss.on('connection', (ws) => {
  console.log('New WebSocket connection established');
  
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);
      
      switch (data.type) {
        case 'subscribe':
          // Handle subscription to real-time data
          handleSubscription(ws, data);
          break;
        case 'unsubscribe':
          // Handle unsubscription
          handleUnsubscription(ws, data);
          break;
        default:
          ws.send(JSON.stringify({ error: 'Unknown message type' }));
      }
    } catch (error) {
      ws.send(JSON.stringify({ error: error.message }));
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket connection closed');
    // Clean up any subscriptions
  });
});

// Real-time data subscriptions
const subscriptions = new Map();

function handleSubscription(ws, data) {
  const { channel, params } = data;
  
  switch (channel) {
    case 'prices':
      // Subscribe to real-time price updates
      const interval = setInterval(async () => {
        try {
          const price = await apiClients.coinbase.getProduct(params.productId);
          ws.send(JSON.stringify({
            channel: 'prices',
            data: price
          }));
        } catch (error) {
          ws.send(JSON.stringify({ error: error.message }));
        }
      }, 5000); // Update every 5 seconds
      
      subscriptions.set(ws, { interval, channel });
      break;
      
    case 'indicators':
      // Subscribe to technical indicators
      const indicatorInterval = setInterval(async () => {
        try {
          const rsi = await apiClients.taapi.getRSI(
            params.exchange,
            params.symbol,
            params.interval
          );
          ws.send(JSON.stringify({
            channel: 'indicators',
            data: { rsi }
          }));
        } catch (error) {
          ws.send(JSON.stringify({ error: error.message }));
        }
      }, 60000); // Update every minute
      
      subscriptions.set(ws, { interval: indicatorInterval, channel });
      break;
  }
}

function handleUnsubscription(ws, data) {
  const subscription = subscriptions.get(ws);
  if (subscription) {
    clearInterval(subscription.interval);
    subscriptions.delete(ws);
  }
}

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Bridge error:', err);
  res.status(500).json({
    success: false,
    error: err.message
  });
});

// Start the server
const PORT = process.env.BRIDGE_PORT || 3001;
app.listen(PORT, () => {
  console.log(`🌉 Python-Node.js Bridge running on port ${PORT}`);
  console.log(`📡 WebSocket server running on port 3002`);
});

module.exports = { app, wss }; 