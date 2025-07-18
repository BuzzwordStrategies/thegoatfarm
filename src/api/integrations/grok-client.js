const BaseAPIClient = require('../base/api-client');

class GrokClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'Grok',
      baseURL: 'https://api.x.ai/v1',
      timeout: 30000,
      retries: 2
    });
    
    this.keyManager = keyManager;
  }
  
  async getAuthHeaders(config) {
    const apiKey = await this.keyManager.getKey('grok', 'GROK_API_KEY');
    return {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  async chat(messages, model = 'grok-1') {
    return this.post('/chat/completions', {
      model,
      messages
    });
  }
  
  async analyzeTrends(topic) {
    const messages = [
      {
        role: 'system',
        content: 'You are an AI assistant analyzing cryptocurrency trends and social media sentiment.'
      },
      {
        role: 'user',
        content: `Analyze current trends and sentiment for: ${topic}`
      }
    ];
    
    return this.chat(messages);
  }
}

module.exports = GrokClient; 