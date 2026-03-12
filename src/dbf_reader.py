"""
Módulo para lectura y procesamiento de archivos DBF de FoxPro
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from dbfread import DBF
from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)


class DBFReader:
    """Lector de archivos DBF con manejo de errores y validaciones"""
    
    def __init__(self, dbf_path: Optional[str] = None):
        self.encoding = Config.DBF_ENCODING
        resolved = dbf_path or Config.get_latest_dbf_path()
        self.dbf_path = Path(resolved)

        if not self.dbf_path.exists():
            raise FileNotFoundError(f"Ruta DBF no encontrada: {self.dbf_path}")

        logger.info(f"DBFReader inicializado con ruta: {self.dbf_path}")

    def refresh_path(self) -> bool:
        """
        Verifica si hay una carpeta DBF más reciente y cambia a ella
        SOLO si los archivos críticos existen y están completos
        
        Returns:
            True si cambió a una carpeta nueva, False si no
        """
        new_path = Path(Config.get_latest_dbf_path())
        
        if new_path != self.dbf_path:
            # Verificar que los archivos críticos existen y tienen tamaño > 0
            producto_file = new_path / 'Producto.DBF'
            movmes_file = new_path / 'MovMes.DBF'
            mes_actual = datetime.now().month
            movmes_mes = new_path / f'MovMes{mes_actual:02d}.DBF'
            
            # Verificar existencia y tamaño
            archivos_ok = (
                producto_file.exists() and producto_file.stat().st_size > 1000 and
                (movmes_file.exists() and movmes_file.stat().st_size > 1000 or
                 movmes_mes.exists() and movmes_mes.stat().st_size > 1000)
            )
            
            if archivos_ok:
                logger.info(f"✓ Nueva carpeta DBF lista: {new_path}")
                logger.info(f"  Cambiando de: {self.dbf_path}")
                self.dbf_path = new_path
                return True
            else:
                logger.warning(f"⚠ Nueva carpeta detectada pero archivos NO están listos: {new_path}")
                logger.info(f"  Manteniendo carpeta actual: {self.dbf_path}")
                logger.info(f"  (Los archivos se están copiando, se intentará en próxima sincronización)")
                return False
        
        return False
    
    def _sanitize_value(self, value: Any) -> Any:
        """
        Limpia y convierte valores a tipos JSON-serializables
        
        Args:
            value: Valor a sanitizar
            
        Returns:
            Valor sanitizado
        """
        if value is None:
            return None
        
        # Convertir bytes a string
        if isinstance(value, bytes):
            try:
                return value.decode(self.encoding).strip()
            except:
                return None
        
        # Convertir datetime y date a string ISO
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        # Convertir Decimal a float
        if isinstance(value, Decimal):
            return float(value)
        
        # Limpiar strings
        if isinstance(value, str):
            value = value.strip()
            # Remover caracteres nulos y de control
            value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
            return value if value else None
        
        # Convertir booleanos
        if isinstance(value, bool):
            return value
        
        # Números
        if isinstance(value, (int, float)):
            return value
        
        return str(value)
    
    def _read_dbf_file(self, filename: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lee un archivo DBF y retorna los registros
        
        Args:
            filename: Nombre del archivo DBF
            limit: Límite de registros a leer (opcional)
            
        Returns:
            Lista de registros como diccionarios
        """
        filepath = self.dbf_path / filename
        
        if not filepath.exists():
            logger.error(f"Archivo no encontrado: {filepath}")
            raise FileNotFoundError(f"Archivo no encontrado: {filename}")
        
        try:
            table = DBF(
                str(filepath),
                encoding=self.encoding,
                ignore_missing_memofile=True,
                load=True
            )
            
            records = []
            for i, record in enumerate(table):
                if limit and i >= limit:
                    break
                
                # Sanitizar todos los valores del registro
                clean_record = {
                    key: self._sanitize_value(value)
                    for key, value in record.items()
                    if not key.startswith('_')  # Ignorar campos internos
                }
                records.append(clean_record)
            
            logger.info(f"Leídos {len(records)} registros de {filename}")
            return records
            
        except Exception as e:
            logger.error(f"Error leyendo {filename}: {str(e)}")
            raise
    
    def get_productos(self, activos_solo: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de productos
        
        Args:
            activos_solo: Si True, solo retorna productos activos
            
        Returns:
            Lista de productos
        """
        try:
            productos = self._read_dbf_file('Producto.DBF')
            
            if activos_solo:
                productos = [p for p in productos if p.get('ACTIVO') is True]
            
            logger.info(f"Obtenidos {len(productos)} productos")
            return productos
            
        except Exception as e:
            logger.error(f"Error obteniendo productos: {str(e)}")
            raise
    
    def get_inventario(self) -> List[Dict[str, Any]]:
        """
        Obtiene el inventario actual desde MovMes
        
        Returns:
            Lista de inventario con disponibilidad
        """
        try:
            # Leer MovMes (movimientos mensuales)
            movimientos = self._read_dbf_file('MovMes.DBF')
            
            # Leer productos para enriquecer la información
            productos = self._read_dbf_file('Producto.DBF')
            productos_dict = {p['COD_PRODUC']: p for p in productos}
            
            inventario = []
            for mov in movimientos:
                cod_producto = mov.get('COD_PRODUC', '').strip()
                
                if not cod_producto:
                    continue
                
                producto = productos_dict.get(cod_producto, {})
                
                # Usar ACTUALMES que ya tiene el stock actual calculado
                disponible = mov.get('ACTUALMES', 0) or 0
                inicial = mov.get('INICIALMES', 0) or 0
                entradas = mov.get('ENTRADASME', 0) or 0
                salidas = mov.get('SALIDASMES', 0) or 0
                
                # Solo incluir productos con inventario o activos
                if disponible > 0 or producto.get('ACTIVO'):
                    inventario.append({
                        'codigo': cod_producto,
                        'descripcion': producto.get('DESCRIPCIO', ''),
                        'referencia': producto.get('REFERENCIA', ''),
                        'disponible': disponible,
                        'inicial_mes': inicial,
                        'entradas_mes': entradas,
                        'salidas_mes': salidas,
                        'centro_costo': mov.get('CEN_COSTO', ''),
                        'fecha_actualizacion': mov.get('FECHA', ''),
                        'activo': producto.get('ACTIVO', False)
                    })
            
            logger.info(f"Obtenido inventario de {len(inventario)} productos")
            return inventario
            
        except Exception as e:
            logger.error(f"Error obteniendo inventario: {str(e)}")
            raise
    
    def get_precios(self) -> List[Dict[str, Any]]:
        """
        Obtiene los precios de venta de los productos
        
        Returns:
            Lista de productos con sus precios
        """
        try:
            productos = self._read_dbf_file('Producto.DBF')
            
            precios = []
            for producto in productos:
                if not producto.get('ACTIVO'):
                    continue
                
                precios.append({
                    'codigo': producto.get('COD_PRODUC', ''),
                    'descripcion': producto.get('DESCRIPCIO', ''),
                    'referencia': producto.get('REFERENCIA', ''),
                    'costo': producto.get('COSTO', 0),
                    'costo_promedio': producto.get('COSTO_PROM', 0),
                    'precio_venta_1': producto.get('VENTA1', 0),
                    'precio_venta_2': producto.get('VENTA2', 0),
                    'precio_venta_3': producto.get('VENTA3', 0),
                    'precio_venta_4': producto.get('VENTA4', 0),
                    'precio_venta_5': producto.get('VENTA5', 0),
                    'iva': producto.get('IVA', 0),
                    'utilidad_porcentaje': producto.get('UTILIDAD', 0),
                    'activo': producto.get('ACTIVO', False)
                })
            
            logger.info(f"Obtenidos precios de {len(precios)} productos")
            return precios
            
        except Exception as e:
            logger.error(f"Error obteniendo precios: {str(e)}")
            raise
    
    def get_inventario_con_precios(self) -> List[Dict[str, Any]]:
        """
        Obtiene inventario combinado con precios (endpoint principal)
        OPTIMIZADO: Solo lee el mes actual de MovMes
        
        Returns:
            Lista completa de inventario con disponibilidad y precios
        """
        try:
            from datetime import datetime
            
            logger.info("Iniciando lectura de inventario con precios...")
            inicio = datetime.now()
            
            # Leer solo productos activos
            productos = self._read_dbf_file('Producto.DBF')
            logger.info(f"Productos leídos: {len(productos)} en {(datetime.now() - inicio).total_seconds():.2f}s")
            
            productos_dict = {p['COD_PRODUC']: p for p in productos if p.get('ACTIVO')}
            
            # Determinar archivo MovMes del mes actual
            mes_actual = datetime.now().month
            archivo_movmes = f'MovMes{mes_actual:02d}.DBF'
            
            logger.info(f"Leyendo inventario del mes actual: {archivo_movmes}")
            
            # Verificar si existe el archivo del mes
            movmes_path = self.dbf_path / archivo_movmes
            if not movmes_path.exists():
                logger.warning(f"Archivo {archivo_movmes} no encontrado, usando MovMes.DBF")
                archivo_movmes = 'MovMes.DBF'
            
            # Diccionario para acumular disponibilidad por producto
            disponibilidad = {}
            
            try:
                movimientos = self._read_dbf_file(archivo_movmes)
                logger.info(f"Registros de movimientos leídos: {len(movimientos)}")
                
                for mov in movimientos:
                    cod = mov.get('COD_PRODUC', '').strip()
                    if cod and cod in productos_dict:
                        # Usar ACTUALMES que ya tiene el stock actual calculado
                        actual = mov.get('ACTUALMES', 0) or 0
                        
                        if cod not in disponibilidad:
                            disponibilidad[cod] = 0
                        disponibilidad[cod] += actual
                
                logger.info(f"Productos con movimientos: {len(disponibilidad)}")
                
            except Exception as e:
                logger.error(f"Error leyendo {archivo_movmes}: {e}")
                # Continuar sin movimientos
            
            # Construir resultado
            resultado = []
            for cod_producto, producto in productos_dict.items():
                resultado.append({
                    # Campos principales usados por integraciones existentes
                    'codigo': cod_producto,
                    'descripcion': producto.get('DESCRIPCIO', ''),
                    'referencia': producto.get('REFERENCIA', ''),
                    'disponible': disponibilidad.get(cod_producto, 0),
                    'costo': producto.get('COSTO', 0),
                    'costo_promedio': producto.get('COSTO_PROM', 0),
                    'precio_venta_1': producto.get('VENTA1', 0),
                    'precio_venta_2': producto.get('VENTA2', 0),
                    'precio_venta_3': producto.get('VENTA3', 0),
                    'precio_venta_4': producto.get('VENTA4', 0),
                    'precio_venta_5': producto.get('VENTA5', 0),
                    'iva': producto.get('IVA', 0),
                    'inc': producto.get('INC', 0),
                    'utilidad_porcentaje': producto.get('UTILIDAD', 0),
                    'ret_fuente': producto.get('RET_FUENTE', ''),

                    # Campos adicionales del maestro de productos
                    'cod_largo': producto.get('COD_LARGO', ''),
                    'cod_invent': producto.get('COD_INVENT', ''),
                    'factor': producto.get('FACTOR', 0),
                    'sugerido': producto.get('SUGERIDO', 0),
                    'rotacion': producto.get('ROTACION', 0),
                    'divisor': producto.get('DIVISOR', 0),
                    'medida': producto.get('MEDIDA', ''),
                    'atributo1': producto.get('ATRIBUTO1', ''),
                    'atributo2': producto.get('ATRIBUTO2', ''),
                    'decimal': producto.get('DECIMAL', False),
                    'touch': producto.get('TOUCH', False),
                    'und_empaque': producto.get('UND_EMPAQU', 0),
                    'porcen1': producto.get('PORCEN1', 0),
                    'porcen2': producto.get('PORCEN2', 0),
                    'porcen3': producto.get('PORCEN3', 0),
                    'porcen4': producto.get('PORCEN4', 0),
                    'porcen5': producto.get('PORCEN5', 0),
                    'impuesto': producto.get('IMPUESTO', 0),
                    'tipo_impto': producto.get('TIPO_IMPTO', 0),
                    'inventario': producto.get('INVENTARIO', False),
                    'gravado': producto.get('GRAVADO', 0),
                    'obligatori': producto.get('OBLIGATORI', False),
                    'biencubier': producto.get('BIENCUBIER', False),
                    'compuesto': producto.get('COMPUESTO', False),
                    'fecha_ingreso': producto.get('FECHA_ING', ''),
                    'categoria': producto.get('CATEGORIA', 0),
                    'es_gratuito': producto.get('ESGRATUITO', False),
                    'activo': True
                })
            
            logger.info(f"Obtenido inventario completo de {len(resultado)} productos")
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo inventario con precios: {str(e)}")
            raise
