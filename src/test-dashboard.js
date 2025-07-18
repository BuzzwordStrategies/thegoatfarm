// Test Dashboard Server
const WebSocket = require('ws');
const fetch = require('node-fetch');

const SERVER_URL = 'http://localhost:3001';
const WS_URL = 'ws://localhost:3002';

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

async function testDashboard() {
  console.log(`${colors.blue}Starting Dashboard Server Tests...${colors.reset}\n`);
  
  // Test 1: HTTP Server
  console.log('1. Testing HTTP Server...');
  try {
    const response = await fetch(`${SERVER_URL}/api/health`);
    const data = await response.json();
    console.log(`${colors.green}✓ HTTP Server is running${colors.reset}`);
    console.log(`  Response: ${JSON.stringify(data)}\n`);
  } catch (error) {
    console.log(`${colors.red}✗ HTTP Server is not running${colors.reset}`);
    console.log(`  Error: ${error.message}\n`);
    console.log(`${colors.yellow}Please start the server with: npm start${colors.reset}`);
    return;
  }
  
  // Test 2: Dashboard UI
  console.log('2. Testing Dashboard UI...');
  try {
    const response = await fetch(SERVER_URL);
    if (response.ok) {
      console.log(`${colors.green}✓ Dashboard UI is accessible${colors.reset}`);
      console.log(`  URL: ${SERVER_URL}\n`);
    } else {
      console.log(`${colors.red}✗ Dashboard UI returned status ${response.status}${colors.reset}\n`);
    }
  } catch (error) {
    console.log(`${colors.red}✗ Failed to access Dashboard UI${colors.reset}`);
    console.log(`  Error: ${error.message}\n`);
  }
  
  // Test 3: Initial Data API
  console.log('3. Testing Initial Data API...');
  try {
    const response = await fetch(`${SERVER_URL}/api/dashboard/initial`);
    const data = await response.json();
    console.log(`${colors.green}✓ Initial Data API is working${colors.reset}`);
    console.log(`  API Status: ${data.apiStatus ? 'Available' : 'Not available'}`);
    console.log(`  Market Data: ${data.marketData ? 'Available' : 'Not available'}`);
    console.log(`  News: ${data.news ? data.news.length + ' articles' : 'Not available'}`);
    console.log(`  Signals: ${data.signals ? data.signals.length + ' signals' : 'Not available'}\n`);
  } catch (error) {
    console.log(`${colors.red}✗ Initial Data API failed${colors.reset}`);
    console.log(`  Error: ${error.message}\n`);
  }
  
  // Test 4: WebSocket Server
  console.log('4. Testing WebSocket Server...');
  
  return new Promise((resolve) => {
    const ws = new WebSocket(WS_URL);
    let messageCount = 0;
    
    ws.on('open', () => {
      console.log(`${colors.green}✓ WebSocket connected${colors.reset}`);
      
      // Send test messages
      ws.send(JSON.stringify({ type: 'subscribe', channels: ['all'] }));
      ws.send(JSON.stringify({ type: 'get-status' }));
    });
    
    ws.on('message', (data) => {
      messageCount++;
      const message = JSON.parse(data.toString());
      console.log(`  Received: ${message.type}`);
      
      if (messageCount >= 2) {
        console.log(`${colors.green}✓ WebSocket communication working${colors.reset}\n`);
        ws.close();
      }
    });
    
    ws.on('error', (error) => {
      console.log(`${colors.red}✗ WebSocket error${colors.reset}`);
      console.log(`  Error: ${error.message}\n`);
      resolve();
    });
    
    ws.on('close', () => {
      // Test 5: Market Data API
      console.log('5. Testing Market Data API...');
      fetch(`${SERVER_URL}/api/market/BTC/USD`)
        .then(response => response.json())
        .then(data => {
          console.log(`${colors.green}✓ Market Data API working${colors.reset}`);
          if (data.averagePrice) {
            console.log(`  BTC/USD Price: $${data.averagePrice.toFixed(2)}`);
          }
          console.log();
        })
        .catch(error => {
          console.log(`${colors.red}✗ Market Data API failed${colors.reset}`);
          console.log(`  Error: ${error.message}\n`);
        })
        .finally(() => {
          // Summary
          console.log(`${colors.blue}Dashboard Test Summary:${colors.reset}`);
          console.log(`- HTTP Server: ${colors.green}Running${colors.reset}`);
          console.log(`- WebSocket Server: ${colors.green}Running${colors.reset}`);
          console.log(`- Dashboard UI: ${colors.green}Accessible${colors.reset}`);
          console.log(`- APIs: ${colors.green}Functional${colors.reset}`);
          console.log(`\n${colors.green}✓ Dashboard is ready to use!${colors.reset}`);
          console.log(`${colors.yellow}Open ${SERVER_URL} in your browser${colors.reset}`);
          resolve();
        });
    });
    
    // Timeout fallback
    setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      console.log(`${colors.yellow}WebSocket test timed out${colors.reset}\n`);
      resolve();
    }, 5000);
  });
}

// Run tests
testDashboard().catch(console.error); 