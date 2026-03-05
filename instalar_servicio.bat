@echo off
title Instalador Servicio - API Centro Japon
cd /d "%~dp0"

echo.
echo ============================================================
echo   INSTALADOR - API Centro Japon
echo ============================================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecutar como ADMINISTRADOR: clic derecho - Ejecutar como administrador
    pause
    exit /b 1
)
echo [OK] Ejecutando como administrador

set PYTHON=
echo [..] Buscando Python...
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

for %%V in (314 313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" & goto :python_found
    )
    if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe" & goto :python_found
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set "PYTHON=C:\Program Files\Python%%V\python.exe" & goto :python_found
    )
    if exist "C:\Program Files (x86)\Python%%V\python.exe" (
        set "PYTHON=C:\Program Files (x86)\Python%%V\python.exe" & goto :python_found
    )
    if exist "D:\Python%%V\python.exe" (
        set "PYTHON=D:\Python%%V\python.exe" & goto :python_found
    )
)
if exist "D:\Python\python.exe" ( set "PYTHON=D:\Python\python.exe" & goto :python_found )

echo [..] Buscando python.exe en disco...
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command ^
    "Get-ChildItem 'C:\' -Recurse -Filter 'python.exe' -ErrorAction SilentlyContinue ^| " ^
    "Where-Object { $_.FullName -notmatch 'WindowsApps|store' } ^| " ^
    "Select-Object -First 1 -ExpandProperty FullName"`) do (
    if exist "%%P" ( set PYTHON=%%P & goto :python_found )
)

echo [ERROR] Python no encontrado. Instala desde https://python.org
pause
exit /b 1

:python_found
echo [OK] Python: %PYTHON%

echo.
echo [..] Creando entorno virtual...
if not exist "venv" (
    %PYTHON% -m venv venv
    if %errorlevel% neq 0 ( echo [ERROR] No se pudo crear venv. & pause & exit /b 1 )
)
echo [OK] Entorno virtual listo

echo [..] Instalando dependencias...
venv\Scripts\pip.exe install -r requirements.txt --quiet
if %errorlevel% neq 0 ( echo [ERROR] Fallo instalacion de dependencias. & pause & exit /b 1 )
echo [OK] Dependencias instaladas

set NSSM_DIR=%~dp0tools\nssm
set NSSM=%NSSM_DIR%\nssm.exe

if exist "%NSSM%" goto :nssm_found

echo.
echo [..] Descargando NSSM...
mkdir "%NSSM_DIR%" >nul 2>&1
powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%NSSM_DIR%\nssm.zip' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo descargar NSSM.
    echo         Descarga manual: https://nssm.cc/download
    echo         Coloca nssm.exe en: %NSSM_DIR%\nssm.exe
    pause & exit /b 1
)
powershell -Command "Expand-Archive -Path '%NSSM_DIR%\nssm.zip' -DestinationPath '%NSSM_DIR%\extracted' -Force"
copy /y "%NSSM_DIR%\extracted\nssm-2.24\win64\nssm.exe" "%NSSM%" >nul
del "%NSSM_DIR%\nssm.zip" >nul 2>&1

:nssm_found
echo [OK] NSSM listo

set SERVICE_NAME=CentroJaponAPI
set APP_DIR=%~dp0
if "%APP_DIR:~-1%"=="\" set APP_DIR=%APP_DIR:~0,-1%
set PYTHON_EXE=%APP_DIR%\venv\Scripts\python.exe
set APP_SCRIPT=%APP_DIR%\app.py

echo.
echo ============================================================
echo   CREDENCIALES DE WINDOWS
echo   El servicio necesita correr bajo tu usuario para acceder
echo   a rutas de red. Usa el usuario con el que inicias sesion.
echo ============================================================
echo.
set /p SVC_USER="   Usuario (ej: Administrador o dominio\usuario): "
set /p SVC_PASS="   Contrasena: "
echo.

echo [..] Configurando servicio...
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM%" remove %SERVICE_NAME% confirm >nul 2>&1
"%NSSM%" install %SERVICE_NAME% "%PYTHON_EXE%" "%APP_SCRIPT%"
"%NSSM%" set %SERVICE_NAME% DisplayName "API Centro Japon - Inventario"
"%NSSM%" set %SERVICE_NAME% AppDirectory "%APP_DIR%"
"%NSSM%" set %SERVICE_NAME% ObjectName "%SVC_USER%" "%SVC_PASS%"
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM%" set %SERVICE_NAME% AppRestartDelay 10000
"%NSSM%" set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service_out.log"
"%NSSM%" set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\service_err.log"
"%NSSM%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM%" set %SERVICE_NAME% AppRotateBytes 5242880
echo [OK] Servicio registrado

echo.
echo [..] Abriendo puerto 5000...
netsh advfirewall firewall delete rule name="CentroJaponAPI" >nul 2>&1
netsh advfirewall firewall add rule name="CentroJaponAPI" dir=in action=allow protocol=TCP localport=5000
echo [OK] Puerto 5000 abierto

echo.
echo [..] Iniciando servicio...
"%NSSM%" start %SERVICE_NAME%
timeout /t 3 /nobreak >nul
"%NSSM%" status %SERVICE_NAME%

echo.
echo.
echo ============================================================
echo   INSTALACION COMPLETADA
echo ============================================================
echo.
echo   Acceder desde otro PC:
echo     http://[IP-DE-ESTE-SERVIDOR]:5000/api/inventario
echo.
echo   IP de este servidor:
ipconfig | findstr "IPv4"
echo.
echo   Logs: %APP_DIR%\logs\service_out.log
echo.
echo   Gestionar servicio:
echo     sc start %SERVICE_NAME%
echo     sc stop  %SERVICE_NAME%
echo     sc query %SERVICE_NAME%
echo.
pause
