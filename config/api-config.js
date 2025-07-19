// /config/api-config.js
const crypto = require('crypto');
const elliptic = require('elliptic');
const ec = new elliptic.ec('secp256k1');

module.exports = {
  coinbase: {
    apiKey: process.env.COINBASE_API_KEY,
    apiSecret: process.env.COINBASE_API_SECRET,
    apiPassphrase: process.env.COINBASE_API_PASSPHRASE,
    
    // ECDSA Configuration
    ecdsa: {
      privateKey: process.env.COINBASE_ECDSA_PRIVATE_KEY,
      publicKey: process.env.COINBASE_ECDSA_PUBLIC_KEY,
      
      signRequest: (method, path, body = '') => {
        const timestamp = Date.now() / 1000;
        const message = timestamp + method.toUpperCase() + path + body;
        
        const key = ec.keyFromPrivate(process.env.COINBASE_ECDSA_PRIVATE_KEY, 'hex');
        const signature = key.sign(crypto.createHash('sha256').update(message).digest());
        
        return {
          signature: signature.toDER('hex'),
          timestamp: timestamp
        };
      }
    },
    
    endpoints: {
      base: 'https://api.coinbase.com',
      wsBase: 'wss://ws-feed.coinbase.com',
      accounts: '/v2/accounts',
      prices: '/v2/prices',
      trades: '/v2/trades',
      orders: '/v3/brokerage/orders'
    },
    
    rateLimit: {
      maxRequests: 10000,
      windowMs: 3600000, // 1 hour
      retryAfter: 60000 // 1 minute
    }
  },
  
  // Add other API configurations here
  analytics: {
    apiKey: process.env.ANALYTICS_API_KEY,
    endpoint: process.env.ANALYTICS_ENDPOINT
  },
  
  // WebSocket configuration
  websocket: {
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000
  }
}; 