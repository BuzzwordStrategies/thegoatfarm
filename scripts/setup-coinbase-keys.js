#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const crypto = require('crypto');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('🔐 Coinbase Advanced Trade API Key Setup\n');

async function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function setupKeys() {
  try {
    // Get Key Name
    const keyName = await question('Enter your Coinbase Key Name (e.g., 8f68***6d3c): ');
    
    if (!keyName || !keyName.match(/^[a-f0-9]{4,}\*{3}[a-f0-9]{4}$/)) {
      console.error('❌ Invalid key name format');
      process.exit(1);
    }
    
    console.log('\nEnter your Private Key:');
    console.log('(Paste the entire key, including BEGIN/END lines if present)');
    console.log('Press Enter twice when done:\n');
    
    let privateKey = '';
    let emptyLineCount = 0;
    
    rl.on('line', (line) => {
      if (line === '') {
        emptyLineCount++;
        if (emptyLineCount >= 2) {
          rl.removeAllListeners('line');
          processPrivateKey(keyName, privateKey);
        }
      } else {
        emptyLineCount = 0;
        privateKey += line + '\n';
      }
    });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function processPrivateKey(keyName, privateKey) {
  privateKey = privateKey.trim();
  
  // Validate and format private key
  if (!privateKey) {
    console.error('❌ Private key cannot be empty');
    process.exit(1);
  }
  
  // If it's not in PEM format, add headers
  if (!privateKey.includes('BEGIN EC PRIVATE KEY')) {
    privateKey = `-----BEGIN EC PRIVATE KEY-----\n${privateKey}\n-----END EC PRIVATE KEY-----`;
  }
  
  // Test the key
  try {
    crypto.createSign('SHA256').update('test').sign(privateKey, 'base64');
    console.log('✅ Private key validated successfully');
  } catch (error) {
    console.error('❌ Invalid private key:', error.message);
    process.exit(1);
  }
  
  // Update .env file
  const envPath = path.join(process.cwd(), '.env');
  let envContent = '';
  
  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, 'utf8');
    
    // Remove old Coinbase keys
    envContent = envContent.replace(/COINBASE_API_KEY=.*/g, '');
    envContent = envContent.replace(/COINBASE_API_SECRET=.*/g, '');
    envContent = envContent.replace(/COINBASE_API_PASSPHRASE=.*/g, '');
    envContent = envContent.replace(/COINBASE_SANDBOX=.*/g, '');
    
    // Remove existing new keys
    envContent = envContent.replace(/COINBASE_KEY_NAME=.*/g, '');
    envContent = envContent.replace(/COINBASE_PRIVATE_KEY=.*/g, '');
  }
  
  // Add new keys
  const newKeys = `
# Coinbase Advanced Trade API
COINBASE_KEY_NAME=${keyName}
COINBASE_PRIVATE_KEY=${privateKey.replace(/\n/g, '\\n')}
`;
  
  envContent += newKeys;
  
  fs.writeFileSync(envPath, envContent.trim() + '\n');
  
  console.log('\n✅ Coinbase API keys have been configured successfully!');
  console.log('\nNext steps:');
  console.log('1. Run: node src/utils/security/api-key-audit.js');
  console.log('2. Start the application: npm run dev');
  
  rl.close();
}

setupKeys(); 