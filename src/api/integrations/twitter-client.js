const BaseAPIClient = require('../base/api-client');

class TwitterAPIioClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'TwitterAPIio',
      baseURL: 'https://api.twitterapi.io/v2',
      timeout: 30000,
      retries: 3
    });
    
    this.keyManager = keyManager;
  }
  
  async getAuthHeaders(config) {
    const apiKey = await this.keyManager.getKey('twitterapiio', 'TWITTERAPIIO_API_KEY');
    return {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  // Get user details by username
  async getUserByUsername(username) {
    return this.get(`/users/by/username/${username}`);
  }
  
  // Get user details by ID
  async getUserById(userId) {
    return this.get(`/users/${userId}`);
  }
  
  // Get user tweets
  async getUserTweets(username, count = 10) {
    try {
      // First get user ID from username
      const userResponse = await this.getUserByUsername(username);
      const userId = userResponse.data?.id;
      
      if (!userId) {
        throw new Error(`User not found: ${username}`);
      }
      
      // Then get tweets
      const params = {
        max_results: count,
        'tweet.fields': 'created_at,public_metrics,author_id,conversation_id,entities',
        'user.fields': 'name,username,profile_image_url,verified',
        'expansions': 'author_id,referenced_tweets.id'
      };
      
      const tweets = await this.get(`/users/${userId}/tweets`, params);
      
      return this.formatTweets(tweets.data || [], username);
    } catch (error) {
      console.error(`Error fetching tweets for @${username}:`, error);
      throw error;
    }
  }
  
  // Search tweets
  async searchTweets(query, count = 10) {
    const params = {
      query,
      max_results: count,
      'tweet.fields': 'created_at,public_metrics,author_id',
      'user.fields': 'name,username,profile_image_url',
      'expansions': 'author_id'
    };
    
    const results = await this.get('/tweets/search/recent', params);
    return this.formatTweets(results.data || []);
  }
  
  // Monitor multiple accounts
  async monitorAccounts(usernames, tweetsPerUser = 5) {
    const monitoringResults = {};
    
    for (const username of usernames) {
      try {
        const tweets = await this.getUserTweets(username, tweetsPerUser);
        monitoringResults[username] = {
          success: true,
          tweets,
          lastChecked: new Date().toISOString()
        };
      } catch (error) {
        monitoringResults[username] = {
          success: false,
          error: error.message,
          tweets: [],
          lastChecked: new Date().toISOString()
        };
      }
    }
    
    return monitoringResults;
  }
  
  // Get tweet by ID
  async getTweet(tweetId) {
    const params = {
      'tweet.fields': 'created_at,public_metrics,author_id,conversation_id,entities',
      'user.fields': 'name,username,profile_image_url',
      'expansions': 'author_id'
    };
    
    return this.get(`/tweets/${tweetId}`, params);
  }
  
  // Get tweet engagement metrics
  async getTweetMetrics(tweetId) {
    const tweet = await this.getTweet(tweetId);
    return {
      tweetId,
      metrics: tweet.data?.public_metrics || {},
      engagement_rate: this.calculateEngagementRate(tweet.data?.public_metrics)
    };
  }
  
  // Format tweets for consistent output
  formatTweets(tweets, username = null) {
    return tweets.map(tweet => ({
      id: tweet.id,
      text: tweet.text,
      created_at: tweet.created_at,
      author: username || tweet.author_id,
      likes: tweet.public_metrics?.like_count || 0,
      retweets: tweet.public_metrics?.retweet_count || 0,
      replies: tweet.public_metrics?.reply_count || 0,
      quotes: tweet.public_metrics?.quote_count || 0,
      impressions: tweet.public_metrics?.impression_count || 0,
      url: `https://twitter.com/${username || 'i'}/status/${tweet.id}`,
      entities: tweet.entities || {}
    }));
  }
  
  // Calculate engagement rate
  calculateEngagementRate(metrics) {
    if (!metrics || !metrics.impression_count) return 0;
    
    const engagements = (metrics.like_count || 0) + 
                      (metrics.retweet_count || 0) + 
                      (metrics.reply_count || 0) + 
                      (metrics.quote_count || 0);
    
    return ((engagements / metrics.impression_count) * 100).toFixed(2);
  }
  
  // Crypto-specific monitoring
  async monitorCryptoInfluencers() {
    const cryptoInfluencers = [
      'elonmusk',
      'VitalikButerin',
      'aantonop',
      'APompliano',
      'CathieDWood',
      'saylor',
      'cz_binance',
      'brian_armstrong',
      'SatoshiLite',
      'rogerkver'
    ];
    
    return this.monitorAccounts(cryptoInfluencers, 3);
  }
  
  // Search for crypto-related tweets
  async searchCryptoTweets(cryptocurrency = 'bitcoin', count = 20) {
    const queries = {
      bitcoin: '(bitcoin OR btc) -is:retweet lang:en',
      ethereum: '(ethereum OR eth) -is:retweet lang:en',
      general: '(crypto OR cryptocurrency OR blockchain) -is:retweet lang:en'
    };
    
    const query = queries[cryptocurrency.toLowerCase()] || queries.general;
    return this.searchTweets(query, count);
  }
  
  // Analyze tweet sentiment for crypto mentions
  async analyzeCryptoSentiment(tweets) {
    const sentimentKeywords = {
      bullish: ['moon', 'bullish', 'buy', 'long', 'pump', 'rally', 'breakout', 'ath', 'hodl'],
      bearish: ['bearish', 'sell', 'short', 'dump', 'crash', 'correction', 'bear', 'down']
    };
    
    let bullishCount = 0;
    let bearishCount = 0;
    
    tweets.forEach(tweet => {
      const text = tweet.text.toLowerCase();
      
      const bullishScore = sentimentKeywords.bullish.filter(word => 
        text.includes(word)
      ).length;
      
      const bearishScore = sentimentKeywords.bearish.filter(word => 
        text.includes(word)
      ).length;
      
      if (bullishScore > bearishScore) bullishCount++;
      else if (bearishScore > bullishScore) bearishCount++;
    });
    
    const total = tweets.length;
    return {
      bullish: (bullishCount / total * 100).toFixed(2),
      bearish: (bearishCount / total * 100).toFixed(2),
      neutral: ((total - bullishCount - bearishCount) / total * 100).toFixed(2),
      signal: bullishCount > bearishCount ? 'BULLISH' : 
             bearishCount > bullishCount ? 'BEARISH' : 'NEUTRAL'
    };
  }
}

module.exports = TwitterAPIioClient; 