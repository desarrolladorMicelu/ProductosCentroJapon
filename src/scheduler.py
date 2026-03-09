"""
Programador de tareas para sincronización automática
"""
import os
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from src.config import Config
from src.logger import setup_logger
from src.cache_manager import cache_manager

logger = setup_logger(__name__)


class TaskScheduler:
    """Gestor de tareas programadas"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.dbf_reader = None
        self.last_modification_times = {}
    
    def set_dbf_reader(self, dbf_reader):
        self.dbf_reader = dbf_reader
    
    def _check_files_modified(self) -> bool:
        try:
            if self.dbf_reader is None:
                return False

            dbf_path = Path(self.dbf_reader.dbf_path)
            mes_actual = datetime.now().month
            files_to_check = ['Producto.DBF', 'MovMes.DBF', f'MovMes{mes_actual:02d}.DBF']
            has_changes = False

            for filename in files_to_check:
                filepath = dbf_path / filename
                if not filepath.exists():
                    continue
                current_mtime = os.path.getmtime(filepath)
                if filename not in self.last_modification_times:
                    self.last_modification_times[filename] = current_mtime
                    has_changes = True
                elif current_mtime > self.last_modification_times[filename]:
                    logger.info(f"Cambios detectados en {filename}")
                    self.last_modification_times[filename] = current_mtime
                    has_changes = True

            return has_changes

        except Exception as e:
            logger.error(f"Error verificando archivos: {e}")
            return True
    
    def sync_cache(self):
        try:
            if self.dbf_reader is None:
                return

            folder_changed = self.dbf_reader.refresh_path()
            if folder_changed:
                logger.info(f"Nueva carpeta DBF: {self.dbf_reader.dbf_path}")
                self.last_modification_times.clear()

            cache_missing = cache_manager.get('inventario_completo') is None
            if not (folder_changed or self._check_files_modified() or cache_missing):
                return

            inicio = datetime.now()
            inventario = self.dbf_reader.get_inventario_con_precios()
            cache_manager.set('inventario_completo', inventario)
            cache_manager.invalidate('productos_True')
            cache_manager.invalidate('productos_False')
            cache_manager.invalidate('precios')

            logger.info(f"Cache actualizado: {len(inventario)} productos en {(datetime.now() - inicio).total_seconds():.2f}s")

        except Exception as e:
            logger.error(f"Error en sincronizacion: {e}")
    
    def start(self):
        if self.is_running:
            return
        try:
            self.scheduler.add_job(
                func=self.sync_cache,
                trigger=IntervalTrigger(minutes=Config.SYNC_INTERVAL_MINUTES),
                id='sync_cache',
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler iniciado. Intervalo: {Config.SYNC_INTERVAL_MINUTES} minutos")
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
            raise

    def stop(self):
        if not self.is_running:
            return
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler detenido")
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {e}")

    def get_jobs(self):
        return self.scheduler.get_jobs()


task_scheduler = TaskScheduler()
