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
        self.dbf_reader = None  # Se asignará desde app.py
        self.last_modification_times = {}  # Guarda las fechas de modificación
    
    def set_dbf_reader(self, dbf_reader):
        """
        Asigna el lector DBF para las tareas de sincronización
        
        Args:
            dbf_reader: Instancia de DBFReader
        """
        self.dbf_reader = dbf_reader
        logger.debug("DBFReader asignado al scheduler")
    
    def _check_files_modified(self) -> bool:
        """
        Verifica si los archivos DBF han sido modificados
        
        Returns:
            True si hay cambios, False si no
        """
        try:
            if self.dbf_reader is None:
                return False
            
            dbf_path = Path(self.dbf_reader.dbf_path)
            
            # Archivos críticos a monitorear
            files_to_check = ['Producto.DBF', 'MovMes.DBF']
            
            # También verificar archivos MovMes por mes
            mes_actual = datetime.now().month
            files_to_check.append(f'MovMes{mes_actual:02d}.DBF')
            
            has_changes = False
            
            for filename in files_to_check:
                filepath = dbf_path / filename
                
                if not filepath.exists():
                    continue
                
                # Obtener fecha de modificación
                current_mtime = os.path.getmtime(filepath)
                
                # Comparar con la última vez
                if filename not in self.last_modification_times:
                    # Primera vez, guardar y marcar como cambio
                    self.last_modification_times[filename] = current_mtime
                    has_changes = True
                    logger.debug(f"Primera verificación de {filename}")
                elif current_mtime > self.last_modification_times[filename]:
                    # Archivo modificado
                    logger.info(f"✓ Cambios detectados en {filename}")
                    logger.info(f"  Anterior: {datetime.fromtimestamp(self.last_modification_times[filename])}")
                    logger.info(f"  Actual: {datetime.fromtimestamp(current_mtime)}")
                    self.last_modification_times[filename] = current_mtime
                    has_changes = True
            
            return has_changes
            
        except Exception as e:
            logger.error(f"Error verificando modificación de archivos: {e}")
            # En caso de error, asumir que hay cambios para forzar actualización
            return True
    
    def sync_cache(self):
        """
        Tarea de sincronización: actualiza el caché en background.

        Orden de verificación:
          1. ¿Appareció una nueva carpeta DbfRed más reciente? → actualizar siempre.
          2. ¿Los archivos DBF dentro de la carpeta actual cambiaron? → actualizar.
          3. Sin cambios → no hacer nada.
        """
        try:
            logger.info("=" * 60)
            logger.info("Verificando actualizaciones de archivos DBF...")

            if self.dbf_reader is None:
                logger.warning("DBFReader no configurado, omitiendo sincronización")
                return

            # --- Paso 1: detectar nueva carpeta DbfRed ---
            folder_changed = self.dbf_reader.refresh_path()
            if folder_changed:
                logger.info(f"★ Nueva carpeta detectada: {self.dbf_reader.dbf_path}")
                # Resetear tiempos guardados para que se re-escaneen los archivos nuevos
                self.last_modification_times.clear()

            # --- Paso 2: detectar cambios en archivos dentro de la carpeta activa ---
            has_changes = folder_changed or self._check_files_modified()

            if not has_changes:
                logger.info("✓ Sin cambios detectados. Caché actual sigue válido.")
                logger.info("=" * 60)
                return

            # --- Paso 3: actualizar caché ---
            logger.info("Actualizando caché con nuevos datos...")
            inicio = datetime.now()

            inventario = self.dbf_reader.get_inventario_con_precios()
            cache_manager.set('inventario_completo', inventario)
            # Invalidar otros cachés dependientes para que se recalculen
            cache_manager.invalidate('productos_True')
            cache_manager.invalidate('productos_False')
            cache_manager.invalidate('precios')

            tiempo = (datetime.now() - inicio).total_seconds()
            logger.info(f"✓ Sincronización completada: {len(inventario)} productos actualizados")
            logger.info(f"✓ Tiempo de actualización: {tiempo:.2f}s")
            logger.info(f"✓ Carpeta activa: {self.dbf_reader.dbf_path}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error en sincronización programada: {e}")
            logger.error("El caché anterior sigue disponible para consultas")
            logger.info("=" * 60)
    
    def start(self):
        """Inicia el programador de tareas"""
        if self.is_running:
            logger.warning("El scheduler ya está en ejecución")
            return
        
        try:
            # Agregar tarea de sincronización
            self.scheduler.add_job(
                func=self.sync_cache,
                trigger=IntervalTrigger(minutes=Config.SYNC_INTERVAL_MINUTES),
                id='sync_cache',
                name='Sincronización de caché',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info(
                f"Scheduler iniciado. Sincronización cada {Config.SYNC_INTERVAL_MINUTES} minutos"
            )
            
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
            raise
    
    def stop(self):
        """Detiene el programador de tareas"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler detenido")
            
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {e}")
    
    def get_jobs(self):
        """Obtiene la lista de trabajos programados"""
        return self.scheduler.get_jobs()


# Instancia global del scheduler
task_scheduler = TaskScheduler()
