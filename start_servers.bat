@echo off
title Sistema de Reprocesos - Arranque Completo
color 0A

echo.
echo =============================================
echo   Sistema de Control de Reprocesos
echo   Iniciando todos los servicios...
echo =============================================
echo.

:: Verificar que el entorno virtual de Python existe
if not exist "%~dp0backend\venv\Scripts\activate.bat" (
    echo [ADVERTENCIA] No se encontro entorno virtual en backend\venv
    echo Iniciando con Python global del sistema...
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=%~dp0backend\venv\Scripts\python
)

:: ─── Ventana 1: Backend FastAPI ───────────────────────────────────────
echo [1/2] Iniciando Backend FastAPI en puerto 8000...
start "Backend FastAPI" cmd /k "cd /d %~dp0backend && %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Esperar 3 segundos a que FastAPI arranque
timeout /t 3 /nobreak > nul

:: ─── Ventana 2: Túnel Cloudflare ──────────────────────────────────────
echo [2/2] Iniciando Tunel Cloudflare...
start "Tunel Cloudflare" powershell -ExecutionPolicy Bypass -File "%~dp0cloudflare\iniciar_tunel.ps1"

echo.
echo =============================================
echo   Servicios iniciados en ventanas separadas.
echo   Mira la ventana "Tunel Cloudflare" para
echo   obtener la URL publica.
echo =============================================
echo.
pause
