const BaseAPIClient = require('../base/api-client');

class AnthropicClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'Anthropic',
      baseURL: 'https://api.anthropic.com/v1',
      timeout: 60000,
      retries: 2
    });
    
    this.keyManager = keyManager;
  }
  
  async getAuthHeaders(config) {
    const apiKey = await this.keyManager.getKey('anthropic', 'ANTHROPIC_API_KEY');
    return {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json'
    };
  }
  
  async createMessage(messages, model = 'claude-3-sonnet-20240229', maxTokens = 1024) {
    return this.post('/messages', {
      model,
      max_tokens: maxTokens,
      messages
    });
  }
  
  async analyzeMarket(data) {
    const messages = [
      {
        role: 'user',
        content: `Analyze the following cryptocurrency market data and provide insights: ${JSON.stringify(data)}`
      }
    ];
    
    return this.createMessage(messages);
  }
}

module.exports = AnthropicClient; 