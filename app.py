"""
Punto de entrada principal de la aplicación
"""
import sys
from src.api import create_app
from src.scheduler import task_scheduler
from src.config import Config
from src.logger import setup_logger
from src.dbf_reader import DBFReader
from src.cache_manager import cache_manager

logger = setup_logger(__name__)


def preload_cache():
    """
    Pre-carga el caché al iniciar la aplicación
    OPTIMIZADO: Carga rápida con logging de progreso
    """
    try:
        logger.info("=" * 80)
        logger.info("INICIANDO PRE-CARGA DE CACHÉ")
        logger.info("=" * 80)
        
        from datetime import datetime
        inicio = datetime.now()
        
        # Verificar si ya existe caché en disco (de hace menos de 3 horas)
        cache_key = 'inventario_completo'
        inventario_cache = cache_manager.get(cache_key, max_age=10800)  # 3 horas
        
        if inventario_cache is not None:
            logger.info(f"✓ Caché encontrado en disco: {len(inventario_cache)} productos")
            logger.info(f"✓ Pre-carga completada en {(datetime.now() - inicio).total_seconds():.2f}s")
            logger.info("  El scheduler verificará actualizaciones cada 30 minutos")
            logger.info("=" * 80)
            return None  # No necesitamos el dbf_reader si hay caché
        
        logger.info("Caché no encontrado, cargando desde DBF...")
        
        # Crear instancia del lector DBF
        dbf_reader = DBFReader()
        
        # Cargar inventario completo
        logger.info("Leyendo archivos DBF...")
        inventario = dbf_reader.get_inventario_con_precios()
        
        # Guardar en caché
        cache_manager.set(cache_key, inventario)
        
        tiempo_total = (datetime.now() - inicio).total_seconds()
        logger.info(f"✓ Caché cargado: {len(inventario)} productos")
        logger.info(f"✓ Tiempo total: {tiempo_total:.2f}s")
        logger.info("  El scheduler verificará actualizaciones cada 30 minutos")
        logger.info("=" * 80)
        
        return dbf_reader
        
    except Exception as e:
        logger.error(f"Error pre-cargando caché: {e}")
        logger.warning("La aplicación continuará, pero la primera consulta será lenta")
        logger.info("=" * 80)
        return None


def main():
    """Función principal"""
    try:
        logger.info("=" * 80)
        logger.info("Iniciando API Centro Japón - Inventario y Precios")
        logger.info("=" * 80)
        
        # Pre-cargar caché antes de iniciar el servidor
        dbf_reader = preload_cache()
        
        # Crear aplicación Flask
        app = create_app()
        
        # Configurar el scheduler con el lector DBF
        if dbf_reader:
            task_scheduler.set_dbf_reader(dbf_reader)
        
        # Iniciar scheduler de tareas programadas
        task_scheduler.start()
        
        # Información de inicio
        logger.info(f"Servidor iniciando en {Config.HOST}:{Config.PORT}")
        logger.info(f"Ruta DBF: {Config.DBF_PATH}")
        logger.info(f"Sincronización automática cada {Config.SYNC_INTERVAL_MINUTES} minutos")
        logger.info(f"Ambiente: {Config.FLASK_ENV}")
        logger.info("=" * 80)
        
        # Iniciar servidor
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False  # Evitar que el scheduler se duplique
        )
        
    except KeyboardInterrupt:
        logger.info("\nInterrupción por teclado detectada")
        shutdown()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        shutdown()
        sys.exit(1)


def shutdown():
    """Limpieza al cerrar la aplicación"""
    logger.info("Cerrando aplicación...")
    task_scheduler.stop()
    logger.info("Aplicación cerrada correctamente")


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
