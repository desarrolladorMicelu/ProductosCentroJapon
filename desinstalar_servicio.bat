@echo off
:: ============================================================
::  DESINSTALADOR DEL SERVICIO - API Centro Japón
::  Ejecutar como ADMINISTRADOR
:: ============================================================
title Desinstalador Servicio - API Centro Japon
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecutar como ADMINISTRADOR.
    pause & exit /b 1
)

set SERVICE_NAME=CentroJaponAPI
set NSSM=%~dp0tools\nssm\nssm.exe

echo Deteniendo y eliminando servicio %SERVICE_NAME%...
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM%" remove %SERVICE_NAME% confirm

:: Eliminar regla del firewall
netsh advfirewall firewall delete rule name="CentroJaponAPI" >nul 2>&1

echo.
echo [OK] Servicio eliminado correctamente.
pause
