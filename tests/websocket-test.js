const WebSocket = require('ws');

const WS_URL = process.env.WS_URL || 'ws://localhost:3002';

console.log('Testing WebSocket connection...');

const ws = new WebSocket(WS_URL);

let messageCount = 0;
const testTimeout = setTimeout(() => {
  console.error('❌ WebSocket test timed out');
  process.exit(1);
}, 10000);

ws.on('open', () => {
  console.log('✅ WebSocket connected successfully');
  
  // Test subscribe message
  ws.send(JSON.stringify({ type: 'subscribe', channels: ['all'] }));
  console.log('📤 Sent subscribe message');
  
  // Test status request
  ws.send(JSON.stringify({ type: 'get-status' }));
  console.log('📤 Sent status request');
  
  // Test market data request
  ws.send(JSON.stringify({ type: 'get-market-data', symbol: 'BTC/USD' }));
  console.log('📤 Sent market data request');
});

ws.on('message', (data) => {
  messageCount++;
  const message = JSON.parse(data.toString());
  console.log(`📥 Received message ${messageCount}: ${message.type}`);
  
  if (messageCount >= 3) {
    console.log('✅ All WebSocket tests passed');
    clearTimeout(testTimeout);
    ws.close();
    process.exit(0);
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocket error:', error.message);
  clearTimeout(testTimeout);
  process.exit(1);
});

ws.on('close', () => {
  console.log('WebSocket connection closed');
}); 