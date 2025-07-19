require('dotenv').config();

async function testAllAPIs() {
  console.log('Testing all API connections...\n');
  
  // Test Coinbase
  try {
    if (process.env.COINBASE_API_KEY_NAME && process.env.COINBASE_API_KEY_PRIVATE_KEY) {
      // Test with CDP keys
      console.log('✅ Coinbase CDP keys found');
    } else if (process.env.COINBASE_API_KEY && process.env.COINBASE_API_SECRET) {
      // Test with legacy keys
      console.log('✅ Coinbase legacy keys found');
    } else {
      throw new Error('No Coinbase keys found');
    }
  } catch (error) {
    console.log('❌ Coinbase API:', error.message);
  }
  
  // Test Twitter
  try {
    const twitterKey = process.env.TWITTER_API_KEY || process.env.TWITTERAPI_KEY;
    if (twitterKey) {
      const response = await fetch(`${process.env.TWITTER_API_BASE_URL || 'https://api.twitterapi.io/v1'}/test`, {
        headers: { 'Authorization': `Bearer ${twitterKey}` }
      });
      console.log('✅ Twitter API: Key found');
    } else {
      throw new Error('No Twitter API key found');
    }
  } catch (error) {
    console.log('❌ Twitter API:', error.message);
  }
  
  // Test TAAPI
  try {
    if (process.env.TAAPI_SECRET) {
      console.log('✅ TAAPI: Key found');
      // Could make actual API call here to test
    } else {
      throw new Error('No TAAPI key found');
    }
  } catch (error) {
    console.log('❌ TAAPI:', error.message);
  }
  
  // Test ScrapingBee
  try {
    if (process.env.SCRAPINGBEE_API_KEY) {
      console.log('✅ ScrapingBee: Key found');
    } else {
      throw new Error('No ScrapingBee key found');
    }
  } catch (error) {
    console.log('❌ ScrapingBee:', error.message);
  }
  
  // Test AI APIs
  const aiAPIs = {
    'XAI/Grok': 'XAI_API_KEY',
    'Perplexity': 'PERPLEXITY_API_KEY',
    'Anthropic': 'ANTHROPIC_API_KEY'
  };
  
  for (const [name, envVar] of Object.entries(aiAPIs)) {
    try {
      if (process.env[envVar]) {
        console.log(`✅ ${name}: Key found`);
      } else {
        throw new Error(`No ${name} key found`);
      }
    } catch (error) {
      console.log(`❌ ${name}:`, error.message);
    }
  }
  
  // Summary
  console.log('\n=== API Key Summary ===');
  const requiredKeys = [
    'COINBASE_API_KEY_NAME or COINBASE_API_KEY',
    'TWITTER_API_KEY or TWITTERAPI_KEY',
    'TAAPI_SECRET',
    'SCRAPINGBEE_API_KEY',
    'XAI_API_KEY',
    'PERPLEXITY_API_KEY', 
    'ANTHROPIC_API_KEY'
  ];
  
  console.log('Required environment variables:', requiredKeys.join(', '));
  console.log('\nMake sure your .env file contains all required keys.');
}

// Run the test
testAllAPIs().catch(console.error); 