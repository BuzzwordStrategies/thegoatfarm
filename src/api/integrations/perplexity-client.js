const BaseAPIClient = require('../base/api-client');

class PerplexityClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'Perplexity',
      baseURL: 'https://api.perplexity.ai',
      timeout: 30000,
      retries: 2
    });
    
    this.keyManager = keyManager;
  }
  
  async getAuthHeaders(config) {
    const apiKey = await this.keyManager.getKey('perplexity', 'PERPLEXITY_API_KEY');
    return {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  async chat(messages, model = 'llama-3-sonar-small-32k-online') {
    return this.post('/chat/completions', {
      model,
      messages
    });
  }
  
  async analyzeCrypto(query) {
    const messages = [
      {
        role: 'system',
        content: 'You are a cryptocurrency market analyst. Provide concise, factual analysis.'
      },
      {
        role: 'user',
        content: query
      }
    ];
    
    return this.chat(messages);
  }
}

module.exports = PerplexityClient; 