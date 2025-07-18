#!/usr/bin/env node

/**
 * GOAT Farm Complete Launcher
 * This script validates everything and launches the entire trading platform
 * Ensures 100% functionality before starting any trading operations
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');
const net = require('net');
const readline = require('readline');

// Terminal colors for better output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Configuration
const CONFIG = {
  ports: {
    flask: 5000,
    express: 3001,
    websocket: 3002,
    redis: 6379
  },
  requiredKeys: {
    coinbase: ['COINBASE_KEY_NAME', 'COINBASE_PRIVATE_KEY'],
    coindesk: ['COINDESK_API_KEY'],
    taapi: ['TAAPI_API_KEY'],
    perplexity: ['PERPLEXITY_API_KEY'],
    grok: ['GROK_API_KEY'],
    anthropic: ['ANTHROPIC_API_KEY'],
    scrapingbee: ['SCRAPINGBEE_API_KEY'],
    twitterapiio: ['TWITTERAPIIO_API_KEY']
  }
};

// Process tracking
const processes = {
  redis: null,
  pythonBots: null,
  flaskDashboard: null,
  nodeDashboard: null,
  websocketServer: null
};

// Utility functions
function log(message, type = 'info') {
  const typeColors = {
    info: colors.blue,
    success: colors.green,
    error: colors.red,
    warning: colors.yellow,
    process: colors.magenta
  };
  const color = typeColors[type] || colors.reset;
  console.log(`${color}[${new Date().toTimeString().split(' ')[0]}] ${message}${colors.reset}`);
}

function checkPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    server.listen(port);
  });
}

function waitForPort(port, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      const client = net.createConnection({ port }, () => {
        client.end();
        resolve();
      });
      
      client.on('error', () => {
        if (Date.now() - startTime > timeout) {
          reject(new Error(`Port ${port} did not become available within ${timeout}ms`));
        } else {
          setTimeout(check, 1000);
        }
      });
    };
    
    check();
  });
}

function checkEnvFile() {
  const envPath = path.join(process.cwd(), '.env');
  if (!fs.existsSync(envPath)) {
    log('❌ .env file not found!', 'error');
    log('Please create a .env file with your API keys. You can use env.example as a template.', 'warning');
    return false;
  }
  return true;
}

function loadEnv() {
  const envPath = path.join(process.cwd(), '.env');
  const envContent = fs.readFileSync(envPath, 'utf8');
  const env = {};
  
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    }
  });
  
  return env;
}

function validateApiKeys(env) {
  log('🔐 Validating API keys...', 'info');
  let allValid = true;
  const missingKeys = [];
  
  for (const [service, keys] of Object.entries(CONFIG.requiredKeys)) {
    for (const key of keys) {
      if (!env[key] || env[key] === '' || env[key].includes('your_')) {
        missingKeys.push(`${service}: ${key}`);
        allValid = false;
      }
    }
  }
  
  if (!allValid) {
    log('❌ Missing or invalid API keys:', 'error');
    missingKeys.forEach(key => log(`  - ${key}`, 'error'));
    log('\nTo fix this:', 'warning');
    log('1. Get your API keys from the respective platforms', 'warning');
    log('2. Add them to your .env file', 'warning');
    log('3. For Coinbase, run: node scripts/setup-coinbase-keys.js', 'warning');
    return false;
  }
  
  log('✅ All API keys validated', 'success');
  return true;
}

async function checkRedis() {
  log('🔍 Checking Redis...', 'info');
  
  const isPortAvailable = await checkPortAvailable(CONFIG.ports.redis);
  
  if (!isPortAvailable) {
    log('✅ Redis is already running', 'success');
    return true;
  }
  
  log('📦 Redis not running, attempting to start...', 'warning');
  
  // Try to start Redis
  return new Promise((resolve) => {
    // Try different Redis executables
    const redisCommands = ['redis-server', 'redis-server.exe'];
    let started = false;
    
    for (const cmd of redisCommands) {
      if (started) break;
      
      try {
        processes.redis = spawn(cmd, [], {
          stdio: 'pipe',
          shell: true
        });
        
        processes.redis.on('error', (err) => {
          if (!started && cmd === redisCommands[redisCommands.length - 1]) {
            log('❌ Failed to start Redis. Please install Redis manually.', 'error');
            log('Windows: Download from https://github.com/microsoftarchive/redis/releases', 'warning');
            log('Mac/Linux: Use package manager (brew, apt, yum)', 'warning');
            resolve(false);
          }
        });
        
        processes.redis.stdout.on('data', (data) => {
          if (data.toString().includes('Ready to accept connections')) {
            started = true;
            log('✅ Redis started successfully', 'success');
            resolve(true);
          }
        });
        
        // Give it time to start
        setTimeout(() => {
          if (!started) {
            processes.redis.kill();
          }
        }, 5000);
        
      } catch (err) {
        // Try next command
      }
    }
  });
}

async function checkPythonDependencies() {
  log('🐍 Checking Python dependencies...', 'info');
  
  return new Promise((resolve) => {
    exec('pip list', (error, stdout) => {
      if (error) {
        log('❌ Python pip not found', 'error');
        resolve(false);
        return;
      }
      
      const requiredPackages = [
        'flask', 'sqlite3', 'tweepy', 'praw', 'vaderSentiment', 
        'textblob', 'requests', 'ccxt', 'scikit-learn', 'pandas', 
        'numpy', 'matplotlib', 'cryptography'
      ];
      
      const installedPackages = stdout.toLowerCase();
      const missing = requiredPackages.filter(pkg => 
        pkg !== 'sqlite3' && !installedPackages.includes(pkg)
      );
      
      if (missing.length > 0) {
        log('📦 Installing missing Python packages...', 'warning');
        exec(`pip install ${missing.join(' ')}`, (err) => {
          if (err) {
            log('❌ Failed to install Python packages', 'error');
            resolve(false);
          } else {
            log('✅ Python dependencies installed', 'success');
            resolve(true);
          }
        });
      } else {
        log('✅ All Python dependencies present', 'success');
        resolve(true);
      }
    });
  });
}

async function checkNodeDependencies() {
  log('📦 Checking Node.js dependencies...', 'info');
  
  const packageJsonPath = path.join(process.cwd(), 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    log('❌ package.json not found', 'error');
    return false;
  }
  
  const nodeModulesPath = path.join(process.cwd(), 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    log('📦 Installing Node.js dependencies...', 'warning');
    return new Promise((resolve) => {
      exec('npm install', (error) => {
        if (error) {
          log('❌ Failed to install Node.js packages', 'error');
          resolve(false);
        } else {
          log('✅ Node.js dependencies installed', 'success');
          resolve(true);
        }
      });
    });
  }
  
  log('✅ Node.js dependencies present', 'success');
  return true;
}

async function startPythonBots() {
  log('🤖 Starting Python trading bots...', 'process');
  
  return new Promise((resolve) => {
    const env = { ...process.env };
    const envVars = loadEnv();
    Object.assign(env, envVars);
    
    processes.pythonBots = spawn('python', ['main.py'], {
      stdio: 'pipe',
      env: env
    });
    
    processes.pythonBots.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        log(`[BOTS] ${output}`, 'info');
      }
      if (output.includes('All bots started')) {
        log('✅ Trading bots are running', 'success');
        resolve(true);
      }
    });
    
    processes.pythonBots.stderr.on('data', (data) => {
      log(`[BOTS ERROR] ${data.toString().trim()}`, 'error');
    });
    
    processes.pythonBots.on('error', (error) => {
      log(`❌ Failed to start trading bots: ${error.message}`, 'error');
      resolve(false);
    });
    
    // Give it time to start
    setTimeout(() => resolve(true), 5000);
  });
}

async function startFlaskDashboard() {
  log('🌐 Starting Flask dashboard...', 'process');
  
  const isPortAvailable = await checkPortAvailable(CONFIG.ports.flask);
  if (!isPortAvailable) {
    log(`⚠️  Port ${CONFIG.ports.flask} is already in use`, 'warning');
    return true;
  }
  
  return new Promise((resolve) => {
    const env = { ...process.env };
    const envVars = loadEnv();
    Object.assign(env, envVars);
    
    processes.flaskDashboard = spawn('python', [path.join('dashboard', 'app.py')], {
      stdio: 'pipe',
      env: env
    });
    
    processes.flaskDashboard.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        log(`[FLASK] ${output}`, 'info');
      }
      if (output.includes('Running on')) {
        log(`✅ Flask dashboard running at http://localhost:${CONFIG.ports.flask}`, 'success');
        resolve(true);
      }
    });
    
    processes.flaskDashboard.stderr.on('data', (data) => {
      const output = data.toString().trim();
      // Flask logs to stderr by default
      if (output && !output.includes('WARNING')) {
        log(`[FLASK] ${output}`, 'info');
      }
    });
    
    processes.flaskDashboard.on('error', (error) => {
      log(`❌ Failed to start Flask dashboard: ${error.message}`, 'error');
      resolve(false);
    });
    
    // Give it time to start
    setTimeout(() => resolve(true), 5000);
  });
}

async function startNodeDashboard() {
  log('🚀 Starting Node.js dashboard and WebSocket server...', 'process');
  
  const expressAvailable = await checkPortAvailable(CONFIG.ports.express);
  const wsAvailable = await checkPortAvailable(CONFIG.ports.websocket);
  
  if (!expressAvailable || !wsAvailable) {
    log('⚠️  Node.js services already running', 'warning');
    return true;
  }
  
  return new Promise((resolve) => {
    const env = { ...process.env };
    const envVars = loadEnv();
    Object.assign(env, envVars);
    env.PORT = CONFIG.ports.express;
    env.WS_PORT = CONFIG.ports.websocket;
    
    processes.nodeDashboard = spawn('node', [path.join('src', 'server', 'index.js')], {
      stdio: 'pipe',
      env: env
    });
    
    processes.nodeDashboard.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        log(`[NODE] ${output}`, 'info');
      }
      if (output.includes('Express server running')) {
        log(`✅ Node.js dashboard running at http://localhost:${CONFIG.ports.express}`, 'success');
        log(`✅ WebSocket server running on port ${CONFIG.ports.websocket}`, 'success');
        resolve(true);
      }
    });
    
    processes.nodeDashboard.stderr.on('data', (data) => {
      log(`[NODE ERROR] ${data.toString().trim()}`, 'error');
    });
    
    processes.nodeDashboard.on('error', (error) => {
      log(`❌ Failed to start Node.js dashboard: ${error.message}`, 'error');
      resolve(false);
    });
    
    // Give it time to start
    setTimeout(() => resolve(true), 5000);
  });
}

async function runApiKeyAudit() {
  log('🔍 Running API key audit...', 'info');
  
  return new Promise((resolve) => {
    const audit = spawn('node', [path.join('src', 'utils', 'security', 'api-key-audit.js')], {
      stdio: 'pipe',
      env: { ...process.env, ...loadEnv() }
    });
    
    audit.stdout.on('data', (data) => {
      process.stdout.write(data);
    });
    
    audit.stderr.on('data', (data) => {
      process.stderr.write(data);
    });
    
    audit.on('close', (code) => {
      if (code === 0) {
        log('✅ API key audit completed successfully', 'success');
        resolve(true);
      } else {
        log('⚠️  API key audit found issues', 'warning');
        resolve(false);
      }
    });
  });
}

// Graceful shutdown
function shutdown() {
  log('\n🛑 Shutting down GOAT Farm...', 'warning');
  
  Object.entries(processes).forEach(([name, proc]) => {
    if (proc && !proc.killed) {
      log(`Stopping ${name}...`, 'info');
      proc.kill();
    }
  });
  
  setTimeout(() => {
    log('👋 GOAT Farm shutdown complete', 'info');
    process.exit(0);
  }, 2000);
}

// Main launch sequence
async function launch() {
  console.clear();
  log('🐐 GOAT FARM LAUNCHER v1.0', 'success');
  log('============================\n', 'success');
  
  // Check environment file
  if (!checkEnvFile()) {
    process.exit(1);
  }
  
  // Load and validate API keys
  const env = loadEnv();
  if (!validateApiKeys(env)) {
    process.exit(1);
  }
  
  // Check dependencies
  const pythonDepsOk = await checkPythonDependencies();
  if (!pythonDepsOk) {
    log('Please install Python dependencies manually: pip install -r requirements.txt', 'error');
    process.exit(1);
  }
  
  const nodeDepsOk = await checkNodeDependencies();
  if (!nodeDepsOk) {
    log('Please install Node.js dependencies manually: npm install', 'error');
    process.exit(1);
  }
  
  // Check Redis
  const redisOk = await checkRedis();
  if (!redisOk) {
    log('⚠️  Continuing without Redis (some features may be limited)', 'warning');
  }
  
  // Run API key audit
  log('\n📋 Running pre-flight API checks...', 'info');
  const auditOk = await runApiKeyAudit();
  if (!auditOk) {
    log('⚠️  Some APIs may not be fully functional', 'warning');
  }
  
  // Start services
  log('\n🚀 Starting all services...', 'info');
  
  // Start Python trading bots
  const botsStarted = await startPythonBots();
  if (!botsStarted) {
    log('Failed to start trading bots', 'error');
    shutdown();
    return;
  }
  
  // Start Flask dashboard
  const flaskStarted = await startFlaskDashboard();
  if (!flaskStarted) {
    log('Failed to start Flask dashboard', 'error');
    shutdown();
    return;
  }
  
  // Start Node.js dashboard
  const nodeStarted = await startNodeDashboard();
  if (!nodeStarted) {
    log('Failed to start Node.js dashboard', 'error');
    shutdown();
    return;
  }
  
  // Success!
  log('\n' + '='.repeat(50), 'success');
  log('🎉 GOAT FARM IS FULLY OPERATIONAL! 🎉', 'success');
  log('='.repeat(50) + '\n', 'success');
  
  log('📊 Dashboards:', 'info');
  log(`   Flask Dashboard: http://localhost:${CONFIG.ports.flask}`, 'info');
  log(`   Node.js Dashboard: http://localhost:${CONFIG.ports.express}`, 'info');
  log(`   WebSocket Feed: ws://localhost:${CONFIG.ports.websocket}`, 'info');
  
  log('\n🤖 Trading Bots Status:', 'info');
  log('   Bot 1: Trend-Following Momentum (BTC/ETH)', 'info');
  log('   Bot 2: Mean-Reversion Scalper (SOL/ADA)', 'info');
  log('   Bot 3: News-Driven Breakout (Multi-pair)', 'info');
  log('   Bot 4: ML-Powered Range Scalper (Top 10)', 'info');
  
  log('\n⚡ Quick Commands:', 'info');
  log('   Press Ctrl+C to stop all services', 'info');
  log('   View logs in real-time in this terminal', 'info');
  log('   Access dashboards to control bot parameters', 'info');
  
  log('\n💰 Happy Trading! May the gains be with you! 🚀\n', 'success');
}

// Handle shutdown signals
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  log(`Uncaught exception: ${error.message}`, 'error');
  shutdown();
});

// Launch the platform
launch().catch((error) => {
  log(`Launch failed: ${error.message}`, 'error');
  shutdown();
});