@echo off
:: ============================================================
::  INSTALADOR DEL SERVICIO WINDOWS - API Centro Japón
::  Ejecutar como ADMINISTRADOR
::  
::  Qué hace este script:
::    1. Verifica que se ejecuta como administrador
::    2. Encuentra Python automáticamente
::    3. Crea/actualiza el entorno virtual e instala dependencias
::    4. Descarga NSSM (herramienta para registrar servicios)
::    5. Registra la API como servicio de Windows
::    6. Abre el puerto 5000 en el firewall
::    7. Inicia el servicio
:: ============================================================

title Instalador Servicio - API Centro Japon
cd /d "%~dp0"

echo.
echo ============================================================
echo   INSTALADOR - API Centro Japon
echo ============================================================
echo.

:: ── Paso 0: Verificar permisos de administrador ─────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Este script necesita ejecutarse como ADMINISTRADOR.
    echo.
    echo   Haz clic derecho en instalar_servicio.bat
    echo   y selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)
echo [OK] Ejecutando como administrador

:: ── Paso 1: Encontrar Python ─────────────────────────────────
set PYTHON=

:: Método 1: Registro de Windows — Python siempre escribe aquí al instalarse,
::           sin importar si está o no en PATH. Es el método más fiable.
echo [..] Buscando Python en el registro de Windows...
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command ^
    "$paths = @(); " ^
    "'HKLM','HKCU' | ForEach-Object { " ^
    "  $base = $_+':SOFTWARE\Python\PythonCore'; " ^
    "  if (Test-Path $base) { " ^
    "    Get-ChildItem $base | ForEach-Object { " ^
    "      $ip = $_.PSPath+'\InstallPath'; " ^
    "      if (Test-Path $ip) { " ^
    "        $v = (Get-ItemProperty $ip -ErrorAction SilentlyContinue).'(default)'; " ^
    "        if ($v -and (Test-Path ($v+'python.exe'))) { $paths += $v+'python.exe' } " ^
    "        $ep = (Get-ItemProperty $ip -ErrorAction SilentlyContinue).ExecutablePath; " ^
    "        if ($ep -and (Test-Path $ep)) { $paths += $ep } " ^
    "      } " ^
    "    } " ^
    "  } " ^
    "}; " ^
    "$paths | Select-Object -First 1"`) do (
    if exist "%%P" ( set PYTHON=%%P & goto :python_found )
)

:: Método 2: Rutas fijas conocidas (por versión)
for %%V in (314 313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :python_found
    )
    if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe"
        goto :python_found
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set "PYTHON=C:\Program Files\Python%%V\python.exe"
        goto :python_found
    )
    if exist "C:\Program Files (x86)\Python%%V\python.exe" (
        set "PYTHON=C:\Program Files (x86)\Python%%V\python.exe"
        goto :python_found
    )
    if exist "D:\Python%%V\python.exe" (
        set "PYTHON=D:\Python%%V\python.exe"
        goto :python_found
    )
)
:: Ruta personalizada detectada en este servidor
if exist "D:\Python\python.exe" (
    set "PYTHON=D:\Python\python.exe"
    goto :python_found
)

:: Método 3: Búsqueda en disco completo (lento pero definitivo)
echo [..] Buscando python.exe en disco (puede tardar unos segundos)...
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command ^
    "Get-ChildItem 'C:\' -Recurse -Filter 'python.exe' -ErrorAction SilentlyContinue ^| " ^
    "Where-Object { $_.FullName -notmatch 'WindowsApps|store' } ^| " ^
    "Select-Object -First 1 -ExpandProperty FullName"`) do (
    if exist "%%P" ( set PYTHON=%%P & goto :python_found )
)

echo [ERROR] No se encontró Python en ninguna ubicación conocida.
echo.
echo         Ve a https://python.org, descarga Python 3.x para Windows
echo         y ejecútalo. NO es necesario marcar "Add to PATH".
echo.
pause
exit /b 1

:python_found
echo [OK] Python encontrado: %PYTHON%

:: ── Paso 2: Crear entorno virtual e instalar dependencias ────
echo.
echo [..] Creando entorno virtual...
if not exist "venv" (
    %PYTHON% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause & exit /b 1
    )
)
echo [OK] Entorno virtual listo

echo [..] Instalando dependencias...
venv\Scripts\pip.exe install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Falló la instalación de dependencias.
    pause & exit /b 1
)
echo [OK] Dependencias instaladas

:: ── Paso 3: Descargar NSSM si no existe ─────────────────────
:: NSSM = Non-Sucking Service Manager, estándar para servicios Windows sin instalar nada
set NSSM_DIR=%~dp0tools\nssm
set NSSM=%NSSM_DIR%\nssm.exe

if exist "%NSSM%" goto :nssm_found

echo.
echo [..] Descargando NSSM...
mkdir "%NSSM_DIR%" >nul 2>&1

:: Descargar con PowerShell (disponible en todos los Windows modernos)
powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%NSSM_DIR%\nssm.zip' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo descargar NSSM. Verifica la conexión a internet.
    echo         Descarga manual: https://nssm.cc/download
    echo         Extrae nssm.exe en: %NSSM_DIR%\nssm.exe
    pause & exit /b 1
)

powershell -Command "Expand-Archive -Path '%NSSM_DIR%\nssm.zip' -DestinationPath '%NSSM_DIR%\extracted' -Force"
:: Copiar el ejecutable de 64 bits
copy /y "%NSSM_DIR%\extracted\nssm-2.24\win64\nssm.exe" "%NSSM%" >nul
del "%NSSM_DIR%\nssm.zip" >nul 2>&1

:nssm_found
echo [OK] NSSM listo: %NSSM%

:: ── Paso 4: Configurar variables del servicio ───────────────
set SERVICE_NAME=CentroJaponAPI
set APP_DIR=%~dp0
:: Quitar barra final si la hay
if "%APP_DIR:~-1%"=="\" set APP_DIR=%APP_DIR:~0,-1%
set PYTHON_EXE=%APP_DIR%\venv\Scripts\python.exe
set APP_SCRIPT=%APP_DIR%\app.py

:: ── Credenciales para acceso a red ──────────────────────────
:: El servicio DEBE correr bajo un usuario real (no SYSTEM) para
:: poder acceder a rutas de red tipo \\servidor\carpeta
echo.
echo ============================================================
echo   CREDENCIALES DE WINDOWS
echo   El servicio necesita un usuario con acceso a la red.
echo   Usa el mismo usuario con el que normalmente inicias sesion.
echo   Formato usuario: NOMBRE_PC\usuario  o solo: usuario
echo ============================================================
echo.
set /p SVC_USER="   Usuario de Windows (ej: Administrador): "
set /p SVC_PASS="   Contraseña: "
echo.

echo.
echo [..] Configurando servicio Windows...

:: Eliminar servicio anterior si existe
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM%" remove %SERVICE_NAME% confirm >nul 2>&1

:: Registrar servicio
"%NSSM%" install %SERVICE_NAME% "%PYTHON_EXE%" "%APP_SCRIPT%"
"%NSSM%" set %SERVICE_NAME% DisplayName "API Centro Japon - Inventario"
"%NSSM%" set %SERVICE_NAME% Description "API REST que expone inventario y precios desde archivos DBF FoxPro"
"%NSSM%" set %SERVICE_NAME% AppDirectory "%APP_DIR%"

:: Correr bajo el usuario real para tener acceso a rutas de red
"%NSSM%" set %SERVICE_NAME% ObjectName ".\%SVC_USER%" "%SVC_PASS%"

:: Inicio automático con Windows
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START

:: Reinicio automático si falla (espera 10seg antes de reintentar)
"%NSSM%" set %SERVICE_NAME% AppRestartDelay 10000

:: Redirigir stdout/stderr a archivos de log
"%NSSM%" set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service_out.log"
"%NSSM%" set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\service_err.log"
"%NSSM%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM%" set %SERVICE_NAME% AppRotateBytes 5242880

echo [OK] Servicio registrado como usuario: %SVC_USER%

:: ── Paso 5: Abrir puerto 5000 en el firewall ────────────────
echo.
echo [..] Abriendo puerto 5000 en el firewall...
netsh advfirewall firewall delete rule name="CentroJaponAPI" >nul 2>&1
netsh advfirewall firewall add rule name="CentroJaponAPI" dir=in action=allow protocol=TCP localport=5000
echo [OK] Puerto 5000 abierto

:: ── Paso 6: Iniciar el servicio ─────────────────────────────
echo.
echo [..] Iniciando servicio...
"%NSSM%" start %SERVICE_NAME%
timeout /t 3 /nobreak >nul

:: Verificar estado
"%NSSM%" status %SERVICE_NAME%

echo.
echo ============================================================
echo   INSTALACION COMPLETADA
echo ============================================================
echo.
echo   Servicio: %SERVICE_NAME%
echo   Estado:   Iniciado y configurado para arrancar con Windows
echo.
echo   Acceder desde otro PC:
echo     http://[IP-DE-ESTE-SERVIDOR]:5000
echo     http://[IP-DE-ESTE-SERVIDOR]:5000/api/inventario
echo.
echo   Ver IP de este servidor:
ipconfig | findstr "IPv4"
echo.
echo   Logs del servicio:
echo     %APP_DIR%\logs\service_out.log
echo     %APP_DIR%\logs\service_err.log
echo.
echo   Para gestionar el servicio:
echo     Iniciar:    sc start %SERVICE_NAME%
echo     Detener:    sc stop %SERVICE_NAME%
echo     Estado:     sc query %SERVICE_NAME%
echo.
pause
