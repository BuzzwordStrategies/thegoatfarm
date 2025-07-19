// /src/core/StartupValidator.js
import ApiOrchestrator from './ApiOrchestrator';
import Redis from 'ioredis';
import { Client as PGClient } from 'pg';
import fs from 'fs';
import path from 'path';

class StartupValidator {
  constructor() {
    this.validationResults = [];
    this.criticalFailures = [];
  }

  async validateAll() {
    console.log('🔍 Starting comprehensive validation...\n');
    
    const validations = [
      this.validateEnvironmentVariables(),
      this.validateApiConnections(),
      this.validateDatabaseConnection(),
      this.validateRedisConnection(),
      this.validateWebSocketConnections(),
      this.validateFilePermissions(),
      this.validateDependencies()
    ];
    
    const results = await Promise.all(validations);
    const allPassed = results.every(r => r.success);
    
    // Print summary
    console.log('\n📊 Validation Summary:');
    console.log('═════════════════════════════════════════');
    
    results.forEach(result => {
      const icon = result.success ? '✅' : '❌';
      const status = result.success ? 'PASSED' : 'FAILED';
      console.log(`${icon} ${result.category}: ${status}`);
      
      if (!result.success) {
        console.log(`   └─ Error: ${result.error}`);
        if (result.details) {
          result.details.forEach(detail => {
            console.log(`      └─ ${detail}`);
          });
        }
      }
    });
    
    console.log('═════════════════════════════════════════\n');
    
    if (!allPassed) {
      console.error('❌ Startup validation FAILED');
      console.error('\nCritical issues that must be resolved:');
      this.criticalFailures.forEach((issue, index) => {
        console.error(`${index + 1}. ${issue}`);
      });
      
      console.error('\n⚠️  The application cannot start until these issues are fixed.');
      process.exit(1); // DO NOT START THE APPLICATION
    }
    
    console.log('✅ All validations passed! Starting application...\n');
    return true;
  }
  
  async validateEnvironmentVariables() {
    console.log('Checking environment variables...');
    
    const required = [
      // Coinbase
      'COINBASE_CDP_API_KEY_NAME',
      'COINBASE_CDP_API_KEY_SECRET',
      'COINBASE_ECDSA_PRIVATE_KEY',
      'COINBASE_ECDSA_PUBLIC_KEY',
      
      // Other APIs
      'TAAPI_API_KEY',
      'TWITTERAPI_API_KEY',
      'SCRAPINGBEE_API_KEY',
      'XAI_API_KEY',
      'PERPLEXITY_API_KEY',
      'ANTHROPIC_API_KEY',
      
      // System
      'SYSTEM_SECRET',
      'REDIS_URL',
      'DATABASE_URL',
      'SESSION_SECRET',
      'PORT'
    ];
    
    const missing = [];
    const warnings = [];
    
    required.forEach(key => {
      if (!process.env[key]) {
        missing.push(key);
      }
    });
    
    // Check for default values
    if (process.env.SYSTEM_SECRET === 'default-goat-farm-2025') {
      warnings.push('SYSTEM_SECRET is using default value - SECURITY RISK!');
      this.criticalFailures.push('Change SYSTEM_SECRET from default value');
    }
    
    if (process.env.SESSION_SECRET === 'supersecretkey') {
      warnings.push('SESSION_SECRET is using default value - SECURITY RISK!');
      this.criticalFailures.push('Change SESSION_SECRET from default value');
    }
    
    if (missing.length > 0) {
      this.criticalFailures.push(`Set missing environment variables: ${missing.join(', ')}`);
      return {
        success: false,
        category: 'Environment Variables',
        error: `Missing ${missing.length} required variables`,
        details: missing.map(key => `Missing: ${key}`)
      };
    }
    
    return {
      success: warnings.length === 0,
      category: 'Environment Variables',
      error: warnings.length > 0 ? `${warnings.length} security warnings` : null,
      details: warnings
    };
  }
  
  async validateApiConnections() {
    console.log('Testing API connections...');
    
    const orchestrator = ApiOrchestrator.getInstance();
    const apis = [
      'coinbase',
      'taapi',
      'twitterapi',
      'scrapingbee',
      'grok',
      'perplexity',
      'anthropic',
      'coindesk'
    ];
    
    const failures = [];
    
    for (const api of apis) {
      try {
        const health = await orchestrator.checkApiHealth(api);
        if (!health) {
          failures.push(`${api}: Health check failed`);
        }
      } catch (error) {
        failures.push(`${api}: ${error.message}`);
      }
    }
    
    if (failures.length > 0) {
      // Check if critical APIs are down
      if (failures.some(f => f.startsWith('coinbase:'))) {
        this.criticalFailures.push('Coinbase API connection failed - trading will not work');
      }
      
      return {
        success: false,
        category: 'API Connections',
        error: `${failures.length} APIs failed health check`,
        details: failures
      };
    }
    
    return {
      success: true,
      category: 'API Connections'
    };
  }
  
  async validateDatabaseConnection() {
    console.log('Testing database connection...');
    
    try {
      // For SQLite (current implementation)
      const dbPath = path.join(process.cwd(), 'data', 'app.db');
      
      if (!fs.existsSync(dbPath)) {
        // Initialize database if it doesn't exist
        const { init_db } = await import('../../utils/db.py');
        init_db();
      }
      
      // Check if we can read the database
      const stats = fs.statSync(dbPath);
      if (!stats.isFile()) {
        throw new Error('Database file is not accessible');
      }
      
      return {
        success: true,
        category: 'Database Connection'
      };
    } catch (error) {
      this.criticalFailures.push('Database connection failed - app cannot store data');
      return {
        success: false,
        category: 'Database Connection',
        error: error.message
      };
    }
  }
  
  async validateRedisConnection() {
    console.log('Testing Redis connection...');
    
    try {
      const redis = new Redis(process.env.REDIS_URL);
      
      // Test connection with ping
      const pong = await redis.ping();
      if (pong !== 'PONG') {
        throw new Error('Redis ping failed');
      }
      
      // Test write/read
      await redis.set('test:startup', 'ok', 'EX', 10);
      const value = await redis.get('test:startup');
      if (value !== 'ok') {
        throw new Error('Redis read/write test failed');
      }
      
      await redis.del('test:startup');
      redis.disconnect();
      
      return {
        success: true,
        category: 'Redis Connection'
      };
    } catch (error) {
      // Redis is optional - used for caching and rate limiting
      return {
        success: true,
        category: 'Redis Connection',
        warning: 'Redis not available - using in-memory fallback'
      };
    }
  }
  
  async validateWebSocketConnections() {
    console.log('Testing WebSocket connections...');
    
    const orchestrator = ApiOrchestrator.getInstance();
    
    // Wait for WebSocket connections to establish
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    const wsApis = ['coinbase'];
    const failures = [];
    
    wsApis.forEach(api => {
      const ws = orchestrator.websockets.get(api);
      if (!ws || ws.readyState !== 1) { // 1 = OPEN
        failures.push(`${api}: WebSocket not connected`);
      }
    });
    
    if (failures.length > 0) {
      return {
        success: false,
        category: 'WebSocket Connections',
        error: `${failures.length} WebSocket connections failed`,
        details: failures
      };
    }
    
    return {
      success: true,
      category: 'WebSocket Connections'
    };
  }
  
  async validateFilePermissions() {
    console.log('Checking file permissions...');
    
    const criticalPaths = [
      'data',
      'logs',
      '.env',
      'config'
    ];
    
    const issues = [];
    
    criticalPaths.forEach(pathName => {
      const fullPath = path.join(process.cwd(), pathName);
      
      try {
        if (pathName.includes('.')) {
          // File check
          fs.accessSync(fullPath, fs.constants.R_OK | fs.constants.W_OK);
        } else {
          // Directory check
          if (!fs.existsSync(fullPath)) {
            fs.mkdirSync(fullPath, { recursive: true });
          }
          fs.accessSync(fullPath, fs.constants.R_OK | fs.constants.W_OK);
        }
      } catch (error) {
        issues.push(`${pathName}: ${error.message}`);
      }
    });
    
    if (issues.length > 0) {
      return {
        success: false,
        category: 'File Permissions',
        error: `${issues.length} permission issues`,
        details: issues
      };
    }
    
    return {
      success: true,
      category: 'File Permissions'
    };
  }
  
  async validateDependencies() {
    console.log('Checking dependencies...');
    
    try {
      // Check package.json exists
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), 'package.json'), 'utf8')
      );
      
      // Check critical Node.js dependencies
      const criticalDeps = [
        'opossum',
        'ws',
        'ioredis',
        'express'
      ];
      
      const missing = criticalDeps.filter(dep => 
        !packageJson.dependencies[dep] && !packageJson.devDependencies[dep]
      );
      
      if (missing.length > 0) {
        return {
          success: false,
          category: 'Dependencies',
          error: `Missing critical dependencies: ${missing.join(', ')}`,
          details: [`Run: npm install ${missing.join(' ')}`]
        };
      }
      
      return {
        success: true,
        category: 'Dependencies'
      };
    } catch (error) {
      return {
        success: false,
        category: 'Dependencies',
        error: 'Could not check dependencies',
        details: [error.message]
      };
    }
  }
  
  // Run validation and exit if fails
  static async validate() {
    const validator = new StartupValidator();
    return await validator.validateAll();
  }
}

// Auto-run if called directly
if (require.main === module) {
  StartupValidator.validate();
}

export default StartupValidator; 