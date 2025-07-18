const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class SecureAPIKeyManager {
  constructor() {
    this.encryptionKey = this.deriveEncryptionKey();
    this.keyStore = new Map();
    this.configPath = path.join(process.cwd(), '.secure-keys');
  }
  
  deriveEncryptionKey() {
    // In production, this should come from a secure key management service
    const masterKey = process.env.MASTER_ENCRYPTION_KEY || 'default-dev-key-change-in-production';
    return crypto.createHash('sha256').update(masterKey).digest();
  }
  
  encrypt(text) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', this.encryptionKey, iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return iv.toString('hex') + ':' + encrypted;
  }
  
  decrypt(encryptedText) {
    const parts = encryptedText.split(':');
    const iv = Buffer.from(parts[0], 'hex');
    const encrypted = parts[1];
    const decipher = crypto.createDecipheriv('aes-256-cbc', this.encryptionKey, iv);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }
  
  async storeKey(service, keyName, keyValue) {
    if (!this.keyStore.has(service)) {
      this.keyStore.set(service, {});
    }
    
    const encryptedValue = this.encrypt(keyValue);
    this.keyStore.get(service)[keyName] = {
      encrypted: encryptedValue,
      addedAt: new Date().toISOString(),
      lastUsed: null,
      usageCount: 0
    };
    
    await this.saveKeyStore();
    console.log(`✅ Stored key ${keyName} for ${service}`);
  }
  
  async getKey(service, keyName) {
    await this.loadKeyStore();
    
    const serviceKeys = this.keyStore.get(service);
    if (!serviceKeys || !serviceKeys[keyName]) {
      throw new Error(`Key ${keyName} not found for service ${service}`);
    }
    
    const keyData = serviceKeys[keyName];
    keyData.lastUsed = new Date().toISOString();
    keyData.usageCount++;
    
    await this.saveKeyStore();
    
    return this.decrypt(keyData.encrypted);
  }
  
  async rotateKey(service, keyName, newKeyValue) {
    const oldKeyData = this.keyStore.get(service)?.[keyName];
    if (!oldKeyData) {
      throw new Error(`Key ${keyName} not found for service ${service}`);
    }
    
    // Archive old key
    if (!oldKeyData.history) oldKeyData.history = [];
    oldKeyData.history.push({
      encrypted: oldKeyData.encrypted,
      rotatedAt: new Date().toISOString()
    });
    
    // Store new key
    oldKeyData.encrypted = this.encrypt(newKeyValue);
    oldKeyData.lastRotated = new Date().toISOString();
    
    await this.saveKeyStore();
    console.log(`🔄 Rotated key ${keyName} for ${service}`);
  }
  
  async validateKeys() {
    const validationResults = {};
    
    for (const [service, keys] of this.keyStore.entries()) {
      validationResults[service] = {};
      
      for (const [keyName, keyData] of Object.entries(keys)) {
        try {
          const decrypted = this.decrypt(keyData.encrypted);
          validationResults[service][keyName] = {
            valid: true,
            length: decrypted.length,
            lastUsed: keyData.lastUsed,
            usageCount: keyData.usageCount
          };
        } catch (error) {
          validationResults[service][keyName] = {
            valid: false,
            error: error.message
          };
        }
      }
    }
    
    return validationResults;
  }
  
  async saveKeyStore() {
    const data = JSON.stringify(Array.from(this.keyStore.entries()));
    await fs.writeFile(this.configPath, data, 'utf8');
  }
  
  async loadKeyStore() {
    try {
      const data = await fs.readFile(this.configPath, 'utf8');
      this.keyStore = new Map(JSON.parse(data));
    } catch (error) {
      // File doesn't exist yet
      this.keyStore = new Map();
    }
  }
  
  async initializeFromEnv() {
    const apiKeyMappings = {
      coinbase: ['COINBASE_KEY_NAME', 'COINBASE_PRIVATE_KEY'],
      coindesk: ['COINDESK_API_KEY'],
      taapi: ['TAAPI_API_KEY'],
      perplexity: ['PERPLEXITY_API_KEY'],
      grok: ['GROK_API_KEY'],
      anthropic: ['ANTHROPIC_API_KEY'],
      scrapingbee: ['SCRAPINGBEE_API_KEY'],
      twitterapiio: ['TWITTERAPIIO_API_KEY']
    };
    
    for (const [service, keys] of Object.entries(apiKeyMappings)) {
      for (const keyName of keys) {
        if (process.env[keyName]) {
          await this.storeKey(service, keyName, process.env[keyName]);
        }
      }
    }
    
    console.log('✅ Initialized secure key store from environment variables');
  }
}

module.exports = SecureAPIKeyManager; 