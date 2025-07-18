const EventEmitter = require('events');
const SecureAPIKeyManager = require('../utils/security/api-key-manager');
const APIHealthMonitor = require('../utils/monitoring/api-health-monitor');

// Import all API clients
const CoinbaseAdvancedClient = require('./integrations/coinbase-client');
const CoinDeskClient = require('./integrations/coindesk-client');
const TaapiClient = require('./integrations/taapi-client');
const ScrapingBeeClient = require('./integrations/scrapingbee-client');
const PerplexityClient = require('./integrations/perplexity-client');
const GrokClient = require('./integrations/grok-client');
const AnthropicClient = require('./integrations/anthropic-client');
const TwitterAPIioClient = require('./integrations/twitter-client');

class UnifiedAPIManager extends EventEmitter {
  constructor() {
    super();
    this.keyManager = new SecureAPIKeyManager();
    this.healthMonitor = new APIHealthMonitor();
    this.clients = {};
    this.initialized = false;
  }
  
  async initialize() {
    console.log('🚀 Initializing Unified API Manager...');
    
    // Initialize key manager
    await this.keyManager.initializeFromEnv();
    
    // Initialize API clients
    this.clients = {
      coinbase: new CoinbaseAdvancedClient(this.keyManager),
      coindesk: new CoinDeskClient(this.keyManager),
      taapi: new TaapiClient(this.keyManager),
      scrapingbee: new ScrapingBeeClient(this.keyManager),
      perplexity: new PerplexityClient(this.keyManager),
      grok: new GrokClient(this.keyManager),
      anthropic: new AnthropicClient(this.keyManager),
      twitterapiio: new TwitterAPIioClient(this.keyManager)
    };
    
    // Set up health monitoring
    await this.setupHealthMonitoring();
    
    // Set up event handlers
    this.setupEventHandlers();
    
    this.initialized = true;
    console.log('✅ API Manager initialized successfully');
    
    return this;
  }
  
  async setupHealthMonitoring() {
    // Define health check functions for each API
    const healthChecks = {
      coinbase: async () => {
        const accounts = await this.clients.coinbase.getAccounts(1);
        return { success: true, hasAccounts: accounts.accounts?.length > 0 };
      },
      coindesk: async () => {
        const price = await this.clients.coindesk.getCurrentPrice();
        return { success: true, btcPrice: price };
      },
      taapi: async () => {
        const rsi = await this.clients.taapi.getRSI('binance', 'BTC/USDT', '1h');
        return { success: true, rsi: rsi.value };
      },
      scrapingbee: async () => {
        const result = await this.clients.scrapingbee.scrape('https://example.com');
        return { success: true, statusCode: result.statusCode };
      }
    };
    
    // Start monitoring each API
    for (const [apiName, checkFunction] of Object.entries(healthChecks)) {
      this.healthMonitor.startMonitoring(apiName, checkFunction, 300000); // 5 minutes
    }
    
    // Listen for health events
    this.healthMonitor.on('api-critical', (data) => {
      console.error(`🚨 CRITICAL: ${data.api} is down!`, data);
      this.emit('api-critical', data);
    });
    
    this.healthMonitor.on('high-error-rate', (data) => {
      console.warn(`⚠️  High error rate for ${data.api}:`, data);
      this.emit('api-warning', data);
    });
  }
  
  setupEventHandlers() {
    // Auto-rotate keys on repeated auth failures
    this.on('auth-failure', async (data) => {
      console.error(`🔐 Auth failure for ${data.api}`, data);
      // Implement key rotation logic here
    });
    
    // Log all API calls for debugging
    if (process.env.DEBUG === 'true') {
      this.on('api-call', (data) => {
        console.log(`📞 API Call: ${data.api}.${data.method}`, data.params);
      });
    }
  }
  
  // Unified method to get any client
  getClient(apiName) {
    if (!this.initialized) {
      throw new Error('API Manager not initialized. Call initialize() first.');
    }
    
    const client = this.clients[apiName];
    if (!client) {
      throw new Error(`Unknown API client: ${apiName}`);
    }
    
    return client;
  }
  
  // Market Data Aggregation
  async getAggregatedMarketData(symbol = 'BTC/USD') {
    const [ticker, tradingPair] = symbol.split('/');
    
    const marketData = {
      symbol,
      timestamp: new Date().toISOString(),
      prices: {},
      indicators: {},
      news: [],
      sentiment: {}
    };
    
    // Fetch data from multiple sources in parallel
    const dataPromises = [
      // Price data
      this.clients.coinbase.getProductTicker(`${ticker}-${tradingPair}`)
        .then(data => marketData.prices.coinbase = data)
        .catch(err => console.error('Coinbase price error:', err)),
        
      this.clients.coindesk.getCurrentPrice(tradingPair)
        .then(data => marketData.prices.coindesk = data)
        .catch(err => console.error('CoinDesk price error:', err)),
      
      // Technical indicators
      this.clients.taapi.getMultipleIndicators('binance', symbol, '1h')
        .then(data => marketData.indicators = data)
        .catch(err => console.error('TAAPI indicators error:', err)),
      
      // News and sentiment
      this.clients.scrapingbee.scrapeCryptoNews(['coindesk', 'cointelegraph'])
        .then(data => marketData.news = data.slice(0, 5))
        .catch(err => console.error('News scraping error:', err)),
        
      this.clients.scrapingbee.analyzeCryptoSentiment(ticker.toLowerCase())
        .then(data => marketData.sentiment = data)
        .catch(err => console.error('Sentiment analysis error:', err))
    ];
    
    await Promise.allSettled(dataPromises);
    
    // Calculate average price
    const prices = Object.values(marketData.prices)
      .map(p => parseFloat(p.rate || p.price || p))
      .filter(p => !isNaN(p));
      
    if (prices.length > 0) {
      marketData.averagePrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    }
    
    return marketData;
  }
  
  // Trading Signal Generation
  async generateTradingSignal(symbol, timeframe = '1h') {
    const marketData = await this.getAggregatedMarketData(symbol);
    const technicalSignal = await this.clients.taapi.getTradingSignal(
      'binance', 
      symbol, 
      timeframe
    );
    
    // Combine technical and sentiment analysis
    const sentimentScore = parseFloat(marketData.sentiment.score) || 0;
    const technicalScore = technicalSignal.bullishSignals - technicalSignal.bearishSignals;
    
    const compositeScore = (technicalScore * 0.7) + (sentimentScore * 0.3);
    
    return {
      symbol,
      timeframe,
      timestamp: new Date().toISOString(),
      technical: technicalSignal,
      sentiment: marketData.sentiment,
      price: marketData.averagePrice,
      signal: compositeScore > 1 ? 'STRONG_BUY' :
             compositeScore > 0 ? 'BUY' :
             compositeScore < -1 ? 'STRONG_SELL' :
             compositeScore < 0 ? 'SELL' : 'HOLD',
      confidence: Math.abs(compositeScore) * 10,
      recommendation: this.generateRecommendation(compositeScore, marketData)
    };
  }
  
  generateRecommendation(score, marketData) {
    const indicators = marketData.indicators;
    const recommendations = [];
    
    if (score > 1) {
      recommendations.push('Strong buy signal detected.');
      if (indicators.rsi && indicators.rsi.value < 30) {
        recommendations.push('RSI indicates oversold conditions.');
      }
      if (indicators.macd && indicators.macd.valueMACD > indicators.macd.valueMACDSignal) {
        recommendations.push('MACD shows bullish crossover.');
      }
    } else if (score < -1) {
      recommendations.push('Strong sell signal detected.');
      if (indicators.rsi && indicators.rsi.value > 70) {
        recommendations.push('RSI indicates overbought conditions.');
      }
      if (indicators.macd && indicators.macd.valueMACD < indicators.macd.valueMACDSignal) {
        recommendations.push('MACD shows bearish crossover.');
      }
    } else {
      recommendations.push('Market conditions are neutral.');
      recommendations.push('Consider waiting for clearer signals.');
    }
    
    // Add volatility warning
    if (indicators.atr && indicators.atr.value > 100) {
      recommendations.push('⚠️  High volatility detected. Use appropriate position sizing.');
    }
    
    return recommendations.join(' ');
  }
  
  // Automated News Monitoring
  async startNewsMonitoring(interval = 600000) { // 10 minutes
    console.log('📰 Starting automated news monitoring...');
    
    const monitorNews = async () => {
      try {
        const news = await this.clients.scrapingbee.scrapeCryptoNews();
        const importantNews = news.filter(article => 
          article.title.toLowerCase().match(/breaking|urgent|alert|hack|crash|surge|rally/)
        );
        
        if (importantNews.length > 0) {
          this.emit('important-news', {
            timestamp: new Date().toISOString(),
            articles: importantNews
          });
        }
        
        // Analyze sentiment shift
        const sentiment = await this.clients.scrapingbee.analyzeCryptoSentiment();
        this.emit('sentiment-update', sentiment);
        
      } catch (error) {
        console.error('News monitoring error:', error);
      }
    };
    
    // Initial check
    await monitorNews();
    
    // Set up interval
    this.newsMonitoringInterval = setInterval(monitorNews, interval);
  }
  
  // Social Media Monitoring
  async startSocialMonitoring(config) {
    console.log('🐦 Starting social media monitoring...');
    
    const { 
      twitterAccounts = [], 
      redditSubreddits = [], 
      interval = 1800000 // 30 minutes
    } = config;
    
    const monitorSocial = async () => {
      const socialData = {
        timestamp: new Date().toISOString(),
        twitter: {},
        reddit: {}
      };
      
      // Monitor Twitter accounts
      for (const account of twitterAccounts) {
        try {
                  const tweets = await this.clients.twitterapiio.getUserTweets(account, 5);
        socialData.twitter[account] = tweets;
      } catch (error) {
        console.error(`Error monitoring Twitter @${account}:`, error);
        }
      }
      
      // Monitor Reddit subreddits
      for (const subreddit of redditSubreddits) {
        try {
          const posts = await this.clients.scrapingbee.scrapeReddit(subreddit, 'hot', 10);
          socialData.reddit[subreddit] = posts;
        } catch (error) {
          console.error(`Error monitoring r/${subreddit}:`, error);
        }
      }
      
      this.emit('social-update', socialData);
    };
    
    // Initial check
    await monitorSocial();
    
    // Set up interval
    this.socialMonitoringInterval = setInterval(monitorSocial, interval);
  }
  
  // Get comprehensive API status
  getStatus() {
    return {
      initialized: this.initialized,
      health: this.healthMonitor.getHealthSummary(),
      apis: Object.keys(this.clients).map(api => ({
        name: api,
        status: this.healthMonitor.getHealthStatus(api)?.status || 'unknown',
        metrics: this.clients[api].getMetrics()
      }))
    };
  }
  
  // Cleanup
  async shutdown() {
    console.log('🛑 Shutting down API Manager...');
    
    // Stop monitoring
    this.healthMonitor.stopAllMonitoring();
    
    if (this.newsMonitoringInterval) {
      clearInterval(this.newsMonitoringInterval);
    }
    
    if (this.socialMonitoringInterval) {
      clearInterval(this.socialMonitoringInterval);
    }
    
    // Close any open connections
    for (const client of Object.values(this.clients)) {
      if (client.cleanup) {
        await client.cleanup();
      }
    }
    
    console.log('✅ API Manager shutdown complete');
  }
}

module.exports = UnifiedAPIManager; 