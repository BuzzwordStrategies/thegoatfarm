require('dotenv').config({ path: require('path').join(__dirname, '.env') });
const UnifiedAPIManager = require('./api/api-manager');

async function testAPIIntegration() {
  const apiManager = new UnifiedAPIManager();
  
  try {
    console.log('🧪 Starting API Integration Test...\n');
    
    // Initialize the API manager
    await apiManager.initialize();
    
    // Test 1: Get API Status
    console.log('\n📊 TEST 1: API Status Check');
    console.log('═'.repeat(60));
    const status = apiManager.getStatus();
    console.log('System Status:', JSON.stringify(status, null, 2));
    
    // Test 2: Individual API Client Access
    console.log('\n🔌 TEST 2: Individual API Client Access');
    console.log('═'.repeat(60));
    
    try {
      const coinbaseClient = apiManager.getClient('coinbase');
      console.log('✅ Coinbase client retrieved successfully');
      
      // Test Coinbase time endpoint
      console.log('Testing Coinbase time endpoint...');
      const time = await coinbaseClient.getTime();
      console.log('Coinbase server time:', time);
    } catch (error) {
      console.error('❌ Coinbase test failed:', error.message);
    }
    
    // Test 3: Aggregated Market Data
    console.log('\n📈 TEST 3: Aggregated Market Data');
    console.log('═'.repeat(60));
    
    try {
      console.log('Fetching aggregated BTC/USD market data...');
      const marketData = await apiManager.getAggregatedMarketData('BTC/USD');
      
      console.log('\nMarket Data Summary:');
      console.log(`Symbol: ${marketData.symbol}`);
      console.log(`Average Price: $${marketData.averagePrice?.toFixed(2) || 'N/A'}`);
      console.log(`Sentiment: ${marketData.sentiment.recommendation || 'N/A'}`);
      console.log(`News Articles: ${marketData.news.length}`);
      
      if (marketData.indicators.rsi) {
        console.log(`RSI: ${marketData.indicators.rsi.value?.toFixed(2) || 'N/A'}`);
      }
    } catch (error) {
      console.error('❌ Market data aggregation failed:', error.message);
    }
    
    // Test 4: Trading Signal Generation
    console.log('\n🎯 TEST 4: Trading Signal Generation');
    console.log('═'.repeat(60));
    
    try {
      console.log('Generating trading signal for BTC/USD...');
      const signal = await apiManager.generateTradingSignal('BTC/USD', '1h');
      
      console.log('\nTrading Signal:');
      console.log(`Signal: ${signal.signal}`);
      console.log(`Confidence: ${signal.confidence?.toFixed(2)}%`);
      console.log(`Recommendation: ${signal.recommendation}`);
    } catch (error) {
      console.error('❌ Trading signal generation failed:', error.message);
    }
    
    // Test 5: News Monitoring
    console.log('\n📰 TEST 5: News Monitoring');
    console.log('═'.repeat(60));
    
    // Set up news event listeners
    apiManager.on('important-news', (data) => {
      console.log('\n🚨 IMPORTANT NEWS DETECTED:');
      data.articles.forEach(article => {
        console.log(`- ${article.title} (${article.source})`);
      });
    });
    
    apiManager.on('sentiment-update', (data) => {
      console.log('\n📊 Sentiment Update:');
      console.log(`Overall: ${data.recommendation}`);
      console.log(`Score: ${data.score}`);
    });
    
    // Start news monitoring (with shorter interval for testing)
    await apiManager.startNewsMonitoring(60000); // 1 minute for testing
    console.log('✅ News monitoring started');
    
    // Test 6: Social Media Monitoring
    console.log('\n🐦 TEST 6: Social Media Monitoring');
    console.log('═'.repeat(60));
    
    apiManager.on('social-update', (data) => {
      console.log('\n📱 Social Media Update:');
      console.log(`Reddit posts monitored: ${Object.keys(data.reddit).length}`);
      console.log(`Twitter accounts monitored: ${Object.keys(data.twitter).length}`);
    });
    
    // Start social monitoring
    await apiManager.startSocialMonitoring({
      redditSubreddits: ['bitcoin', 'cryptocurrency'],
      twitterAccounts: ['elonmusk', 'VitalikButerin'],
      interval: 120000 // 2 minutes for testing
    });
    console.log('✅ Social media monitoring started');
    
    // Test 7: API Metrics
    console.log('\n📊 TEST 7: API Metrics');
    console.log('═'.repeat(60));
    
    // Get metrics for each API
    const apis = ['coinbase', 'coindesk', 'taapi', 'scrapingbee'];
    for (const api of apis) {
      try {
        const client = apiManager.getClient(api);
        const metrics = client.getMetrics();
        console.log(`\n${api.toUpperCase()} Metrics:`);
        console.log(`  Total Requests: ${metrics.totalRequests}`);
        console.log(`  Success Rate: ${metrics.successRate?.toFixed(2)}%`);
        console.log(`  Avg Response Time: ${metrics.averageResponseTime?.toFixed(2)}ms`);
      } catch (error) {
        console.log(`\n${api.toUpperCase()}: No metrics available`);
      }
    }
    
    // Keep the test running for 3 minutes to see monitoring in action
    console.log('\n⏰ Monitoring will run for 3 minutes. Press Ctrl+C to stop.');
    
    setTimeout(async () => {
      console.log('\n🏁 Test complete. Shutting down...');
      await apiManager.shutdown();
      process.exit(0);
    }, 180000); // 3 minutes
    
  } catch (error) {
    console.error('\n❌ Test failed:', error);
    await apiManager.shutdown();
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\n🛑 Received interrupt signal. Shutting down gracefully...');
  process.exit(0);
});

// Run the test
if (require.main === module) {
  testAPIIntegration().catch(console.error);
} 