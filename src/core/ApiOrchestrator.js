// /src/core/ApiOrchestrator.js
import CircuitBreaker from 'opossum';
import { EventEmitter } from 'events';
import WebSocket from 'ws';
import Redis from 'ioredis';

class ApiOrchestrator extends EventEmitter {
  constructor() {
    super();
    this.apis = new Map();
    this.healthChecks = new Map();
    this.circuitBreakers = new Map();
    this.websockets = new Map();
    this.redis = new Redis(process.env.REDIS_URL);
    
    // Initialize all APIs
    this.initializeApis();
    
    // Start health monitoring
    this.startHealthMonitoring();
    
    // Setup global error handling
    this.setupGlobalErrorHandling();
  }

  initializeApis() {
    // Coinbase API
    this.registerApi('coinbase', {
      baseUrl: 'https://api.coinbase.com',
      wsUrl: 'wss://ws-feed.coinbase.com',
      auth: {
        type: 'ECDSA',
        keyId: process.env.COINBASE_ECDSA_PUBLIC_KEY,
        privateKey: process.env.COINBASE_ECDSA_PRIVATE_KEY
      },
      rateLimit: { requests: 10000, window: 3600000 },
      timeout: 10000,
      retries: 3,
      healthEndpoint: '/v2/time'
    });

    // TAAPI
    this.registerApi('taapi', {
      baseUrl: 'https://api.taapi.io',
      auth: {
        type: 'apiKey',
        secret: process.env.TAAPI_API_KEY
      },
      rateLimit: { requests: 100, window: 60000 },
      timeout: 15000,
      retries: 2,
      healthEndpoint: '/ping'
    });

    // TwitterAPI.io
    this.registerApi('twitterapi', {
      baseUrl: 'https://api.twitterapi.io',
      auth: {
        type: 'bearer',
        token: process.env.TWITTERAPI_API_KEY
      },
      rateLimit: { requests: 1000, window: 900000 },
      timeout: 10000,
      retries: 2,
      healthEndpoint: '/v1/status'
    });

    // ScrapingBee
    this.registerApi('scrapingbee', {
      baseUrl: 'https://app.scrapingbee.com/api/v1',
      auth: {
        type: 'apiKey',
        key: process.env.SCRAPINGBEE_API_KEY
      },
      rateLimit: { requests: 1000, window: 3600000 },
      timeout: 30000,
      retries: 2,
      healthEndpoint: '/ping'
    });

    // Grok (X AI)
    this.registerApi('grok', {
      baseUrl: 'https://api.x.ai/v1',
      auth: {
        type: 'bearer',
        token: process.env.XAI_API_KEY
      },
      rateLimit: { requests: 100, window: 60000 },
      timeout: 30000,
      retries: 2,
      healthEndpoint: '/models'
    });

    // Perplexity
    this.registerApi('perplexity', {
      baseUrl: 'https://api.perplexity.ai',
      auth: {
        type: 'bearer',
        token: process.env.PERPLEXITY_API_KEY
      },
      rateLimit: { requests: 1000, window: 3600000 },
      timeout: 30000,
      retries: 2,
      healthEndpoint: '/models'
    });

    // Anthropic (Claude)
    this.registerApi('anthropic', {
      baseUrl: 'https://api.anthropic.com',
      auth: {
        type: 'apiKey',
        key: process.env.ANTHROPIC_API_KEY
      },
      rateLimit: { requests: 1000, window: 60000 },
      timeout: 60000,
      retries: 2,
      healthEndpoint: '/v1/messages'
    });

    // CoinDesk
    this.registerApi('coindesk', {
      baseUrl: 'https://api.coindesk.com/v1',
      auth: {
        type: 'none'
      },
      rateLimit: { requests: 100, window: 60000 },
      timeout: 10000,
      retries: 2,
      healthEndpoint: '/articles'
    });
  }

  registerApi(name, config) {
    // Create circuit breaker for this API
    const breaker = new CircuitBreaker(
      this.makeRequest.bind(this, name),
      {
        timeout: config.timeout,
        errorThresholdPercentage: 50,
        resetTimeout: 30000,
        volumeThreshold: 10
      }
    );

    breaker.on('open', () => {
      console.error(`Circuit breaker OPEN for ${name}`);
      this.emit('api:circuit:open', { api: name });
      this.notifyOpsTeam(name, 'circuit_open');
    });

    breaker.on('halfOpen', () => {
      console.log(`Circuit breaker HALF-OPEN for ${name}`);
    });

    this.circuitBreakers.set(name, breaker);
    this.apis.set(name, config);
    
    // Initialize WebSocket if needed
    if (config.wsUrl) {
      this.initializeWebSocket(name, config);
    }
  }

  async makeRequest(apiName, method, path, data = null) {
    const api = this.apis.get(apiName);
    if (!api) throw new Error(`API ${apiName} not registered`);

    // Check health before making request
    const isHealthy = await this.checkApiHealth(apiName);
    if (!isHealthy) {
      throw new Error(`API ${apiName} is unhealthy`);
    }

    // Rate limiting check
    const canProceed = await this.checkRateLimit(apiName);
    if (!canProceed) {
      throw new Error(`Rate limit exceeded for ${apiName}`);
    }

    // Make the actual request with retry logic
    return await this.executeWithRetry(apiName, method, path, data);
  }

  async checkApiHealth(apiName) {
    const cached = await this.redis.get(`health:${apiName}`);
    if (cached) return cached === 'healthy';

    const api = this.apis.get(apiName);
    try {
      const response = await fetch(`${api.baseUrl}${api.healthEndpoint}`);
      const isHealthy = response.ok;
      
      // Cache health status for 30 seconds
      await this.redis.setex(`health:${apiName}`, 30, isHealthy ? 'healthy' : 'unhealthy');
      
      return isHealthy;
    } catch (error) {
      await this.redis.setex(`health:${apiName}`, 30, 'unhealthy');
      return false;
    }
  }

  async checkRateLimit(apiName) {
    const api = this.apis.get(apiName);
    const key = `ratelimit:${apiName}`;
    
    const current = await this.redis.incr(key);
    if (current === 1) {
      await this.redis.expire(key, Math.floor(api.rateLimit.window / 1000));
    }
    
    return current <= api.rateLimit.requests;
  }

  async executeWithRetry(apiName, method, path, data, attempt = 1) {
    const api = this.apis.get(apiName);
    
    try {
      const headers = this.buildAuthHeaders(apiName);
      const url = `${api.baseUrl}${path}`;
      
      const options = {
        method,
        headers,
        ...(data && { body: JSON.stringify(data) })
      };
      
      const response = await fetch(url, options);
      
      if (!response.ok && attempt < api.retries) {
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        return this.executeWithRetry(apiName, method, path, data, attempt + 1);
      }
      
      return await response.json();
    } catch (error) {
      if (attempt < api.retries) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        return this.executeWithRetry(apiName, method, path, data, attempt + 1);
      }
      throw error;
    }
  }

  buildAuthHeaders(apiName) {
    const api = this.apis.get(apiName);
    const headers = {
      'Content-Type': 'application/json'
    };
    
    switch (api.auth.type) {
      case 'bearer':
        headers['Authorization'] = `Bearer ${api.auth.token}`;
        break;
      case 'apiKey':
        headers['X-API-Key'] = api.auth.key;
        break;
      case 'ECDSA':
        // Implement ECDSA signing for Coinbase
        const timestamp = Date.now() / 1000;
        headers['CB-ACCESS-KEY'] = api.auth.keyId;
        headers['CB-ACCESS-TIMESTAMP'] = timestamp;
        headers['CB-ACCESS-SIGN'] = this.signRequest(api.auth.privateKey, timestamp, method, path);
        break;
    }
    
    return headers;
  }

  signRequest(privateKey, timestamp, method, path) {
    // Import from config/api-config.js
    const crypto = require('crypto');
    const message = timestamp + method.toUpperCase() + path;
    const signature = crypto.createHmac('sha256', privateKey)
      .update(message)
      .digest('hex');
    return signature;
  }

  startHealthMonitoring() {
    setInterval(() => {
      this.apis.forEach((config, name) => {
        this.checkApiHealth(name).then(isHealthy => {
          this.emit('health:check', { api: name, healthy: isHealthy });
          
          if (!isHealthy) {
            this.handleUnhealthyApi(name);
          }
        });
      });
    }, 15000); // Check every 15 seconds
  }

  handleUnhealthyApi(name) {
    console.error(`API ${name} is unhealthy`);
    
    // Implement fallback logic
    switch (name) {
      case 'coinbase':
        // Critical - trading will be affected
        this.emit('critical:api:down', { api: name });
        break;
      case 'taapi':
        // Use cached indicators or basic calculations
        this.emit('degraded:service', { api: name, impact: 'indicators' });
        break;
      default:
        this.emit('api:down', { api: name });
    }
  }

  // WebSocket management
  initializeWebSocket(name, config) {
    const ws = new WebSocket(config.wsUrl);
    
    ws.on('open', () => {
      console.log(`WebSocket connected for ${name}`);
      this.emit('ws:connected', { api: name });
      
      // Subscribe to necessary channels
      if (name === 'coinbase') {
        ws.send(JSON.stringify({
          type: 'subscribe',
          channels: ['ticker', 'level2', 'matches'],
          product_ids: ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD']
        }));
      }
    });

    ws.on('message', (data) => {
      this.emit('ws:message', { api: name, data: JSON.parse(data) });
    });

    ws.on('error', (error) => {
      console.error(`WebSocket error for ${name}:`, error);
      this.reconnectWebSocket(name, config);
    });

    ws.on('close', () => {
      console.log(`WebSocket closed for ${name}`);
      this.reconnectWebSocket(name, config);
    });

    this.websockets.set(name, ws);
  }

  reconnectWebSocket(name, config, attempt = 1) {
    if (attempt > 5) {
      console.error(`Failed to reconnect WebSocket for ${name} after 5 attempts`);
      this.notifyOpsTeam(name, 'websocket_failure');
      return;
    }

    setTimeout(() => {
      console.log(`Attempting to reconnect WebSocket for ${name} (attempt ${attempt})`);
      this.initializeWebSocket(name, config);
    }, Math.min(attempt * 1000, 10000));
  }

  notifyOpsTeam(apiName, issue) {
    // Log critical issues
    console.error(`CRITICAL: ${apiName} - ${issue}`);
    
    // Here you would implement actual notifications
    // e.g., send email, SMS, Slack message, etc.
  }

  setupGlobalErrorHandling() {
    process.on('unhandledRejection', (error) => {
      console.error('Unhandled rejection in ApiOrchestrator:', error);
      this.emit('global:error', { error });
    });
  }

  // Get all API statuses
  async getAllApiStatuses() {
    const statuses = {};
    
    for (const [name, config] of this.apis) {
      statuses[name] = await this.checkApiHealth(name);
    }
    
    return statuses;
  }

  // Global instance
  static instance = null;
  static getInstance() {
    if (!ApiOrchestrator.instance) {
      ApiOrchestrator.instance = new ApiOrchestrator();
    }
    return ApiOrchestrator.instance;
  }
}

export default ApiOrchestrator; 