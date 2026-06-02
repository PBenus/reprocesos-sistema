@echo off
title Sistema de Reprocesos - Arranque
color 0A

echo.
echo =============================================
echo   Sistema de Control de Reprocesos
echo   Iniciando servicios...
echo =============================================
echo.

:: Verificar Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta corriendo.
    echo Por favor abre Docker Desktop y vuelve a ejecutar este script.
    echo.
    pause
    exit /b 1
)

:: Verificar que cloudflared.exe existe
if not exist "%~dp0cloudflare\cloudflared.exe" (
    echo [ERROR] No se encontro cloudflared.exe
    echo Ejecuta primero: cloudflare\descargar_cloudflared.ps1
    echo.
    pause
    exit /b 1
)

:: ─── Ventana 1: Backend FastAPI via Docker ────────────────────────────────────
echo [1/2] Iniciando Backend FastAPI (Docker)...
start "Backend FastAPI" cmd /k "cd /d %~dp0backend && docker-compose up"

:: Esperar a que FastAPI arranque
echo     Esperando que FastAPI arranque...
timeout /t 5 /nobreak > nul

:: ─── Ventana 2: Tunel Cloudflare (directo, sin PowerShell) ───────────────────
echo [2/2] Iniciando Tunel Cloudflare...
start "Tunel Cloudflare" cmd /k "%~dp0cloudflare\cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate"

echo.
echo =============================================
echo   Servicios iniciados!
echo.
echo   Backend : http://localhost:8000
echo   Docs    : http://localhost:8000/docs
echo.
echo   Mira la ventana "Tunel Cloudflare" para
echo   ver la URL publica (*.trycloudflare.com)
echo =============================================
echo.
pause
