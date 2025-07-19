// Bot Registry - Add new bots here for scalability
module.exports = {
  activeBots: [
    {
      name: 'TradingBot',
      path: './active/TradingBot',
      enabled: true,
      config: { interval: 300000 } // 5 minutes
    },
    {
      name: 'SentimentBot',
      path: './active/SentimentBot',
      enabled: true,
      config: { interval: 600000 } // 10 minutes
    },
    {
      name: 'ArbitrageBot',
      path: './active/ArbitrageBot',
      enabled: true,
      config: { interval: 60000 } // 1 minute
    }
    // Add new bots here
  ]
}; 