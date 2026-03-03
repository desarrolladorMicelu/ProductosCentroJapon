"""
Sistema de caché para optimizar el rendimiento
"""
import json
import time
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps
from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)


class CacheManager:
    """Gestor de caché en memoria y disco"""
    
    def __init__(self):
        self.memory_cache = {}
        self.cache_dir = Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._loading = {}  # Para evitar múltiples cargas simultáneas
    
    def _get_cache_file(self, key: str) -> Path:
        """Obtiene la ruta del archivo de caché"""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str, max_age: Optional[int] = None) -> Optional[Any]:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del caché
            max_age: Edad máxima en segundos (None = usar Config.CACHE_TIMEOUT)
            
        Returns:
            Valor cacheado o None si no existe o expiró
        """
        max_age = max_age or Config.CACHE_TIMEOUT
        
        # Intentar obtener de memoria primero
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if time.time() - timestamp < max_age:
                logger.debug(f"Cache hit (memoria): {key}")
                return data
            else:
                del self.memory_cache[key]
        
        # Intentar obtener de disco
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                
                timestamp = cached.get('timestamp', 0)
                if time.time() - timestamp < max_age:
                    data = cached.get('data')
                    # Guardar en memoria para próximas consultas
                    self.memory_cache[key] = (data, timestamp)
                    logger.debug(f"Cache hit (disco): {key}")
                    return data
                else:
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error leyendo caché {key}: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Guarda un valor en el caché
        
        Args:
            key: Clave del caché
            value: Valor a cachear
        """
        timestamp = time.time()
        
        # Guardar en memoria
        self.memory_cache[key] = (value, timestamp)
        
        # Guardar en disco
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'data': value
                }, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache guardado: {key}")
        except Exception as e:
            logger.warning(f"Error guardando caché {key}: {e}")
    
    def invalidate(self, key: str) -> None:
        """
        Invalida una entrada del caché
        
        Args:
            key: Clave del caché a invalidar
        """
        # Eliminar de memoria
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Eliminar de disco
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            cache_file.unlink()
        
        logger.debug(f"Cache invalidado: {key}")
    
    def clear_all(self) -> None:
        """Limpia todo el caché"""
        self.memory_cache.clear()
        
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
        
        logger.info("Caché completamente limpiado")


# Instancia global del gestor de caché
cache_manager = CacheManager()


def cached(key_prefix: str, max_age: Optional[int] = None):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        key_prefix: Prefijo para la clave del caché
        max_age: Edad máxima del caché en segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única basada en función y argumentos
            cache_key = f"{key_prefix}_{func.__name__}"
            
            # Intentar obtener del caché
            cached_result = cache_manager.get(cache_key, max_age)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator
