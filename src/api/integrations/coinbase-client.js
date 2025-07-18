const BaseAPIClient = require('../base/api-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

class CoinbaseAdvancedClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'Coinbase',
      baseURL: 'https://api.coinbase.com',
      timeout: 10000,
      retries: 3,
      retryDelay: 1000
    });
    
    this.keyManager = keyManager;
    this.apiVersion = '2023-12-01';
  }
  
  async getAuthHeaders(config) {
    // Get key name and private key from secure storage
    const keyName = await this.keyManager.getKey('coinbase', 'COINBASE_KEY_NAME');
    const privateKey = await this.keyManager.getKey('coinbase', 'COINBASE_PRIVATE_KEY');
    
    // Generate JWT token
    const token = this.generateJWT(config, keyName, privateKey);
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'CB-VERSION': this.apiVersion
    };
  }
  
  generateJWT(config, keyName, privateKey) {
    const requestMethod = config.method.toUpperCase();
    const requestPath = config.url.startsWith('http') 
      ? new URL(config.url).pathname 
      : config.url;
    const requestHost = 'api.coinbase.com';
    
    const uri = `${requestMethod} ${requestHost}${requestPath}`;
    
    const payload = {
      iss: 'coinbase-cloud',
      nbf: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 120, // 2 minute expiration
      sub: keyName,
      uri: uri
    };
    
    // Clean the private key format
    const cleanedKey = this.formatPrivateKey(privateKey);
    
    // Sign with ES256 (ECDSA)
    const token = jwt.sign(payload, cleanedKey, {
      algorithm: 'ES256',
      header: {
        kid: keyName,
        nonce: uuidv4(),
        typ: 'JWT',
        alg: 'ES256'
      }
    });
    
    return token;
  }
  
  formatPrivateKey(privateKey) {
    // Handle different private key formats
    let cleanKey = privateKey.trim();
    
    // If it's not already in PEM format, convert it
    if (!cleanKey.includes('BEGIN EC PRIVATE KEY')) {
      // Remove any whitespace and newlines
      cleanKey = cleanKey.replace(/\s/g, '');
      
      // Add PEM headers if missing
      if (!cleanKey.startsWith('-----BEGIN')) {
        cleanKey = `-----BEGIN EC PRIVATE KEY-----\n${cleanKey}\n-----END EC PRIVATE KEY-----`;
      }
    }
    
    return cleanKey;
  }
  
  // Account Management
  async getAccounts(limit = 250) {
    return this.get('/api/v3/brokerage/accounts', { limit });
  }
  
  async getAccount(accountId) {
    return this.get(`/api/v3/brokerage/accounts/${accountId}`);
  }
  
  // Products and Market Data
  async getProducts(limit = 1000) {
    return this.get('/api/v3/brokerage/products', { limit });
  }
  
  async getProduct(productId) {
    return this.get(`/api/v3/brokerage/products/${productId}`);
  }
  
  async getProductCandles(productId, start, end, granularity) {
    return this.get(`/api/v3/brokerage/products/${productId}/candles`, {
      start,
      end,
      granularity
    });
  }
  
  async getMarketTrades(productId, limit = 100) {
    return this.get(`/api/v3/brokerage/products/${productId}/ticker`, { limit });
  }
  
  // Best bid/ask
  async getBestBidAsk(productIds) {
    const productIdsParam = Array.isArray(productIds) ? productIds.join(',') : productIds;
    return this.get('/api/v3/brokerage/best_bid_ask', {
      product_ids: productIdsParam
    });
  }
  
  // Order Management
  async createOrder(order) {
    const orderRequest = {
      client_order_id: uuidv4(),
      product_id: order.product_id,
      side: order.side.toUpperCase(),
      order_configuration: {}
    };
    
    // Handle different order types
    if (order.type === 'market') {
      if (order.size) {
        orderRequest.order_configuration.market_market_ioc = {
          base_size: order.size
        };
      } else if (order.funds) {
        orderRequest.order_configuration.market_market_ioc = {
          quote_size: order.funds
        };
      }
    } else if (order.type === 'limit') {
      orderRequest.order_configuration.limit_limit_gtc = {
        base_size: order.size,
        limit_price: order.price,
        post_only: order.post_only || false
      };
    } else if (order.type === 'stop_limit') {
      orderRequest.order_configuration.stop_limit_stop_limit_gtc = {
        base_size: order.size,
        limit_price: order.price,
        stop_price: order.stop_price,
        stop_direction: order.stop_direction || 'STOP_DIRECTION_STOP_DOWN'
      };
    }
    
    return this.post('/api/v3/brokerage/orders', orderRequest);
  }
  
  async cancelOrder(orderId) {
    const orderIds = Array.isArray(orderId) ? orderId : [orderId];
    return this.post('/api/v3/brokerage/orders/batch_cancel', {
      order_ids: orderIds
    });
  }
  
  async getOrders(params = {}) {
    const defaultParams = {
      order_status: params.status || 'OPEN',
      limit: params.limit || 1000,
      product_id: params.product_id,
      order_type: params.order_type,
      order_side: params.order_side,
      start_date: params.start_date,
      end_date: params.end_date
    };
    
    // Remove undefined values
    Object.keys(defaultParams).forEach(key => 
      defaultParams[key] === undefined && delete defaultParams[key]
    );
    
    return this.get('/api/v3/brokerage/orders/historical/batch', defaultParams);
  }
  
  async getOrder(orderId) {
    return this.get(`/api/v3/brokerage/orders/historical/${orderId}`);
  }
  
  async getFills(params = {}) {
    const defaultParams = {
      order_id: params.order_id,
      product_id: params.product_id,
      limit: params.limit || 1000,
      start_sequence_timestamp: params.start_sequence_timestamp,
      end_sequence_timestamp: params.end_sequence_timestamp
    };
    
    // Remove undefined values
    Object.keys(defaultParams).forEach(key => 
      defaultParams[key] === undefined && delete defaultParams[key]
    );
    
    return this.get('/api/v3/brokerage/orders/historical/fills', defaultParams);
  }
  
  // Portfolio Management
  async getPortfolios(portfolioType) {
    return this.get('/api/v3/brokerage/portfolios', {
      portfolio_type: portfolioType
    });
  }
  
  async createPortfolio(name) {
    return this.post('/api/v3/brokerage/portfolios', { name });
  }
  
  async getPortfolioBreakdown(portfolioUuid) {
    return this.get(`/api/v3/brokerage/portfolios/${portfolioUuid}`);
  }
  
  // Transactions
  async getTransactions(params = {}) {
    return this.get('/api/v3/brokerage/transaction_summary', {
      start_date: params.start_date,
      end_date: params.end_date,
      user_native_currency: params.currency || 'USD',
      product_type: params.product_type || 'SPOT',
      limit: params.limit || 100
    });
  }
  
  // Fees
  async getTransactionsSummary(params = {}) {
    return this.get('/api/v3/brokerage/transaction_summary', {
      start_date: params.start_date,
      end_date: params.end_date,
      user_native_currency: params.currency || 'USD',
      product_type: 'SPOT'
    });
  }
  
  // WebSocket Feed (uses different auth)
  async subscribeToWebSocket(products, channels, onMessage, onError) {
    const WebSocket = require('ws');
    const ws = new WebSocket('wss://advanced-trade-ws.coinbase.com');
    
    ws.on('open', async () => {
      console.log('📡 Coinbase WebSocket connected');
      
      // Generate JWT for WebSocket
      const keyName = await this.keyManager.getKey('coinbase', 'COINBASE_KEY_NAME');
      const privateKey = await this.keyManager.getKey('coinbase', 'COINBASE_PRIVATE_KEY');
      
      const subscribeMessage = {
        type: 'subscribe',
        product_ids: products,
        channel: channels,
        jwt: this.generateJWT(
          { method: 'GET', url: '/ws' }, 
          keyName, 
          privateKey
        )
      };
      
      ws.send(JSON.stringify(subscribeMessage));
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        onMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });
    
    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    });
    
    ws.on('close', () => {
      console.log('📴 Coinbase WebSocket disconnected');
    });
    
    return ws;
  }
  
  // Helper Methods for compatibility
  async getProductTicker(productId) {
    const response = await this.getBestBidAsk(productId);
    const ticker = response.pricebooks?.[0];
    
    if (!ticker) {
      throw new Error(`No ticker data for ${productId}`);
    }
    
    return {
      price: ticker.bids?.[0]?.price || ticker.asks?.[0]?.price || '0',
      size: ticker.bids?.[0]?.size || ticker.asks?.[0]?.size || '0',
      bid: ticker.bids?.[0]?.price || '0',
      ask: ticker.asks?.[0]?.price || '0',
      time: ticker.time
    };
  }
  
  async getProductOrderBook(productId, level = 2) {
    const response = await this.get(`/api/v3/brokerage/product_book`, {
      product_id: productId,
      limit: level === 1 ? 1 : level === 2 ? 50 : 200
    });
    
    return {
      bids: response.pricebook?.bids || [],
      asks: response.pricebook?.asks || [],
      time: response.pricebook?.time
    };
  }
  
  async getProductTrades(productId, limit = 100) {
    const response = await this.getMarketTrades(productId, limit);
    
    return response.trades?.map(trade => ({
      time: trade.time,
      trade_id: trade.trade_id,
      price: trade.price,
      size: trade.size,
      side: trade.side
    })) || [];
  }
  
  async getProduct24HrStats(productId) {
    const end = new Date();
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
    
    const candles = await this.getProductCandles(
      productId,
      start.toISOString(),
      end.toISOString(),
      'ONE_DAY'
    );
    
    const candle = candles.candles?.[0];
    if (!candle) {
      throw new Error(`No 24hr stats for ${productId}`);
    }
    
    return {
      open: candle.open,
      high: candle.high,
      low: candle.low,
      last: candle.close,
      volume: candle.volume
    };
  }
  
  // Advanced Trading Indicators (same as before but with new data format)
  async getMovingAverage(productId, period = 20, granularity = 'ONE_HOUR') {
    const end = new Date();
    const start = new Date(end.getTime() - period * 60 * 60 * 1000);
    
    const response = await this.getProductCandles(
      productId,
      start.toISOString(),
      end.toISOString(),
      granularity
    );
    
    const candles = response.candles || [];
    if (candles.length < period) {
      throw new Error(`Insufficient data for ${period} period MA`);
    }
    
    const closes = candles.slice(0, period).map(c => parseFloat(c.close));
    const ma = closes.reduce((a, b) => a + b, 0) / period;
    
    return {
      productId,
      period,
      movingAverage: ma,
      currentPrice: parseFloat(candles[0].close),
      signal: parseFloat(candles[0].close) > ma ? 'bullish' : 'bearish'
    };
  }
  
  async getRSI(productId, period = 14, granularity = 'ONE_HOUR') {
    const end = new Date();
    const start = new Date(end.getTime() - (period + 10) * 60 * 60 * 1000);
    
    const response = await this.getProductCandles(
      productId,
      start.toISOString(),
      end.toISOString(),
      granularity
    );
    
    const candles = response.candles || [];
    if (candles.length < period + 1) {
      throw new Error(`Insufficient data for ${period} period RSI`);
    }
    
    let gains = 0;
    let losses = 0;
    
    for (let i = 0; i < period; i++) {
      const change = parseFloat(candles[i].close) - parseFloat(candles[i + 1].close);
      if (change > 0) {
        gains += change;
      } else {
        losses += Math.abs(change);
      }
    }
    
    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));
    
    return {
      productId,
      period,
      rsi,
      signal: rsi > 70 ? 'overbought' : rsi < 30 ? 'oversold' : 'neutral'
    };
  }
}

module.exports = CoinbaseAdvancedClient; 