const botRegistry = require('./config/botRegistry');

class BotManager {
  constructor() {
    this.bots = new Map();
  }
  
  async initialize() {
    for (const botConfig of botRegistry.activeBots) {
      if (botConfig.enabled) {
        try {
          const BotClass = require(botConfig.path);
          const bot = new BotClass(botConfig.config);
          this.bots.set(botConfig.name, bot);
          console.log(`✅ Initialized ${botConfig.name}`);
        } catch (error) {
          console.error(`❌ Failed to initialize ${botConfig.name}:`, error.message);
        }
      }
    }
  }
  
  async startAll() {
    for (const [name, bot] of this.bots) {
      try {
        await bot.start();
        console.log(`✅ Started ${name}`);
      } catch (error) {
        console.error(`❌ Failed to start ${name}:`, error.message);
      }
    }
  }
  
  async stopAll() {
    for (const [name, bot] of this.bots) {
      try {
        await bot.stop();
        console.log(`✅ Stopped ${name}`);
      } catch (error) {
        console.error(`❌ Failed to stop ${name}:`, error.message);
      }
    }
  }
  
  getBot(name) {
    return this.bots.get(name);
  }
  
  getBotStatus() {
    const status = {};
    for (const [name, bot] of this.bots) {
      status[name] = {
        active: bot.isRunning ? bot.isRunning() : false,
        lastRun: bot.lastRun || null
      };
    }
    return status;
  }
}

module.exports = BotManager; 