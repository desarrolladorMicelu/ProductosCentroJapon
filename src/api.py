"""
API RESTful para exponer datos de inventario y precios
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from src.config import Config
from src.logger import setup_logger
from src.dbf_reader import DBFReader
from src.cache_manager import cache_manager, cached

logger = setup_logger(__name__)


def create_app() -> Flask:
    """
    Crea y configura la aplicación Flask
    
    Returns:
        Aplicación Flask configurada
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configurar CORS
    if Config.ALLOWED_ORIGINS == '*':
        CORS(app)
    else:
        origins = [origin.strip() for origin in Config.ALLOWED_ORIGINS.split(',')]
        CORS(app, origins=origins)
    
    # Inicializar directorios
    Config.init_app()
    
    # Inicializar lector DBF
    try:
        dbf_reader = DBFReader()
        logger.info("DBFReader inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando DBFReader: {e}")
        raise
    
    # ==================== RUTAS DE LA API ====================
    
    @app.route('/')
    def index():
        """Endpoint raíz con información de la API"""
        return jsonify({
            'nombre': 'API Centro Japón - Inventario y Precios',
            'version': '1.0.0',
            'descripcion': 'API RESTful para consultar inventario y precios desde FoxPro DBF',
            'endpoints': {
                '/': 'Información de la API',
                '/health': 'Estado de salud del servicio',
                '/api/inventario': 'Inventario completo con disponibilidad y precios',
                '/api/inventario/<codigo>': 'Inventario de un producto específico',
                '/api/productos': 'Lista de productos',
                '/api/precios': 'Precios de venta',
                '/api/cache/clear': 'Limpiar caché (POST)'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/health')
    def health():
        """Endpoint de health check"""
        try:
            # Verificar que se puede leer DBF
            dbf_reader.get_productos(activos_solo=True)
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'dbf_path': str(Config.DBF_PATH),
                'cache_activo': True
            }), 200
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    @app.route('/api/inventario', methods=['GET'])
    def get_inventario():
        """
        Obtiene el inventario completo con disponibilidad y precios
        OPTIMIZADO: Siempre retorna del caché, actualizado cada 30 minutos
        
        Query params:
            - disponible_solo: true/false (solo productos con stock)
            - limit: número máximo de resultados
        """
        try:
            disponible_solo = request.args.get('disponible_solo', 'false').lower() == 'true'
            limit = request.args.get('limit', type=int)
            
            # Obtener del caché (el scheduler lo actualiza cada 30 minutos)
            cache_key = 'inventario_completo'
            inventario = cache_manager.get(cache_key, max_age=10800)  # 3 horas como fallback
            
            # Si no hay caché, retornar mensaje indicando que se está cargando
            if inventario is None:
                logger.warning("Caché vacío, se necesita pre-carga")
                return jsonify({
                    'success': False,
                    'error': 'Datos en proceso de carga. Intente nuevamente en unos segundos.',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'El sistema está sincronizando datos. Por favor espere.'
                }), 503
            
            # Filtrar solo disponibles si se solicita
            if disponible_solo:
                inventario = [item for item in inventario if item['disponible'] > 0]
            
            # Aplicar límite si se especifica
            if limit:
                inventario = inventario[:limit]
            
            return jsonify({
                'success': True,
                'total': len(inventario),
                'timestamp': datetime.now().isoformat(),
                'data': inventario
            }), 200
            
        except Exception as e:
            logger.error(f"Error en /api/inventario: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/inventario/<codigo>', methods=['GET'])
    def get_inventario_producto(codigo: str):
        """
        Obtiene el inventario de un producto específico
        
        Args:
            codigo: Código del producto
        """
        try:
            inventario = dbf_reader.get_inventario_con_precios()
            
            # Buscar el producto
            producto = next((item for item in inventario if item['codigo'] == codigo), None)
            
            if producto:
                return jsonify({
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'data': producto
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Producto {codigo} no encontrado',
                    'timestamp': datetime.now().isoformat()
                }), 404
                
        except Exception as e:
            logger.error(f"Error en /api/inventario/{codigo}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/productos', methods=['GET'])
    def get_productos():
        """
        Obtiene la lista de productos
        
        Query params:
            - activos_solo: true/false
            - limit: número máximo de resultados
        """
        try:
            activos_solo = request.args.get('activos_solo', 'true').lower() == 'true'
            limit = request.args.get('limit', type=int)
            
            # Caché
            cache_key = f'productos_{activos_solo}'
            productos = cache_manager.get(cache_key)
            
            if productos is None:
                productos = dbf_reader.get_productos(activos_solo=activos_solo)
                cache_manager.set(cache_key, productos)
            
            if limit:
                productos = productos[:limit]
            
            return jsonify({
                'success': True,
                'total': len(productos),
                'timestamp': datetime.now().isoformat(),
                'data': productos
            }), 200
            
        except Exception as e:
            logger.error(f"Error en /api/productos: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/precios', methods=['GET'])
    def get_precios():
        """
        Obtiene los precios de venta
        
        Query params:
            - limit: número máximo de resultados
        """
        try:
            limit = request.args.get('limit', type=int)
            
            # Caché
            cache_key = 'precios'
            precios = cache_manager.get(cache_key)
            
            if precios is None:
                precios = dbf_reader.get_precios()
                cache_manager.set(cache_key, precios)
            
            if limit:
                precios = precios[:limit]
            
            return jsonify({
                'success': True,
                'total': len(precios),
                'timestamp': datetime.now().isoformat(),
                'data': precios
            }), 200
            
        except Exception as e:
            logger.error(f"Error en /api/precios: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Limpia el caché de la aplicación"""
        try:
            cache_manager.clear_all()
            logger.info("Caché limpiado manualmente")
            
            return jsonify({
                'success': True,
                'message': 'Caché limpiado correctamente',
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/cache/refresh', methods=['POST'])
    def refresh_cache():
        """
        Fuerza una actualización del caché en background
        Retorna inmediatamente sin esperar
        """
        try:
            from threading import Thread
            
            def actualizar_en_background():
                try:
                    logger.info("Iniciando actualización de caché en background...")
                    inventario = dbf_reader.get_inventario_con_precios()
                    cache_manager.set('inventario_completo', inventario)
                    logger.info(f"✓ Caché actualizado: {len(inventario)} productos")
                except Exception as e:
                    logger.error(f"Error actualizando caché en background: {e}")
            
            # Iniciar actualización en background
            thread = Thread(target=actualizar_en_background)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'message': 'Actualización de caché iniciada en background',
                'timestamp': datetime.now().isoformat()
            }), 202  # 202 Accepted
            
        except Exception as e:
            logger.error(f"Error iniciando actualización de caché: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # ==================== MANEJO DE ERRORES ====================
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint no encontrado',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno del servidor: {error}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    logger.info("Aplicación Flask creada y configurada")
    return app
