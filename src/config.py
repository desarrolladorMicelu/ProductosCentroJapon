"""
Configuración centralizada de la aplicación
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Servidor
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # DBF
    # DBF_BASE_PATH apunta a la carpeta que contiene las subcarpetas DbfRed (ej: "manual por hora")
    # La API siempre usará automáticamente la subcarpeta DbfRed más reciente que haya dentro.
    # Ejemplo: \\192.168.10.10\e\Servidor Delfin\manual por hora
    DBF_BASE_PATH = os.getenv('DBF_BASE_PATH', '')

    # DBF_PATH se usa como fallback si DBF_BASE_PATH no está configurado o no existe
    DBF_PATH = os.getenv('DBF_PATH', r'DbfRed 2025-12-09 17;02;02\DbfRed 2025-12-09 17;02;02')
    DBF_ENCODING = os.getenv('DBF_ENCODING', 'latin-1')

    # Tarea programada: frecuencia con la que se verifica si hay nueva carpeta DbfRed
    # o cambios en los archivos DBF dentro de la carpeta activa.
    # Las carpetas se generan cada ~40 min → con 10 min el peor caso de demora es 9 min.
    # Solo lee DBF reales cuando detecta un cambio; cada tick sin cambios es barato.
    SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', 10))  # 10 minutos por defecto
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')
    
    # Cache
    # Timeout largo para mantener datos disponibles entre actualizaciones de DBF remotos
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 10800))  # 3 horas por defecto
    CACHE_DIR = Path('data/cache')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    @staticmethod
    def get_latest_dbf_path() -> str:
        """
        Devuelve la ruta a la subcarpeta DbfRed más reciente dentro de DBF_BASE_PATH.

        Las carpetas siguen el patrón 'DbfRed YYYY-MM-DD HH;MM;SS'.
        Como el nombre contiene la fecha/hora en formato ISO, ordenar lexicográficamente
        por nombre es equivalente a ordenar cronológicamente.

        Si DBF_BASE_PATH no está configurado o no existe, devuelve DBF_PATH como fallback.
        """
        base = Config.DBF_BASE_PATH
        if base:
            base_path = Path(base)
            if base_path.exists():
                # Listar subcarpetas que empiezan con 'DbfRed'
                dbf_folders = sorted(
                    [f for f in base_path.iterdir() if f.is_dir() and f.name.startswith('DbfRed')],
                    key=lambda f: f.name,
                    reverse=True  # La más reciente queda primera
                )
                if dbf_folders:
                    latest_outer = dbf_folders[0]
                    # Cada carpeta DbfRed contiene dentro otra con el mismo nombre
                    latest_inner = latest_outer / latest_outer.name
                    resolved = latest_inner if latest_inner.exists() else latest_outer
                    return str(resolved)

        # Fallback a ruta fija
        return Config.DBF_PATH

    @staticmethod
    def init_app():
        """Inicializar directorios necesarios"""
        Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
