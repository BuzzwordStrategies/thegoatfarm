const dotenv = require('dotenv');
dotenv.config();

// API Clients
const CoinbaseClient = require('./api/integrations/coinbase-client');
const TaapiClient = require('./api/integrations/taapi-client');
const TwitterClient = require('./api/integrations/twitter-client');
const CoindeskClient = require('./api/integrations/coindesk-client');
const ScrapingBeeClient = require('./api/integrations/scrapingbee-client');
const AnthropicClient = require('./api/integrations/anthropic-client');
const PerplexityClient = require('./api/integrations/perplexity-client');
const GrokClient = require('./api/integrations/grok-client');

// Mock key manager for testing
const mockKeyManager = {
  getKey: async (service, keyName) => {
    const keyMap = {
      'coinbase': {
        'COINBASE_KEY_NAME': process.env.COINBASE_API_KEY_NAME,
        'COINBASE_PRIVATE_KEY': process.env.COINBASE_API_KEY_PRIVATE_KEY
      },
      'taapi': {
        'TAAPI_API_KEY': process.env.TAAPI_SECRET
      },
      'twitterapiio': {
        'TWITTERAPIIO_API_KEY': process.env.TWITTER_API_KEY || process.env.TWITTERAPI_KEY
      },
      'coindesk': {
        'COINDESK_API_KEY': process.env.COINDESK_API_KEY
      },
      'scrapingbee': {
        'SCRAPINGBEE_API_KEY': process.env.SCRAPINGBEE_API_KEY
      },
      'anthropic': {
        'ANTHROPIC_API_KEY': process.env.ANTHROPIC_API_KEY
      },
      'perplexity': {
        'PERPLEXITY_API_KEY': process.env.PERPLEXITY_API_KEY
      },
      'grok': {
        'GROK_API_KEY': process.env.XAI_API_KEY
      }
    };
    return keyMap[service]?.[keyName];
  }
};

async function testCoinbase() {
  console.log('\n🪙 Testing Coinbase API...');
  try {
    const client = new CoinbaseClient(mockKeyManager);
    const products = await client.getProducts();
    console.log(`✅ Coinbase: Found ${products.length} trading pairs`);
    
    // Test specific product
    const btcPrice = await client.getProduct('BTC-USD');
    console.log(`✅ BTC-USD Price: $${btcPrice.price}`);
    return true;
  } catch (error) {
    console.error('❌ Coinbase API Error:', error.message);
    return false;
  }
}

async function testTaapi() {
  console.log('\n📊 Testing TAAPI...');
  try {
    const client = new TaapiClient(mockKeyManager);
    
    // Test RSI indicator
    const rsi = await client.getRSI('binance', 'BTC/USDT', '1h');
    console.log(`✅ TAAPI RSI: ${rsi.value.toFixed(2)}`);
    
    // Test MACD
    const macd = await client.getMACD('binance', 'BTC/USDT', '1h');
    console.log(`✅ TAAPI MACD: Signal=${macd.valueMACDSignal.toFixed(2)}`);
    return true;
  } catch (error) {
    console.error('❌ TAAPI Error:', error.message);
    return false;
  }
}

async function testTwitter() {
  console.log('\n🐦 Testing Twitter API...');
  try {
    const client = new TwitterClient(mockKeyManager);
    
    // Test user lookup
    const user = await client.getUserByUsername('elonmusk');
    console.log(`✅ Twitter: Found user @${user.data.username} with ${user.data.public_metrics.followers_count} followers`);
    
    // Test tweet search
    const tweets = await client.searchTweets('bitcoin', 5);
    console.log(`✅ Twitter: Found ${tweets.data?.length || 0} recent tweets about bitcoin`);
    return true;
  } catch (error) {
    console.error('❌ Twitter API Error:', error.message);
    return false;
  }
}

async function testCoinDesk() {
  console.log('\n📰 Testing CoinDesk API...');
  try {
    const client = new CoindeskClient(mockKeyManager);
    
    // Test Bitcoin price index
    const bpi = await client.getCurrentPrice();
    console.log(`✅ CoinDesk BPI: $${bpi.bpi.USD.rate}`);
    
    // Test historical data
    const historical = await client.getHistoricalData('2024-01-01', '2024-01-07');
    console.log(`✅ CoinDesk: Retrieved ${Object.keys(historical.bpi).length} days of historical data`);
    return true;
  } catch (error) {
    console.error('❌ CoinDesk API Error:', error.message);
    return false;
  }
}

async function testScrapingBee() {
  console.log('\n🐝 Testing ScrapingBee...');
  try {
    const client = new ScrapingBeeClient(mockKeyManager);
    
    // Test account info
    const account = await client.getAccountInfo();
    console.log(`✅ ScrapingBee: ${account.max_api_credit - account.used_api_credit} credits remaining`);
    
    // Test simple scrape
    const result = await client.scrape('https://coinmarketcap.com/currencies/bitcoin/', {
      render_js: false,
      block_resources: true
    });
    console.log(`✅ ScrapingBee: Successfully scraped page (${result.length} bytes)`);
    return true;
  } catch (error) {
    console.error('❌ ScrapingBee Error:', error.message);
    return false;
  }
}

async function testAI() {
  console.log('\n🤖 Testing AI APIs...');
  
  const results = {
    anthropic: false,
    perplexity: false,
    grok: false
  };
  
  // Test Anthropic
  try {
    const client = new AnthropicClient(mockKeyManager);
    const response = await client.complete('What is the current Bitcoin price trend?', {
      max_tokens: 100
    });
    console.log(`✅ Anthropic: Got response (${response.length} chars)`);
    results.anthropic = true;
  } catch (error) {
    console.error('❌ Anthropic Error:', error.message);
  }
  
  // Test Perplexity
  try {
    const client = new PerplexityClient(mockKeyManager);
    const response = await client.complete('Latest crypto market news', {
      max_tokens: 100
    });
    console.log(`✅ Perplexity: Got response (${response.length} chars)`);
    results.perplexity = true;
  } catch (error) {
    console.error('❌ Perplexity Error:', error.message);
  }
  
  // Test Grok
  try {
    const client = new GrokClient(mockKeyManager);
    const response = await client.complete('Bitcoin sentiment analysis', {
      max_tokens: 100
    });
    console.log(`✅ Grok: Got response (${response.length} chars)`);
    results.grok = true;
  } catch (error) {
    console.error('❌ Grok Error:', error.message);
  }
  
  return results;
}

async function runAllTests() {
  console.log('🚀 Starting Comprehensive API Tests...\n');
  console.log('Environment:', process.env.NODE_ENV || 'development');
  
  const results = {
    coinbase: await testCoinbase(),
    taapi: await testTaapi(),
    twitter: await testTwitter(),
    coindesk: await testCoinDesk(),
    scrapingbee: await testScrapingBee(),
    ai: await testAI()
  };
  
  console.log('\n📊 Test Summary:');
  console.log('================');
  
  let allPassed = true;
  for (const [api, result] of Object.entries(results)) {
    if (api === 'ai') {
      console.log(`AI APIs:`);
      for (const [aiApi, aiResult] of Object.entries(result)) {
        console.log(`  ${aiResult ? '✅' : '❌'} ${aiApi}`);
        if (!aiResult) allPassed = false;
      }
    } else {
      console.log(`${result ? '✅' : '❌'} ${api}`);
      if (!result) allPassed = false;
    }
  }
  
  if (allPassed) {
    console.log('\n🎉 All APIs are working correctly!');
  } else {
    console.log('\n⚠️  Some APIs failed. Check the errors above.');
    process.exit(1);
  }
}

// Run tests
runAllTests().catch(console.error); 