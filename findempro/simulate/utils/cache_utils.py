# utils/cache_utils.py
import hashlib
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def make_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments"""
    # Create a string representation of all arguments
    key_parts = []
    
    # Add args
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}_{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}_{type(v).__name__}_{v.id}")
        else:
            key_parts.append(f"{k}_{v}")
    
    # Create hash for long keys
    key_string = "_".join(key_parts)
    if len(key_string) > 200:  # Django cache key limit
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"simulate_{key_string}"


def get_or_set_cache(key: str, callable_func: Callable, timeout: Optional[int] = None) -> Any:
    """Get value from cache or set it using callable function"""
    # Try to get from cache
    cached_value = cache.get(key)
    
    if cached_value is not None:
        logger.debug(f"Cache hit for key: {key}")
        return cached_value
    
    # Generate value
    logger.debug(f"Cache miss for key: {key}")
    value = callable_func()
    
    # Set in cache
    timeout = timeout or getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 3600)
    cache.set(key, value, timeout)
    
    return value


def cache_result(timeout: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = make_cache_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # Get or set cache
            return get_or_set_cache(
                cache_key,
                lambda: func(*args, **kwargs),
                timeout
            )
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache keys matching pattern"""
    if hasattr(cache, '_cache'):  # For local memory cache
        keys_to_delete = [
            key for key in cache._cache.keys()
            if pattern in key
        ]
        for key in keys_to_delete:
            cache.delete(key)
            logger.debug(f"Invalidated cache key: {key}")
    else:
        logger.warning("Cache backend doesn't support pattern deletion")


def cache_simulation_results(simulation_id: int, results: dict, timeout: int = 7200):
    """Cache simulation results with appropriate timeout"""
    key = f"simulation_results_{simulation_id}"
    cache.set(key, results, timeout)
    
    # Also cache individual components for partial access
    for component, data in results.items():
        component_key = f"simulation_{simulation_id}_{component}"
        cache.set(component_key, data, timeout)


def get_cached_simulation_results(simulation_id: int) -> Optional[dict]:
    """Get cached simulation results"""
    key = f"simulation_results_{simulation_id}"
    return cache.get(key)


def clear_simulation_cache(simulation_id: int):
    """Clear all cache related to a simulation"""
    patterns = [
        f"simulation_results_{simulation_id}",
        f"simulation_{simulation_id}_",
        f"charts_{simulation_id}",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


class CacheManager:
    """Manager class for handling complex caching scenarios"""
    
    def __init__(self, prefix: str = "simulate"):
        self.prefix = prefix
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with stats tracking"""
        full_key = f"{self.prefix}_{key}"
        value = cache.get(full_key, default)
        
        if value is not None and value != default:
            self.stats['hits'] += 1
        else:
            self.stats['misses'] += 1
        
        return value
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set value in cache with stats tracking"""
        full_key = f"{self.prefix}_{key}"
        cache.set(full_key, value, timeout)
        self.stats['sets'] += 1
    
    def delete(self, key: str):
        """Delete value from cache with stats tracking"""
        full_key = f"{self.prefix}_{key}"
        cache.delete(full_key)
        self.stats['deletes'] += 1
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total if total > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': hit_rate,
            'total_requests': total
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }