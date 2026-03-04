@echo off
title API Centro Japon

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
    if exist "%%P" ( set PYTHON=%%P & goto :found )
)

for %%V in (314 313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :found
    )
    if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe"
        goto :found
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set "PYTHON=C:\Program Files\Python%%V\python.exe"
        goto :found
    )
    if exist "D:\Python%%V\python.exe" (
        set "PYTHON=D:\Python%%V\python.exe"
        goto :found
    )
)
if exist "D:\Python\python.exe" (
    set "PYTHON=D:\Python\python.exe"
    goto :found
)

echo [ERROR] No se encontro Python. Instala Python desde https://python.org
pause
exit /b 1

:found
echo [OK] Python encontrado: %PYTHON%
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    set PYTHON="%~dp0venv\Scripts\python.exe"
    echo [OK] Usando entorno virtual
)

echo [OK] Iniciando API...
%PYTHON% app.py
