const BaseAPIClient = require('../base/api-client');

class CoinDeskClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'CoinDesk',
      baseURL: 'https://api.coindesk.com/v1',
      timeout: 10000,
      retries: 3
    });
    
    this.keyManager = keyManager;
  }
  
  async getAuthHeaders(config) {
    const apiKey = await this.keyManager.getKey('coindesk', 'COINDESK_API_KEY');
    return {
      'Authorization': `Bearer ${apiKey}`
    };
  }
  
  // Price Data
  async getCurrentPrice(currency = 'USD') {
    const data = await this.get('/bpi/currentprice.json');
    return data.bpi[currency];
  }
  
  async getHistoricalPrice(start, end, currency = 'USD') {
    return this.get('/bpi/historical/close.json', {
      start,
      end,
      currency
    });
  }
  
  // News and Analysis
  async getLatestNews(category = 'markets', limit = 10) {
    return this.get('/news', {
      category,
      limit
    });
  }
  
  async getArticle(articleId) {
    return this.get(`/news/${articleId}`);
  }
  
  async searchNews(query, fromDate = null, toDate = null) {
    const params = { q: query };
    if (fromDate) params.from = fromDate;
    if (toDate) params.to = toDate;
    return this.get('/news/search', params);
  }
  
  // Market Data
  async getMarketCap(limit = 100) {
    return this.get('/marketcap', { limit });
  }
  
  async getCryptoDetails(symbol) {
    return this.get(`/crypto/${symbol}`);
  }
  
  // Indices
  async getCoinDeskIndex(index = 'XBX') {
    return this.get(`/indices/${index}`);
  }
  
  async getIndexHistory(index, start, end) {
    return this.get(`/indices/${index}/history`, {
      start,
      end
    });
  }
  
  // Analysis Tools
  async getTrendingTopics() {
    return this.get('/trending');
  }
  
  async getSentimentAnalysis(symbol = 'BTC') {
    return this.get(`/sentiment/${symbol}`);
  }
  
  // Helper Methods
  async getPriceChange(currency = 'USD', days = 7) {
    const end = new Date();
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
    
    const historicalData = await this.getHistoricalPrice(
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0],
      currency
    );
    
    const prices = Object.values(historicalData.bpi);
    if (prices.length < 2) return null;
    
    const oldPrice = prices[0];
    const currentPrice = prices[prices.length - 1];
    const change = currentPrice - oldPrice;
    const changePercent = (change / oldPrice) * 100;
    
    return {
      currency,
      period: `${days} days`,
      startPrice: oldPrice,
      currentPrice,
      change,
      changePercent,
      trend: change > 0 ? 'up' : 'down'
    };
  }
}

module.exports = CoinDeskClient; 