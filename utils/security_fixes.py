"""
Security fixes and middleware for The GOAT Farm
Implements input sanitization, XSS protection, and security headers
"""
from flask import request, abort, redirect, make_response
from functools import wraps
import re
import html
from typing import Any, Dict

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and SQL injection"""
    if not text:
        return text
    
    # HTML escape
    text = html.escape(text)
    
    # Remove potential SQL injection patterns
    sql_patterns = [
        r'(DROP|INSERT|UPDATE|DELETE|SELECT|UNION|CREATE|ALTER|EXEC|EXECUTE)',
        r'(-{2}|\/\*|\*\/)',  # SQL comments
        r'(;|\||&&)',  # Command chaining
        r'(<script|<\/script|javascript:|onerror=|onload=)',  # XSS
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            abort(400, "Invalid input detected")
    
    return text

def sanitize_decorator(func):
    """Decorator to sanitize all form inputs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitize form data
        if request.form:
            for key in request.form:
                value = request.form[key]
                sanitize_input(value)
        
        # Sanitize JSON data
        if request.is_json:
            data = request.get_json()
            _sanitize_dict(data)
        
        return func(*args, **kwargs)
    return wrapper

def _sanitize_dict(data: Dict[str, Any]):
    """Recursively sanitize dictionary values"""
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = sanitize_input(value)
        elif isinstance(value, dict):
            _sanitize_dict(value)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str):
                    value[i] = sanitize_input(item)
                elif isinstance(item, dict):
                    _sanitize_dict(item)

def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

def setup_security(app):
    """Setup security middleware for Flask app"""
    
    @app.before_request
    def enforce_https():
        """Enforce HTTPS in production"""
        if app.config.get('ENV') == 'production' and not request.is_secure:
            return redirect(request.url.replace('http://', 'https://'))
    
    @app.after_request
    def apply_security_headers(response):
        """Apply security headers to all responses"""
        return add_security_headers(response)
    
    # Configure session cookie security
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600  # 1 hour
    )

def validate_api_key(key: str) -> bool:
    """Validate API key format"""
    # Coinbase CDP key format
    if key.startswith('organizations/'):
        pattern = r'^organizations/[a-f0-9-]+/apiKeys/[a-f0-9-]+$'
        return bool(re.match(pattern, key))
    
    # Generic API key validation (alphanumeric + common chars)
    pattern = r'^[a-zA-Z0-9_\-\.]+$'
    return bool(re.match(pattern, key)) and len(key) >= 16

def validate_crypto_address(address: str, currency: str) -> bool:
    """Validate cryptocurrency address format"""
    patterns = {
        'BTC': r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$',
        'ETH': r'^0x[a-fA-F0-9]{40}$',
        'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
        'ADA': r'^addr1[a-z0-9]+$'
    }
    
    pattern = patterns.get(currency.upper())
    if pattern:
        return bool(re.match(pattern, address))
    return False

def rate_limit_decorator(max_calls: int = 10, window: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use the rate limiter from utils
            from utils.rate_limiter import rate_limiter
            
            # Create a unique key for this endpoint/user
            if hasattr(request, 'endpoint'):
                key = f"{request.endpoint}:{request.remote_addr}"
            else:
                key = f"{func.__name__}:{request.remote_addr}"
            
            allowed, wait_time = rate_limiter.consume(
                api_name='webapp',
                endpoint=key,
                max_tokens=max_calls,
                refill_rate=max_calls/window
            )
            
            if not allowed:
                abort(429, f"Rate limit exceeded. Try again in {int(wait_time)} seconds")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def secure_password_hash(password: str) -> str:
    """Generate secure password hash"""
    from werkzeug.security import generate_password_hash
    # Use strong hashing with salt rounds
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    import hmac
    return hmac.compare_digest(val1, val2)

# CORS configuration for API endpoints
def setup_cors(app):
    """Setup CORS with security in mind"""
    from flask_cors import CORS
    
    cors_config = {
        'origins': [
            'http://localhost:3000',
            'http://localhost:5000',
            'https://yourdomain.com'  # Replace with actual domain
        ],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
        'supports_credentials': True,
        'max_age': 3600
    }
    
    CORS(app, resources={r"/api/*": cors_config}) 