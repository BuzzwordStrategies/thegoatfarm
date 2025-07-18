const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

const securityMiddleware = {
  // Helmet for security headers
  helmet: helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        scriptSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdn.tailwindcss.com"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'", "wss:", "ws:", "https:"],
        fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
      },
    },
    crossOriginEmbedderPolicy: false,
  }),
  
  // CORS configuration
  cors: cors({
    origin: (origin, callback) => {
      const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:3001'];
      
      // Allow requests with no origin (like mobile apps or curl)
      if (!origin) return callback(null, true);
      
      if (allowedOrigins.indexOf(origin) !== -1) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
    optionsSuccessStatus: 200,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key']
  }),
  
  // Rate limiting
  rateLimiter: rateLimit({
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
    message: 'Too many requests from this IP, please try again later.',
    standardHeaders: true,
    legacyHeaders: false,
    // Skip rate limiting for health checks
    skip: (req) => req.path === '/api/health'
  }),
  
  // API-specific rate limiter (stricter)
  apiRateLimiter: rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 20, // 20 requests per minute
    message: 'API rate limit exceeded. Please slow down your requests.',
    standardHeaders: true,
    legacyHeaders: false,
  }),
  
  // API Key validation middleware
  validateAPIKey: (req, res, next) => {
    // Skip validation for public endpoints
    const publicEndpoints = ['/api/health', '/api/status', '/', '/favicon.ico'];
    if (publicEndpoints.includes(req.path)) {
      return next();
    }
    
    const apiKey = req.headers['x-api-key'];
    
    if (!apiKey) {
      return res.status(401).json({ 
        error: 'API key required',
        message: 'Please include your API key in the x-api-key header'
      });
    }
    
    // Validate API key
    const validApiKeys = [
      process.env.INTERNAL_API_KEY,
      // Add more API keys as needed
    ].filter(Boolean);
    
    if (!validApiKeys.includes(apiKey)) {
      return res.status(403).json({ 
        error: 'Invalid API key',
        message: 'The provided API key is not valid'
      });
    }
    
    // Add user info to request
    req.apiKeyUsed = apiKey;
    next();
  },
  
  // Request logging
  requestLogger: (req, res, next) => {
    const start = Date.now();
    const requestId = Math.random().toString(36).substring(7);
    
    // Add request ID to request and response
    req.requestId = requestId;
    res.setHeader('X-Request-ID', requestId);
    
    // Log request
    console.log({
      type: 'request',
      requestId,
      method: req.method,
      url: req.url,
      ip: req.ip || req.connection.remoteAddress,
      userAgent: req.get('user-agent'),
      timestamp: new Date().toISOString()
    });
    
    res.on('finish', () => {
      const duration = Date.now() - start;
      
      console.log({
        type: 'response',
        requestId,
        method: req.method,
        url: req.url,
        status: res.statusCode,
        duration: `${duration}ms`,
        contentLength: res.get('content-length'),
        timestamp: new Date().toISOString()
      });
    });
    
    next();
  },
  
  // Error handler middleware
  errorHandler: (err, req, res, next) => {
    const requestId = req.requestId || 'unknown';
    
    console.error({
      type: 'error',
      requestId,
      error: err.message,
      stack: err.stack,
      url: req.url,
      method: req.method,
      timestamp: new Date().toISOString()
    });
    
    // Don't leak error details in production
    const isDevelopment = process.env.NODE_ENV === 'development';
    
    res.status(err.status || 500).json({
      error: isDevelopment ? err.message : 'Internal Server Error',
      requestId,
      ...(isDevelopment && { stack: err.stack })
    });
  },
  
  // Security headers for WebSocket
  websocketSecurity: (req, socket, head) => {
    const origin = req.headers.origin;
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:3001'];
    
    if (origin && !allowedOrigins.includes(origin)) {
      socket.write('HTTP/1.1 403 Forbidden\r\n\r\n');
      socket.destroy();
      return false;
    }
    
    return true;
  }
};

module.exports = securityMiddleware; 