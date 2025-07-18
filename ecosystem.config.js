module.exports = {
  apps: [
    {
      name: 'crypto-api-server',
      script: './src/server/index.js',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3001
      },
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      log_file: './logs/api-combined.log',
      time: true,
      max_memory_restart: '1G',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      // Graceful shutdown
      kill_timeout: 5000,
      listen_timeout: 3000,
      // Monitoring
      instance_var: 'INSTANCE_ID',
      merge_logs: true,
      // Error handling
      post_update: ['npm install'],
      // Health check
      health_check: {
        interval: 30,
        path: '/api/health',
        port: 3001,
        timeout: 5000,
        max_consecutive_failures: 3
      }
    }
  ],
  
  // Deployment configuration
  deploy: {
    production: {
      user: 'deploy',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:your-username/your-repo.git',
      path: '/var/www/crypto-dashboard',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'npm install pm2 -g'
    }
  }
}; 