# API Centro Japón - Inventario y Precios

API RESTful profesional para exponer datos de inventario y precios desde archivos FoxPro DBF.

## 🎯 Características

- ✅ Lectura eficiente de archivos DBF de FoxPro
- ✅ API RESTful con endpoints bien definidos
- ✅ Sistema de caché multinivel (memoria + disco) - **OPTIMIZADO**
- ✅ **Respuestas instantáneas (< 100ms)**
- ✅ Sincronización automática programable
- ✅ Logging completo y estructurado
- ✅ Manejo robusto de errores
- ✅ Validación y limpieza de datos
- ✅ CORS configurable
- ✅ Health checks
- ✅ **Caché persistente entre reinicios**
- ✅ **Actualización en background sin bloqueos**
- ✅ Optimizado para rendimiento

## 📋 Requisitos

- Python 3.8 o superior
- Acceso a los archivos DBF de FoxPro

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd centro-japon-api
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo:

```bash
copy .env.example .env
```

Editar `.env` con tus configuraciones:

```env
DBF_PATH=ruta\a\tus\archivos\dbf
SYNC_INTERVAL_MINUTES=15
PORT=5000
```

## 🏃 Ejecución

### Modo desarrollo

```bash
python app.py
```

### Modo producción

Para producción, se recomienda usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "src.api:create_app()"
```

## 📡 Endpoints de la API

### Información general

```
GET /
```

Retorna información sobre la API y endpoints disponibles.

### Health Check

```
GET /health
```

Verifica el estado de salud del servicio.

**Respuesta exitosa:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-14T10:30:00",
  "dbf_path": "ruta/a/dbf",
  "cache_activo": true
}
```

### Inventario completo

```
GET /api/inventario
```

Obtiene el inventario completo con disponibilidad y precios.

**Query params:**
- `disponible_solo=true` - Solo productos con stock
- `limit=100` - Limitar resultados

**Respuesta:**
```json
{
  "success": true,
  "total": 1500,
  "timestamp": "2025-02-14T10:30:00",
  "data": [
    {
      "codigo": "000001",
      "descripcion": "PRODUCTO EJEMPLO",
      "referencia": "REF001",
      "disponible": 50,
      "costo": 10000,
      "costo_promedio": 9500,
      "precio_venta_1": 15000,
      "precio_venta_2": 16000,
      "precio_venta_3": 17000,
      "iva": 19,
      "utilidad_porcentaje": 50,
      "activo": true
    }
  ]
}
```

### Inventario por producto

```
GET /api/inventario/<codigo>
```

Obtiene el inventario de un producto específico.

**Ejemplo:**
```
GET /api/inventario/000001
```

### Lista de productos

```
GET /api/productos
```

Obtiene la lista completa de productos.

**Query params:**
- `activos_solo=true` - Solo productos activos (default)
- `limit=100` - Limitar resultados

### Precios de venta

```
GET /api/precios
```

Obtiene los precios de venta de todos los productos.

**Query params:**
- `limit=100` - Limitar resultados

### Limpiar caché

```
POST /api/cache/clear
```

Limpia el caché manualmente para forzar actualización de datos.

### Actualizar caché en background (NUEVO)

```
POST /api/cache/refresh
```

Inicia una actualización del caché en background sin bloquear.
Retorna inmediatamente (202 Accepted) mientras actualiza los datos.

## ⚙️ Configuración

### Variables de entorno (.env)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DBF_PATH` | Ruta a los archivos DBF | - |
| `SYNC_INTERVAL_MINUTES` | Intervalo de sincronización | 30 |
| `PORT` | Puerto del servidor | 5000 |
| `HOST` | Host del servidor | 0.0.0.0 |
| `FLASK_ENV` | Ambiente (production/development) | production |
| `FLASK_DEBUG` | Modo debug | False |
| `SECRET_KEY` | Clave secreta de Flask | - |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | * |
| `DBF_ENCODING` | Encoding de archivos DBF | latin-1 |
| `CACHE_TIMEOUT` | Timeout de caché (segundos) | 10800 (3 horas) |
| `LOG_LEVEL` | Nivel de logging | INFO |

## 🔧 Arquitectura

```
centro-japon-api/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuración centralizada
│   ├── logger.py          # Sistema de logging
│   ├── dbf_reader.py      # Lectura de archivos DBF
│   ├── cache_manager.py   # Gestión de caché
│   ├── api.py             # API Flask
│   └── scheduler.py       # Tareas programadas
├── data/
│   └── cache/             # Caché en disco
├── logs/                  # Archivos de log
├── app.py                 # Punto de entrada
├── requirements.txt       # Dependencias
├── .env                   # Configuración (no versionar)
└── README.md
```

## 🔒 Seguridad

- Validación y sanitización de todos los datos
- Manejo seguro de errores sin exponer información sensible
- CORS configurable
- Logs de auditoría
- Sin exposición de rutas del sistema

## 📊 Rendimiento

- Sistema de caché multinivel (memoria + disco)
- **Respuestas instantáneas: < 100ms**
- **Sincronizado con actualizaciones remotas (cada 2 horas)**
- **Verificación automática cada 30 minutos**
- Caché persistente entre reinicios (3 horas de validez como fallback)
- Lectura optimizada de archivos DBF
- Respuestas JSON comprimidas
- Sincronización programada en background
- **Pre-carga inteligente al iniciar**
- **Actualización en background sin bloqueos**
- **Eficiente: No lee archivos innecesariamente**

### ⚡ Optimizaciones Implementadas

Para garantizar tiempos de respuesta instantáneos sincronizados con actualizaciones remotas:

1. **Actualización inteligente cada 30 minutos**: El scheduler verifica y actualiza el caché en background
2. **Pre-carga al iniciar**: El caché se carga automáticamente al iniciar el servidor
3. **Caché persistente**: Se guarda en disco y sobrevive reinicios
4. **Sin bloqueos**: Las consultas NUNCA esperan a leer DBF
5. **Sincronizado con remoto**: Configurado para archivos DBF que se actualizan cada 2 horas

**Balance perfecto:** Respuestas instantáneas + Sincronización eficiente con datos remotos

**Ver más detalles en:** [OPTIMIZACIONES.md](OPTIMIZACIONES.md)

## 🐛 Troubleshooting

### Error: "Ruta DBF no encontrada"

Verificar que la variable `DBF_PATH` en `.env` apunte correctamente a los archivos DBF.

### Error: "pip no se reconoce"

Asegurarse de tener Python instalado y agregado al PATH del sistema.

### El caché no se actualiza

Llamar manualmente al endpoint `POST /api/cache/clear` o reiniciar el servicio.

### Problemas de encoding

Ajustar la variable `DBF_ENCODING` en `.env` (probar: latin-1, cp850, utf-8).

## 📝 Logs

Los logs se guardan en:
- Consola (stdout)
- Archivo: `logs/app.log`

Niveles de log: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🤝 Soporte

Para problemas o consultas, revisar los logs en `logs/app.log`.

## 📄 Licencia

Proyecto privado - Centro Japón
