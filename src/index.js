require('dotenv').config();
const BotManager = require('./bots/BotManager');

async function main() {
  console.log('🚀 Starting The GOAT Farm...\n');
  
  // Validate environment variables
  const requiredEnvVars = [
    { name: 'COINBASE_API_KEY_NAME', alternative: 'COINBASE_API_KEY' },
    { name: 'TWITTER_API_KEY', alternative: 'TWITTERAPI_KEY' },
    { name: 'TAAPI_SECRET' },
    { name: 'SCRAPINGBEE_API_KEY' }
  ];
  
  let hasAllKeys = true;
  for (const envVar of requiredEnvVars) {
    if (typeof envVar === 'string') {
      if (!process.env[envVar]) {
        console.error(`❌ Missing required environment variable: ${envVar}`);
        hasAllKeys = false;
      }
    } else {
      // Check for primary or alternative
      if (!process.env[envVar.name] && (!envVar.alternative || !process.env[envVar.alternative])) {
        console.error(`❌ Missing required environment variable: ${envVar.name}${envVar.alternative ? ` or ${envVar.alternative}` : ''}`);
        hasAllKeys = false;
      }
    }
  }
  
  if (!hasAllKeys) {
    console.error('\n⚠️  Please set all required environment variables in your .env file');
    console.error('📄 See env.example for the complete list of required variables');
    process.exit(1);
  }
  
  console.log('✅ All required environment variables found\n');
  
  // Initialize and start bots
  const botManager = new BotManager();
  
  try {
    await botManager.initialize();
    await botManager.startAll();
    
    console.log('\n🤖 All bots are running!');
    console.log('Press Ctrl+C to stop\n');
  } catch (error) {
    console.error('❌ Failed to start bots:', error.message);
    process.exit(1);
  }
  
  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n\n🛑 Shutting down gracefully...');
    await botManager.stopAll();
    console.log('👋 Goodbye!');
    process.exit(0);
  });
  
  // Keep the process running
  setInterval(() => {
    // Heartbeat - could add status logging here
  }, 60000);
}

// Start the application
main().catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
}); 