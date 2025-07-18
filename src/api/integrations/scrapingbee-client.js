const BaseAPIClient = require('../base/api-client');
const cheerio = require('cheerio');

class ScrapingBeeClient extends BaseAPIClient {
  constructor(keyManager) {
    super({
      name: 'ScrapingBee',
      baseURL: 'https://app.scrapingbee.com/api/v1',
      timeout: 60000,
      retries: 2
    });
    
    this.keyManager = keyManager;
  }
  
  async scrape(url, options = {}) {
    const apiKey = await this.keyManager.getKey('scrapingbee', 'SCRAPINGBEE_API_KEY');
    
    const params = {
      api_key: apiKey,
      url: url,
      render_js: options.renderJs || false,
      premium_proxy: options.premiumProxy || false,
      country_code: options.countryCode || '',
      wait: options.wait || 0,
      wait_for: options.waitFor || '',
      block_resources: options.blockResources || false,
      json_response: true,
      ...options.additionalParams
    };
    
    const response = await this.get('/', params);
    return {
      html: response.body,
      statusCode: response.statusCode,
      headers: response.headers,
      cost: response.cost
    };
  }
  
  // Google Search
  async googleSearch(query, options = {}) {
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    const result = await this.scrape(searchUrl, {
      renderJs: true,
      premiumProxy: true,
      ...options
    });
    
    const $ = cheerio.load(result.html);
    const searchResults = [];
    
    // Parse organic results
    $('.g').each((i, element) => {
      const title = $(element).find('h3').text();
      const link = $(element).find('a').attr('href');
      const snippet = $(element).find('.VwiC3b').text();
      
      if (title && link) {
        searchResults.push({
          position: i + 1,
          title,
          link,
          snippet
        });
      }
    });
    
    // Parse news results
    const newsResults = [];
    $('g-card').each((i, element) => {
      const title = $(element).find('.mCBkyc').text();
      const source = $(element).find('.CEMjEf span').text();
      const time = $(element).find('.OSrXXb span').text();
      const link = $(element).find('a').attr('href');
      
      if (title && link) {
        newsResults.push({
          title,
          source,
          time,
          link
        });
      }
    });
    
    return {
      query,
      organicResults: searchResults,
      newsResults,
      totalResults: searchResults.length + newsResults.length
    };
  }
  
  // Crypto News Scraping
  async scrapeCryptoNews(sources = ['coindesk', 'cointelegraph', 'decrypt']) {
    const allNews = [];
    
    const scrapers = {
      coindesk: async () => {
        const result = await this.scrape('https://www.coindesk.com/markets/', {
          renderJs: true
        });
        
        const $ = cheerio.load(result.html);
        const articles = [];
        
        $('article').each((i, element) => {
          const title = $(element).find('h2, h3').first().text().trim();
          const link = $(element).find('a').first().attr('href');
          const time = $(element).find('time').attr('datetime');
          const summary = $(element).find('p').first().text().trim();
          
          if (title && link) {
            articles.push({
              source: 'CoinDesk',
              title,
              link: link.startsWith('http') ? link : `https://www.coindesk.com${link}`,
              publishedAt: time,
              summary
            });
          }
        });
        
        return articles;
      },
      
      cointelegraph: async () => {
        const result = await this.scrape('https://cointelegraph.com/tags/markets', {
          renderJs: true
        });
        
        const $ = cheerio.load(result.html);
        const articles = [];
        
        $('.post-card').each((i, element) => {
          const title = $(element).find('.post-card__title').text().trim();
          const link = $(element).find('a').attr('href');
          const time = $(element).find('time').attr('datetime');
          const summary = $(element).find('.post-card__text').text().trim();
          
          if (title && link) {
            articles.push({
              source: 'Cointelegraph',
              title,
              link: `https://cointelegraph.com${link}`,
              publishedAt: time,
              summary
            });
          }
        });
        
        return articles;
      },
      
      decrypt: async () => {
        const result = await this.scrape('https://decrypt.co/news', {
          renderJs: true
        });
        
        const $ = cheerio.load(result.html);
        const articles = [];
        
        $('article').each((i, element) => {
          const title = $(element).find('h2, h3').first().text().trim();
          const link = $(element).find('a').first().attr('href');
          const time = $(element).find('time').text();
          const summary = $(element).find('p').first().text().trim();
          
          if (title && link) {
            articles.push({
              source: 'Decrypt',
              title,
              link: link.startsWith('http') ? link : `https://decrypt.co${link}`,
              publishedAt: time,
              summary
            });
          }
        });
        
        return articles;
      }
    };
    
    // Scrape from selected sources
    for (const source of sources) {
      if (scrapers[source]) {
        try {
          const articles = await scrapers[source]();
          allNews.push(...articles);
        } catch (error) {
          console.error(`Failed to scrape ${source}:`, error.message);
        }
      }
    }
    
    // Sort by time (newest first)
    allNews.sort((a, b) => {
      const timeA = new Date(a.publishedAt || 0);
      const timeB = new Date(b.publishedAt || 0);
      return timeB - timeA;
    });
    
    return allNews;
  }
  
  // Reddit Scraping
  async scrapeReddit(subreddit, sort = 'hot', limit = 25) {
    const url = `https://old.reddit.com/r/${subreddit}/${sort}/`;
    const result = await this.scrape(url, {
      renderJs: false
    });
    
    const $ = cheerio.load(result.html);
    const posts = [];
    
    $('#siteTable .thing').each((i, element) => {
      if (i >= limit) return false;
      
      const title = $(element).find('a.title').text();
      const link = $(element).find('a.title').attr('href');
      const score = $(element).find('.score.unvoted').text();
      const author = $(element).find('.author').text();
      const comments = $(element).find('.comments').text();
      const time = $(element).find('time').attr('datetime');
      
      const post = {
        title,
        link: link.startsWith('http') ? link : `https://reddit.com${link}`,
        score: score === '•' ? 0 : parseInt(score) || 0,
        author,
        commentCount: parseInt(comments) || 0,
        publishedAt: time,
        subreddit
      };
      
      // Check if it's a text post
      const selfText = $(element).find('.expando .usertext-body').text();
      if (selfText) {
        post.selfText = selfText.trim();
      }
      
      posts.push(post);
    });
    
    return {
      subreddit,
      sort,
      posts,
      count: posts.length
    };
  }
  
  // Twitter/X Monitoring Helper
  async searchTwitter(query, options = {}) {
    // Note: Direct Twitter scraping is complex due to their anti-bot measures
    // This is a simplified version that searches for tweets via Google
    const searchQuery = `site:twitter.com ${query}`;
    const results = await this.googleSearch(searchQuery, options);
    
    return {
      query,
      tweets: results.organicResults.filter(r => 
        r.link.includes('twitter.com/') || r.link.includes('x.com/')
      )
    };
  }
  
  // Market Sentiment Analysis
  async analyzeCryptoSentiment(cryptocurrency = 'bitcoin') {
    const sources = {
      reddit: await this.scrapeReddit(`${cryptocurrency}`, 'hot', 10),
      news: await this.googleSearch(`${cryptocurrency} news today`, { 
        additionalParams: { num: 10 }
      })
    };
    
    // Simple sentiment scoring based on titles
    const sentimentKeywords = {
      positive: ['bullish', 'surge', 'rally', 'gain', 'rise', 'up', 'high', 
                'breakthrough', 'adoption', 'milestone'],
      negative: ['bearish', 'crash', 'drop', 'fall', 'down', 'low', 
                'concern', 'warning', 'risk', 'hack']
    };
    
    let positiveCount = 0;
    let negativeCount = 0;
    let neutralCount = 0;
    
    // Analyze Reddit posts
    sources.reddit.posts.forEach(post => {
      const text = (post.title + ' ' + (post.selfText || '')).toLowerCase();
      let hasPositive = false;
      let hasNegative = false;
      
      sentimentKeywords.positive.forEach(word => {
        if (text.includes(word)) hasPositive = true;
      });
      
      sentimentKeywords.negative.forEach(word => {
        if (text.includes(word)) hasNegative = true;
      });
      
      if (hasPositive && !hasNegative) positiveCount++;
      else if (hasNegative && !hasPositive) negativeCount++;
      else neutralCount++;
    });
    
    // Analyze news
    sources.news.organicResults.forEach(result => {
      const text = (result.title + ' ' + result.snippet).toLowerCase();
      let hasPositive = false;
      let hasNegative = false;
      
      sentimentKeywords.positive.forEach(word => {
        if (text.includes(word)) hasPositive = true;
      });
      
      sentimentKeywords.negative.forEach(word => {
        if (text.includes(word)) hasNegative = true;
      });
      
      if (hasPositive && !hasNegative) positiveCount++;
      else if (hasNegative && !hasPositive) negativeCount++;
      else neutralCount++;
    });
    
    const total = positiveCount + negativeCount + neutralCount;
    
    return {
      cryptocurrency,
      timestamp: new Date().toISOString(),
      sentiment: {
        positive: (positiveCount / total * 100).toFixed(2) + '%',
        negative: (negativeCount / total * 100).toFixed(2) + '%',
        neutral: (neutralCount / total * 100).toFixed(2) + '%'
      },
      score: ((positiveCount - negativeCount) / total * 100).toFixed(2),
      sources: {
        reddit: sources.reddit.posts.length,
        news: sources.news.organicResults.length
      },
      recommendation: positiveCount > negativeCount ? 'BULLISH' : 
                     negativeCount > positiveCount ? 'BEARISH' : 'NEUTRAL'
    };
  }
}

module.exports = ScrapingBeeClient; 