const UnifiedAPIManager = require('../../src/api/api-manager');
const SecureAPIKeyManager = require('../../src/utils/security/api-key-manager');

describe('API Integration Tests', () => {
  let apiManager;
  let keyManager;
  
  beforeAll(async () => {
    // Initialize managers
    keyManager = new SecureAPIKeyManager();
    await keyManager.initializeFromEnv();
    
    apiManager = new UnifiedAPIManager();
    await apiManager.initialize();
  });
  
  afterAll(async () => {
    await apiManager.shutdown();
  });
  
  describe('Coinbase API', () => {
    test('should authenticate successfully', async () => {
      const client = apiManager.getClient('coinbase');
      const accounts = await client.getAccounts(1);
      
      expect(accounts).toBeDefined();
      expect(accounts.accounts).toBeDefined();
      expect(Array.isArray(accounts.accounts)).toBe(true);
    });
    
    test('should fetch products', async () => {
      const client = apiManager.getClient('coinbase');
      const result = await client.getProducts(10);
      
      expect(result).toBeDefined();
      expect(result.products).toBeDefined();
      expect(Array.isArray(result.products)).toBe(true);
      if (result.products.length > 0) {
        expect(result.products[0]).toHaveProperty('product_id');
        expect(result.products[0]).toHaveProperty('base_currency_id');
        expect(result.products[0]).toHaveProperty('quote_currency_id');
      }
    });
    
    test('should fetch BTC-USD ticker', async () => {
      const client = apiManager.getClient('coinbase');
      const ticker = await client.getProductTicker('BTC-USD');
      
      expect(ticker).toBeDefined();
      expect(ticker.price).toBeDefined();
      expect(parseFloat(ticker.price)).toBeGreaterThan(0);
    });
    
    test('should handle rate limiting gracefully', async () => {
      const client = apiManager.getClient('coinbase');
      const promises = [];
      
      // Make multiple requests
      for (let i = 0; i < 5; i++) {
        promises.push(client.getProductTicker('BTC-USD'));
      }
      
      const results = await Promise.allSettled(promises);
      const successful = results.filter(r => r.status === 'fulfilled');
      
      expect(successful.length).toBeGreaterThan(0);
    });
  });
  
  describe('CoinDesk API', () => {
    test('should fetch current BTC price', async () => {
      const client = apiManager.getClient('coindesk');
      const price = await client.getCurrentPrice('USD');
      
      expect(price).toBeDefined();
      expect(price.rate_float).toBeDefined();
      expect(price.rate_float).toBeGreaterThan(0);
    });
    
    test('should fetch historical prices', async () => {
      const client = apiManager.getClient('coindesk');
      const end = new Date();
      const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
      
      const historical = await client.getHistoricalPrice(
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
      );
      
      expect(historical).toBeDefined();
      expect(historical.bpi).toBeDefined();
      expect(Object.keys(historical.bpi).length).toBeGreaterThan(0);
    });
  });
  
  describe('TAAPI Technical Indicators', () => {
    test('should calculate RSI', async () => {
      const client = apiManager.getClient('taapi');
      const rsi = await client.getRSI('binance', 'BTC/USDT', '1h');
      
      expect(rsi).toBeDefined();
      expect(rsi.value).toBeDefined();
      expect(rsi.value).toBeGreaterThanOrEqual(0);
      expect(rsi.value).toBeLessThanOrEqual(100);
    });
    
    test('should fetch multiple indicators', async () => {
      const client = apiManager.getClient('taapi');
      const indicators = await client.getMultipleIndicators('binance', 'BTC/USDT', '1h');
      
      expect(indicators).toBeDefined();
      expect(Object.keys(indicators).length).toBeGreaterThan(0);
    });
    
    test('should generate trading signal', async () => {
      const client = apiManager.getClient('taapi');
      const signal = await client.getTradingSignal('binance', 'BTC/USDT', '1h');
      
      expect(signal).toBeDefined();
      expect(signal.signal).toMatch(/BUY|SELL|HOLD/);
      expect(signal.confidence).toBeDefined();
      expect(signal.indicators).toBeDefined();
    });
  });
  
  describe('ScrapingBee Web Scraping', () => {
    test('should scrape crypto news', async () => {
      const client = apiManager.getClient('scrapingbee');
      const news = await client.scrapeCryptoNews(['coindesk']);
      
      expect(Array.isArray(news)).toBe(true);
      expect(news.length).toBeGreaterThan(0);
      expect(news[0]).toHaveProperty('title');
      expect(news[0]).toHaveProperty('link');
      expect(news[0]).toHaveProperty('source');
    });
    
    test('should analyze crypto sentiment', async () => {
      const client = apiManager.getClient('scrapingbee');
      const sentiment = await client.analyzeCryptoSentiment('bitcoin');
      
      expect(sentiment).toBeDefined();
      expect(sentiment.sentiment).toBeDefined();
      expect(sentiment.score).toBeDefined();
      expect(sentiment.recommendation).toMatch(/BULLISH|BEARISH|NEUTRAL/);
    });
  });
  
  describe('Unified API Manager', () => {
    test('should aggregate market data from multiple sources', async () => {
      const marketData = await apiManager.getAggregatedMarketData('BTC/USD');
      
      expect(marketData).toBeDefined();
      expect(marketData.symbol).toBe('BTC/USD');
      expect(marketData.prices).toBeDefined();
      expect(marketData.indicators).toBeDefined();
      expect(marketData.averagePrice).toBeGreaterThan(0);
    });
    
    test('should generate composite trading signals', async () => {
      const signal = await apiManager.generateTradingSignal('BTC/USD');
      
      expect(signal).toBeDefined();
      expect(signal.symbol).toBe('BTC/USD');
      expect(signal.signal).toMatch(/STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL/);
      expect(signal.confidence).toBeDefined();
      expect(signal.recommendation).toBeDefined();
    });
    
    test('should handle API failures gracefully', async () => {
      // Simulate API failure by using invalid credentials
      const testManager = new UnifiedAPIManager();
      
      // Don't initialize to simulate failure
      expect(() => testManager.getClient('coinbase')).toThrow();
    });
  });
  
  describe('Health Monitoring', () => {
    test('should report API health status', async () => {
      const status = apiManager.getStatus();
      
      expect(status).toBeDefined();
      expect(status.initialized).toBe(true);
      expect(status.health).toBeDefined();
      expect(status.apis).toBeDefined();
      expect(Array.isArray(status.apis)).toBe(true);
    });
    
    test('should detect degraded APIs', async () => {
      // This would require mocking API responses
      // For now, just verify the structure
      const health = apiManager.healthMonitor.getHealthSummary();
      
      expect(health).toBeDefined();
      expect(health.totalAPIs).toBeGreaterThan(0);
      expect(health).toHaveProperty('healthy');
      expect(health).toHaveProperty('degraded');
      expect(health).toHaveProperty('critical');
    });
  });
}); 