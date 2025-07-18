require('dotenv').config();
const APIKeyAuditor = require('./utils/security/api-key-audit');

async function main() {
  console.log('🚀 Starting API Audit System...\n');
  
  // Map Python environment variables to Node.js expected format
  const envMappings = {
    'COINBASE_API_KEY': process.env.COINBASE_API_KEY,
    'COINBASE_API_SECRET': process.env.COINBASE_SECRET,
    'COINBASE_API_PASSPHRASE': process.env.COINBASE_API_PASSPHRASE || 'passphrase',
    'COINDESK_API_KEY': process.env.COINDESK_API_KEY,
    'TAAPI_API_KEY': process.env.TAAPI_KEY,
    'PERPLEXITY_API_KEY': process.env.PERPLEXITY_API_KEY,
    'GROK_API_KEY': process.env.GROK_API_KEY,
    'ANTHROPIC_API_KEY': process.env.CLAUDE_API_KEY,
    'SCRAPINGBEE_API_KEY': process.env.SCRAPINGBEE_API_KEY,
    'TWITTER_API_KEY': process.env.TWITTER_API_KEY,
    'TWITTER_API_SECRET': process.env.TWITTER_API_SECRET,
    'TWITTER_ACCESS_TOKEN': process.env.TWITTER_ACCESS_TOKEN,
    'TWITTER_ACCESS_SECRET': process.env.TWITTER_ACCESS_SECRET
  };
  
  // Set environment variables
  for (const [key, value] of Object.entries(envMappings)) {
    if (value) {
      process.env[key] = value;
    }
  }
  
  try {
    const auditor = new APIKeyAuditor();
    const results = await auditor.runFullAudit();
    
    console.log('\n📋 Detailed Audit Results:');
    console.log('═'.repeat(60));
    
    for (const [apiName, result] of Object.entries(results.keys)) {
      console.log(`\n${apiName.toUpperCase()}:`);
      console.log(`  Status: ${result.status}`);
      console.log(`  Present Keys: ${result.presentKeys.length}`);
      console.log(`  Missing Keys: ${result.missingKeys.length}`);
      
      if (result.missingKeys.length > 0) {
        console.log(`  Missing: ${result.missingKeys.join(', ')}`);
      }
      
      if (result.errors.length > 0) {
        console.log(`  Errors: ${result.errors.join('; ')}`);
      }
    }
    
  } catch (error) {
    console.error('❌ Audit failed:', error.message);
    process.exit(1);
  }
}

// Run the audit
main().catch(console.error); 