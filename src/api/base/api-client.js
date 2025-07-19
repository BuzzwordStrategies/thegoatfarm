const axios = require('axios');
const axiosRetry = require('axios-retry').default || require('axios-retry');
const CircuitBreaker = require('opossum');
const { performance } = require('perf_hooks');

class BaseAPIClient {
  constructor(config) {
    this.config = {
      name: config.name,
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      retries: config.retries || 3,
      retryDelay: config.retryDelay || 1000,
      circuitBreakerOptions: {
        timeout: config.circuitBreakerTimeout || 30000,
        errorThresholdPercentage: config.errorThresholdPercentage || 50,
        resetTimeout: config.resetTimeout || 30000,
        ...config.circuitBreakerOptions
      }
    };
    
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      totalResponseTime: 0,
      errors: []
    };
    
    this.setupAxiosInstance();
    this.setupCircuitBreaker();
  }
  
  setupAxiosInstance() {
    this.axios = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'User-Agent': 'CryptoTradingBot/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    // Configure retry logic
    axiosRetry(this.axios, {
      retries: this.config.retries,
      retryDelay: (retryCount) => {
        return retryCount * this.config.retryDelay;
      },
      retryCondition: (error) => {
        return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
               (error.response && error.response.status >= 500);
      },
      onRetry: (retryCount, error, requestConfig) => {
        console.log(`🔄 Retrying ${this.config.name} request (attempt ${retryCount}): ${error.message}`);
      }
    });
    
    // Request interceptor for authentication
    this.axios.interceptors.request.use(
      async (config) => {
        // Add authentication headers
        const authHeaders = await this.getAuthHeaders(config);
        config.headers = { ...config.headers, ...authHeaders };
        
        // Add request timestamp
        config.metadata = { startTime: performance.now() };
        
        // Log request
        if (process.env.DEBUG === 'true') {
          console.log(`📤 ${this.config.name} Request:`, {
            method: config.method,
            url: config.url,
            headers: this.sanitizeHeaders(config.headers)
          });
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    
    // Response interceptor for metrics and error handling
    this.axios.interceptors.response.use(
      (response) => {
        // Calculate response time
        const responseTime = performance.now() - response.config.metadata.startTime;
        
        // Update metrics
        this.metrics.totalRequests++;
        this.metrics.successfulRequests++;
        this.metrics.totalResponseTime += responseTime;
        
        // Log response
        if (process.env.DEBUG === 'true') {
          console.log(`📥 ${this.config.name} Response:`, {
            status: response.status,
            responseTime: `${responseTime.toFixed(2)}ms`,
            dataSize: JSON.stringify(response.data).length
          });
        }
        
        return response;
      },
      (error) => {
        // Update metrics
        this.metrics.totalRequests++;
        this.metrics.failedRequests++;
        
        // Log error details
        const errorDetails = {
          timestamp: new Date().toISOString(),
          message: error.message,
          code: error.code,
          status: error.response?.status,
          data: error.response?.data
        };
        
        this.metrics.errors.push(errorDetails);
        
        // Keep only last 100 errors
        if (this.metrics.errors.length > 100) {
          this.metrics.errors = this.metrics.errors.slice(-100);
        }
        
        console.error(`❌ ${this.config.name} Error:`, errorDetails);
        
        // Transform error for better handling
        const enhancedError = new Error(error.message);
        enhancedError.code = error.code;
        enhancedError.status = error.response?.status;
        enhancedError.data = error.response?.data;
        enhancedError.api = this.config.name;
        
        return Promise.reject(enhancedError);
      }
    );
  }
  
  setupCircuitBreaker() {
    const breakerFunction = async (requestConfig) => {
      return await this.axios.request(requestConfig);
    };
    
    this.circuitBreaker = new CircuitBreaker(
      breakerFunction,
      this.config.circuitBreakerOptions
    );
    
    // Circuit breaker events
    this.circuitBreaker.on('open', () => {
      console.error(`🚨 Circuit breaker OPEN for ${this.config.name}`);
    });
    
    this.circuitBreaker.on('halfOpen', () => {
      console.warn(`⚡ Circuit breaker HALF-OPEN for ${this.config.name}`);
    });
    
    this.circuitBreaker.on('close', () => {
      console.log(`✅ Circuit breaker CLOSED for ${this.config.name}`);
    });
  }
  
  async request(config) {
    try {
      const response = await this.circuitBreaker.fire(config);
      return response.data;
    } catch (error) {
      if (error.name === 'OpenCircuitError') {
        console.error(`🚫 ${this.config.name} circuit is open. Service temporarily unavailable.`);
      }
      throw error;
    }
  }
  
  async get(endpoint, params = {}) {
    return this.request({
      method: 'GET',
      url: endpoint,
      params
    });
  }
  
  async post(endpoint, data = {}) {
    return this.request({
      method: 'POST',
      url: endpoint,
      data
    });
  }
  
  async put(endpoint, data = {}) {
    return this.request({
      method: 'PUT',
      url: endpoint,
      data
    });
  }
  
  async delete(endpoint) {
    return this.request({
      method: 'DELETE',
      url: endpoint
    });
  }
  
  // Override in subclasses to provide API-specific auth headers
  async getAuthHeaders(config) {
    return {};
  }
  
  sanitizeHeaders(headers) {
    const sanitized = { ...headers };
    const sensitiveKeys = ['authorization', 'api-key', 'x-api-key', 'secret'];
    
    for (const key of Object.keys(sanitized)) {
      if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
        sanitized[key] = '[REDACTED]';
      }
    }
    
    return sanitized;
  }
  
  getMetrics() {
    const avgResponseTime = this.metrics.successfulRequests > 0
      ? this.metrics.totalResponseTime / this.metrics.successfulRequests
      : 0;
    
    return {
      ...this.metrics,
      averageResponseTime: avgResponseTime,
      successRate: this.metrics.totalRequests > 0
        ? (this.metrics.successfulRequests / this.metrics.totalRequests) * 100
        : 0,
      circuitBreakerState: {
        state: this.circuitBreaker.opened ? 'open' : (this.circuitBreaker.halfOpen ? 'half-open' : 'closed'),
        enabled: this.circuitBreaker.enabled,
        pendingClose: this.circuitBreaker.pendingClose
      }
    };
  }
  
  resetMetrics() {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      totalResponseTime: 0,
      errors: []
    };
  }
}

module.exports = BaseAPIClient;
