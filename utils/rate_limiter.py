"""
Universal rate limiter for all APIs
Implements token bucket algorithm with Redis backend
"""
import time
import redis
from typing import Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import threading

class RateLimiter:
    """Token bucket rate limiter with fallback to in-memory"""
    
    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis
        self.redis_client = None
        self.local_buckets: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        
        if use_redis:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True,
                    socket_connect_timeout=1
                )
                self.redis_client.ping()
            except:
                print("Redis not available, using in-memory rate limiting")
                self.use_redis = False
    
    def _get_bucket_key(self, api_name: str, endpoint: str = "default") -> str:
        """Generate bucket key"""
        return f"rate_limit:{api_name}:{endpoint}"
    
    def _get_bucket(self, key: str, max_tokens: int, refill_rate: float) -> Dict:
        """Get or create token bucket"""
        if self.use_redis and self.redis_client:
            # Redis implementation
            data = self.redis_client.hgetall(key)
            if not data:
                # Initialize bucket
                bucket = {
                    "tokens": max_tokens,
                    "last_refill": time.time(),
                    "max_tokens": max_tokens,
                    "refill_rate": refill_rate
                }
                self.redis_client.hset(key, mapping={
                    k: str(v) for k, v in bucket.items()
                })
                self.redis_client.expire(key, 3600)  # 1 hour expiry
                return bucket
            else:
                return {
                    "tokens": float(data.get("tokens", max_tokens)),
                    "last_refill": float(data.get("last_refill", time.time())),
                    "max_tokens": int(data.get("max_tokens", max_tokens)),
                    "refill_rate": float(data.get("refill_rate", refill_rate))
                }
        else:
            # In-memory implementation
            with self.lock:
                if key not in self.local_buckets:
                    self.local_buckets[key] = {
                        "tokens": max_tokens,
                        "last_refill": time.time(),
                        "max_tokens": max_tokens,
                        "refill_rate": refill_rate
                    }
                return self.local_buckets[key].copy()
    
    def _save_bucket(self, key: str, bucket: Dict):
        """Save bucket state"""
        if self.use_redis and self.redis_client:
            self.redis_client.hset(key, mapping={
                k: str(v) for k, v in bucket.items()
            })
            self.redis_client.expire(key, 3600)
        else:
            with self.lock:
                self.local_buckets[key] = bucket
    
    def consume(self, api_name: str, tokens: int = 1, 
               endpoint: str = "default", max_tokens: int = 10, 
               refill_rate: float = 1.0) -> tuple[bool, float]:
        """
        Consume tokens from bucket
        Returns: (allowed, wait_time_seconds)
        """
        key = self._get_bucket_key(api_name, endpoint)
        
        # Get current bucket state
        bucket = self._get_bucket(key, max_tokens, refill_rate)
        
        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - bucket["last_refill"]
        tokens_to_add = time_passed * bucket["refill_rate"]
        
        bucket["tokens"] = min(
            bucket["max_tokens"],
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_refill"] = now
        
        # Check if we can consume
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            self._save_bucket(key, bucket)
            return True, 0.0
        else:
            # Calculate wait time
            tokens_needed = tokens - bucket["tokens"]
            wait_time = tokens_needed / bucket["refill_rate"]
            self._save_bucket(key, bucket)
            return False, wait_time
    
    def rate_limit(self, api_name: str, max_calls: int = 10, 
                  per_seconds: float = 60.0, cost: int = 1):
        """
        Decorator for rate limiting functions
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Calculate refill rate
                refill_rate = max_calls / per_seconds
                
                # Try to consume tokens
                allowed, wait_time = self.consume(
                    api_name=api_name,
                    tokens=cost,
                    endpoint=func.__name__,
                    max_tokens=max_calls,
                    refill_rate=refill_rate
                )
                
                if allowed:
                    return func(*args, **kwargs)
                else:
                    # Wait and retry
                    if wait_time < 60:  # Don't wait more than 1 minute
                        time.sleep(wait_time)
                        return func(*args, **kwargs)
                    else:
                        raise Exception(f"Rate limit exceeded for {api_name}. Wait {wait_time:.1f}s")
            
            return wrapper
        return decorator
    
    def get_limits_status(self) -> Dict[str, Dict]:
        """Get current status of all rate limits"""
        status = {}
        
        if self.use_redis and self.redis_client:
            # Get all rate limit keys
            keys = self.redis_client.keys("rate_limit:*")
            for key in keys:
                bucket = self.redis_client.hgetall(key)
                if bucket:
                    parts = key.split(":")
                    api_name = parts[1] if len(parts) > 1 else "unknown"
                    endpoint = parts[2] if len(parts) > 2 else "default"
                    
                    status[f"{api_name}:{endpoint}"] = {
                        "tokens": float(bucket.get("tokens", 0)),
                        "max_tokens": int(bucket.get("max_tokens", 0)),
                        "percentage": (float(bucket.get("tokens", 0)) / 
                                     int(bucket.get("max_tokens", 1))) * 100
                    }
        else:
            # In-memory status
            with self.lock:
                for key, bucket in self.local_buckets.items():
                    parts = key.split(":")
                    api_name = parts[1] if len(parts) > 1 else "unknown"
                    endpoint = parts[2] if len(parts) > 2 else "default"
                    
                    status[f"{api_name}:{endpoint}"] = {
                        "tokens": bucket["tokens"],
                        "max_tokens": bucket["max_tokens"],
                        "percentage": (bucket["tokens"] / bucket["max_tokens"]) * 100
                    }
        
        return status

# Global rate limiter instance
rate_limiter = RateLimiter(use_redis=True)

# Convenience decorators for each API
def coinbase_limit(cost: int = 1):
    """Rate limit for Coinbase (30 requests/second)"""
    return rate_limiter.rate_limit("coinbase", max_calls=30, per_seconds=1, cost=cost)

def taapi_limit(cost: int = 1):
    """Rate limit for TAAPI (15 requests/15 seconds)"""
    return rate_limiter.rate_limit("taapi", max_calls=15, per_seconds=15, cost=cost)

def twitter_limit(cost: int = 1):
    """Rate limit for Twitter (100 requests/15 minutes)"""
    return rate_limiter.rate_limit("twitter", max_calls=100, per_seconds=900, cost=cost)

def scrapingbee_limit(cost: int = 1):
    """Rate limit for ScrapingBee (10 concurrent requests)"""
    return rate_limiter.rate_limit("scrapingbee", max_calls=10, per_seconds=1, cost=cost)

def grok_limit(cost: int = 1):
    """Rate limit for Grok (20 requests/minute)"""
    return rate_limiter.rate_limit("grok", max_calls=20, per_seconds=60, cost=cost)

def perplexity_limit(cost: int = 1):
    """Rate limit for Perplexity (20 requests/minute)"""
    return rate_limiter.rate_limit("perplexity", max_calls=20, per_seconds=60, cost=cost)

def anthropic_limit(cost: int = 1):
    """Rate limit for Anthropic (50 requests/minute)"""
    return rate_limiter.rate_limit("anthropic", max_calls=50, per_seconds=60, cost=cost)

def coindesk_limit(cost: int = 1):
    """Rate limit for CoinDesk (100 requests/hour)"""
    return rate_limiter.rate_limit("coindesk", max_calls=100, per_seconds=3600, cost=cost) 