const TwitterAPIioClient = require('../../src/api/integrations/twitter-client');
const SecureAPIKeyManager = require('../../src/utils/security/api-key-manager');

describe('TwitterAPI.io Integration Tests', () => {
  let client;
  let keyManager;
  
  beforeAll(async () => {
    keyManager = new SecureAPIKeyManager();
    await keyManager.initializeFromEnv();
    client = new TwitterAPIioClient(keyManager);
  });
  
  test('should authenticate with TwitterAPI.io', async () => {
    // Test with a known public account
    const user = await client.getUserByUsername('twitter');
    expect(user).toBeDefined();
    expect(user.data).toBeDefined();
    expect(user.data.username).toBe('twitter');
  });
  
  test('should fetch user tweets', async () => {
    const tweets = await client.getUserTweets('elonmusk', 5);
    expect(Array.isArray(tweets)).toBe(true);
    expect(tweets.length).toBeLessThanOrEqual(5);
    
    if (tweets.length > 0) {
      expect(tweets[0]).toHaveProperty('id');
      expect(tweets[0]).toHaveProperty('text');
      expect(tweets[0]).toHaveProperty('created_at');
      expect(tweets[0]).toHaveProperty('likes');
      expect(tweets[0]).toHaveProperty('retweets');
    }
  });
  
  test('should monitor multiple crypto influencers', async () => {
    const accounts = ['VitalikButerin', 'aantonop'];
    const results = await client.monitorAccounts(accounts, 2);
    
    expect(results).toBeDefined();
    accounts.forEach(account => {
      expect(results[account]).toBeDefined();
      expect(results[account]).toHaveProperty('success');
      expect(results[account]).toHaveProperty('lastChecked');
    });
  });
  
  test('should search crypto tweets', async () => {
    const tweets = await client.searchCryptoTweets('bitcoin', 10);
    expect(Array.isArray(tweets)).toBe(true);
    expect(tweets.length).toBeGreaterThan(0);
  });
  
  test('should analyze sentiment', async () => {
    const mockTweets = [
      { text: 'Bitcoin to the moon! Bullish!' },
      { text: 'Crypto market crash incoming' },
      { text: 'Just bought more ETH' }
    ];
    
    const sentiment = await client.analyzeCryptoSentiment(mockTweets);
    expect(sentiment).toHaveProperty('bullish');
    expect(sentiment).toHaveProperty('bearish');
    expect(sentiment).toHaveProperty('neutral');
    expect(sentiment).toHaveProperty('signal');
  });
}); 