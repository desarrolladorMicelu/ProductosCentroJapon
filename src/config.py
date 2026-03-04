import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')

    DBF_BASE_PATH = os.getenv('DBF_BASE_PATH', '')
    DBF_PATH = os.getenv('DBF_PATH', r'DbfRed 2025-12-09 17;02;02\DbfRed 2025-12-09 17;02;02')
    DBF_ENCODING = os.getenv('DBF_ENCODING', 'latin-1')

    SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', 10))

    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')

    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 10800))
    CACHE_DIR = Path('data/cache')

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    @staticmethod
    def get_latest_dbf_path() -> str:
        base = Config.DBF_BASE_PATH
        if base:
            base_path = Path(base)
            if base_path.exists():
                dbf_folders = sorted(
                    [f for f in base_path.iterdir() if f.is_dir() and f.name.startswith('DbfRed')],
                    key=lambda f: f.name,
                    reverse=True
                )
                if dbf_folders:
                    latest_outer = dbf_folders[0]
                    latest_inner = latest_outer / latest_outer.name
                    resolved = latest_inner if latest_inner.exists() else latest_outer
                    return str(resolved)
        return Config.DBF_PATH

    @staticmethod
    def init_app():
        Config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
