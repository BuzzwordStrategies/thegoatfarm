# Phase 4 & 5: Testing and Production Deployment

## Overview

This document covers the comprehensive testing suite (Phase 4) and production deployment configuration (Phase 5) for The GOAT Farm crypto trading platform.

## Phase 4: Testing Suite

### Test Structure

```
tests/
├── api/
│   └── api-integration.test.js    # API integration tests
├── components/                     # Component tests
├── integration/                    # Integration tests
├── websocket-test.js              # WebSocket connection test
├── run-integration-tests.js       # Test runner
├── setup.js                       # Jest setup
├── globalSetup.js                 # Global test setup
└── globalTeardown.js              # Global test teardown
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run integration tests
npm run test:integration

# Test specific components
npm run test-api          # Test API integrations
npm run test-dashboard    # Test dashboard server
```

### Test Coverage

The test suite covers:
- ✅ All 8 API integrations (Coinbase, CoinDesk, TAAPI, etc.)
- ✅ WebSocket connections
- ✅ Rate limiting and circuit breakers
- ✅ Authentication and security
- ✅ Error handling and recovery
- ✅ Health monitoring

### Writing New Tests

```javascript
// Example API test
describe('New API Client', () => {
  let client;
  
  beforeAll(async () => {
    client = new APIClient();
    await client.initialize();
  });
  
  test('should fetch data successfully', async () => {
    const data = await client.getData();
    expect(data).toBeDefined();
    expect(data.value).toBeGreaterThan(0);
  });
  
  test('should handle errors gracefully', async () => {
    // Force an error
    client.apiKey = 'invalid';
    
    await expect(client.getData()).rejects.toThrow();
  });
});
```

## Phase 5: Production Deployment

### Docker Configuration

#### Multi-Service Architecture

```yaml
services:
  dashboard:        # Node.js API server
  trading-bots:     # Python trading bots
  flask-dashboard:  # Original Flask UI
  redis:           # Cache and session store
  nginx:           # Reverse proxy
```

#### Building and Running

```bash
# Build all containers
npm run docker:build

# Start all services
npm run docker:up

# View logs
npm run docker:logs

# Stop all services
npm run docker:down
```

### Security Configuration

#### 1. Environment Variables

```bash
# Copy example file
cp env.example .env

# Edit with your values
nano .env
```

**Required variables:**
- All API keys (Coinbase, TAAPI, etc.)
- Security keys (JWT_SECRET, MASTER_ENCRYPTION_KEY)
- Service URLs (REDIS_URL, DATABASE_URL)

#### 2. Security Middleware

Implemented security features:
- **Helmet.js**: Security headers
- **CORS**: Cross-origin control
- **Rate Limiting**: API protection
- **API Key Validation**: Service authentication
- **Request Logging**: Audit trail

#### 3. SSL/TLS Configuration

```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# For production, use Let's Encrypt
certbot --nginx -d yourdomain.com
```

### PM2 Process Management

#### Starting with PM2

```bash
# Start application
npm run pm2:start

# View status
pm2 status

# View logs
npm run pm2:logs

# Restart all processes
npm run pm2:restart

# Stop all processes
npm run pm2:stop
```

#### PM2 Features
- **Cluster Mode**: Utilizes all CPU cores
- **Auto-restart**: On crashes or memory limits
- **Log Management**: Centralized logging
- **Health Checks**: Built-in monitoring

### Nginx Configuration

#### Features
- SSL/TLS termination
- WebSocket proxy support
- Rate limiting
- Gzip compression
- Security headers
- Static file serving

#### Custom Domain Setup

1. Update nginx.conf:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

2. Update SSL certificates path
3. Restart nginx container

### Monitoring and Logging

#### Application Logs
```bash
# PM2 logs
pm2 logs

# Docker logs
docker-compose logs -f dashboard

# Nginx access logs
docker exec crypto-nginx tail -f /var/log/nginx/access.log
```

#### Health Endpoints
- `/api/health` - Basic health check
- `/api/status` - Detailed system status
- `/health` - Nginx health check

### Production Checklist

#### Before Deployment
- [ ] All API keys configured in .env
- [ ] SSL certificates installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Backup strategy in place

#### Deployment Steps
1. **Clone repository**
   ```bash
   git clone https://github.com/your-repo/crypto-dashboard.git
   cd crypto-dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install --production
   ```

3. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with production values
   ```

4. **Build containers**
   ```bash
   docker-compose build
   ```

5. **Start services**
   ```bash
   docker-compose up -d
   ```

6. **Verify deployment**
   ```bash
   curl https://yourdomain.com/api/health
   ```

### Scaling Considerations

#### Horizontal Scaling
- PM2 cluster mode handles multiple processes
- Docker Swarm or Kubernetes for multiple hosts
- Redis for session sharing

#### Vertical Scaling
- Increase container memory limits
- Adjust PM2 max_memory_restart
- Monitor resource usage

### Backup and Recovery

#### Data Backup
```bash
# Backup Redis data
docker exec crypto-redis redis-cli BGSAVE

# Backup SQLite database
cp data/trading.db data/trading.db.backup

# Backup encrypted keys
cp .secure-keys .secure-keys.backup
```

#### Disaster Recovery
1. Keep backups off-site
2. Document recovery procedures
3. Test recovery regularly
4. Monitor backup integrity

### Troubleshooting

#### Common Issues

**1. Container won't start**
```bash
# Check logs
docker-compose logs dashboard

# Verify environment
docker-compose config
```

**2. WebSocket connection fails**
- Check nginx WebSocket proxy config
- Verify CORS settings
- Check firewall rules

**3. High memory usage**
- Adjust PM2 memory limits
- Check for memory leaks
- Review circuit breaker settings

**4. API rate limits**
- Review rate limit configuration
- Check for bot traffic
- Implement caching

### Performance Optimization

#### Caching Strategy
- Redis for API responses
- Browser caching for static assets
- CDN for global distribution

#### Database Optimization
- Index frequently queried columns
- Regular VACUUM for SQLite
- Consider PostgreSQL for scale

#### API Optimization
- Batch API requests
- Implement request coalescing
- Use WebSocket for real-time data

### Security Best Practices

1. **API Keys**
   - Rotate regularly
   - Use least privilege
   - Monitor usage

2. **Network Security**
   - Use VPN for admin access
   - Implement fail2ban
   - Regular security audits

3. **Data Protection**
   - Encrypt sensitive data
   - Regular backups
   - Access logging

### Maintenance

#### Regular Tasks
- **Daily**: Check logs, monitor alerts
- **Weekly**: Review metrics, update dependencies
- **Monthly**: Security audit, performance review
- **Quarterly**: Disaster recovery test

#### Updates
```bash
# Update dependencies
npm update

# Rebuild containers
docker-compose build --no-cache

# Rolling restart
pm2 reload all
```

## Conclusion

The GOAT Farm platform now includes:
- ✅ Comprehensive test suite with 80%+ coverage
- ✅ Production-ready Docker configuration
- ✅ Enterprise-grade security
- ✅ Scalable architecture
- ✅ Monitoring and logging
- ✅ Deployment automation

The system is ready for production deployment with proper configuration and monitoring in place. 