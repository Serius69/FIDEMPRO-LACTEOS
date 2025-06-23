# utils/cache_utils.py - VERSIÓN CORREGIDA
import hashlib
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def make_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments - VERSIÓN MEJORADA"""
    # Create a string representation of all arguments
    key_parts = []
    
    # Add args de forma más segura
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{type(arg).__name__}_{arg.id}")
        elif hasattr(arg, '__class__'):
            # Para objetos complejos, usar solo el nombre de la clase y hash
            class_name = arg.__class__.__name__
            try:
                arg_hash = hashlib.md5(str(arg).encode('utf-8')).hexdigest()[:8]
                key_parts.append(f"{class_name}_{arg_hash}")
            except:
                key_parts.append(class_name)
        else:
            # Para valores simples, convertir a string de forma segura
            str_val = str(arg).replace(' ', '_').replace('<', '').replace('>', '')
            key_parts.append(str_val[:50])  # Limitar longitud
    
    # Add kwargs de forma más segura
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}_{type(v).__name__}_{v.id}")
        else:
            # Limpiar valores problemáticos
            v_str = str(v).replace(' ', '_').replace('<', '').replace('>', '')
            key_parts.append(f"{k}_{v_str[:30]}")  # Limitar longitud
    
    # Create hash for long keys
    key_string = "_".join(key_parts)
    
    # Limpiar caracteres problemáticos para memcached
    key_string = key_string.replace(' ', '_').replace('<', '').replace('>', '').replace('(', '').replace(')', '')
    
    if len(key_string) > 200:  # Django cache key limit
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"simulate_{key_string}"


def get_or_set_cache(key: str, callable_func: Callable, timeout: Optional[int] = None) -> Any:
    """Get value from cache or set it using callable function"""
    try:
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
    except Exception as e:
        logger.error(f"Error in cache operation for key {key}: {e}")
        # Si hay error de cache, ejecutar directamente la función
        return callable_func()


def cache_result(timeout: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results - VERSIÓN MEJORADA"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Generate cache key de forma más segura
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
            except Exception as e:
                logger.error(f"Error in cache_result decorator: {e}")
                # Si hay error, ejecutar función directamente
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def simple_cache_result(timeout=300, key_prefix=""):
    """Decorador de cache simplificado que evita claves problemáticas"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Solo cachear si hay un self con cache_manager
                if args and hasattr(args[0], 'cache_manager'):
                    cache_manager = args[0].cache_manager
                    
                    # Crear clave simple
                    func_name = func.__name__
                    
                    # Extraer user_id si está disponible
                    user_id = None
                    if len(args) > 1:
                        user_arg = args[1]
                        if hasattr(user_arg, 'id'):
                            user_id = user_arg.id
                        elif hasattr(user_arg, 'pk'):
                            user_id = user_arg.pk
                    
                    # Crear clave simple
                    if user_id:
                        cache_key = f"{key_prefix}_{func_name}_{user_id}"
                    else:
                        cache_key = f"{key_prefix}_{func_name}_{hash(str(args) + str(kwargs)) % 10000}"
                    
                    # Intentar obtener del cache
                    cached_result = cache_manager.get(cache_key)
                    if cached_result is not None:
                        return cached_result
                    
                    # Ejecutar función
                    result = func(*args, **kwargs)
                    
                    # Guardar en cache
                    cache_manager.set(cache_key, result, timeout)
                    return result
                
                # Si no hay cache manager, ejecutar directamente
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in simple_cache_result for {func.__name__}: {e}")
                # Si hay error de cache, ejecutar función directamente
                return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache keys matching pattern"""
    try:
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
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")


def cache_simulation_results(simulation_id: int, results: dict, timeout: int = 7200):
    """Cache simulation results with appropriate timeout"""
    try:
        key = f"simulation_results_{simulation_id}"
        cache.set(key, results, timeout)
        
        # Also cache individual components for partial access
        for component, data in results.items():
            component_key = f"simulation_{simulation_id}_{component}"
            cache.set(component_key, data, timeout)
    except Exception as e:
        logger.error(f"Error caching simulation results: {e}")


def get_cached_simulation_results(simulation_id: int) -> Optional[dict]:
    """Get cached simulation results"""
    try:
        key = f"simulation_results_{simulation_id}"
        return cache.get(key)
    except Exception as e:
        logger.error(f"Error getting cached simulation results: {e}")
        return None


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
    """Manager class for handling complex caching scenarios - VERSIÓN MEJORADA"""
    
    def __init__(self, prefix: str = "simulate"):
        self.prefix = prefix
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    def _safe_key(self, key: str) -> str:
        """Generar clave segura para cache"""
        full_key = f"{self.prefix}_{key}"
        # Limpiar caracteres problemáticos
        full_key = full_key.replace(' ', '_').replace('<', '').replace('>', '').replace('(', '').replace(')', '')
        # Limitar longitud
        if len(full_key) > 240:
            full_key = f"{self.prefix}_{hashlib.md5(full_key.encode()).hexdigest()}"
        return full_key
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with stats tracking"""
        try:
            safe_key = self._safe_key(key)
            value = cache.get(safe_key, default)
            
            if value is not None and value != default:
                self.stats['hits'] += 1
            else:
                self.stats['misses'] += 1
            
            return value
        except Exception as e:
            logger.error(f"Error getting cache value for key {key}: {e}")
            self.stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set value in cache with stats tracking"""
        try:
            safe_key = self._safe_key(key)
            cache.set(safe_key, value, timeout)
            self.stats['sets'] += 1
        except Exception as e:
            logger.error(f"Error setting cache value for key {key}: {e}")
            self.stats['errors'] += 1
    
    def delete(self, key: str):
        """Delete value from cache with stats tracking"""
        try:
            safe_key = self._safe_key(key)
            cache.delete(safe_key)
            self.stats['deletes'] += 1
        except Exception as e:
            logger.error(f"Error deleting cache value for key {key}: {e}")
            self.stats['errors'] += 1
    
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
            'deletes': 0,
            'errors': 0
        }