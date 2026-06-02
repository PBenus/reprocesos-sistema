# =============================================================
#  iniciar_tunel.ps1
#  Inicia el túnel de Cloudflare y muestra la URL pública.
#  Ejecución: Click derecho → "Ejecutar con PowerShell"
#  o desde terminal: .\iniciar_tunel.ps1
# =============================================================

$cloudflaredPath = "$PSScriptRoot\cloudflared.exe"
$logFile = "$PSScriptRoot\tunnel.log"
$envFile = "$PSScriptRoot\..\backend\.env"
$envProdFile = "$PSScriptRoot\..\frontend\.env.production"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Sistema de Reprocesos - Túnel Cloudflare  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que cloudflared existe
if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "[ERROR] No se encontró cloudflared.exe en: $cloudflaredPath" -ForegroundColor Red
    Write-Host "Ejecuta primero: descargar_cloudflared.ps1" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "[1/3] Iniciando túnel Cloudflare hacia http://localhost:8000..." -ForegroundColor Yellow
Write-Host "      (esperando URL pública...)" -ForegroundColor Gray

# Iniciar cloudflared en background y capturar output
$process = Start-Process -FilePath $cloudflaredPath `
    -ArgumentList "tunnel", "--url", "http://localhost:8000", "--no-autoupdate" `
    -RedirectStandardError $logFile `
    -PassThru `
    -NoNewWindow

# Esperar hasta encontrar la URL en el log (máximo 30 segundos)
$tunnelUrl = $null
$timeout = 30
$elapsed = 0

while ($elapsed -lt $timeout) {
    Start-Sleep -Seconds 1
    $elapsed++

    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://[a-zA-Z0-9\-]+\.trycloudflare\.com") {
            $tunnelUrl = $Matches[0]
            break
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "[ERROR] No se pudo obtener la URL del túnel." -ForegroundColor Red
    Write-Host "Verifica que el puerto 8000 esté disponible y que tengas conexión a internet." -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  TÚNEL ACTIVO" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  URL PÚBLICA DEL BACKEND:" -ForegroundColor White
Write-Host "  $tunnelUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "[2/3] Actualizando archivos de configuración..." -ForegroundColor Yellow

# Actualizar CORS_ORIGINS en backend/.env
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    # Obtener el valor actual de CORS_ORIGINS
    if ($envContent -match "CORS_ORIGINS=(.+)") {
        $currentCors = $Matches[1].Trim()
        # Agregar la URL del túnel si no está ya
        if ($currentCors -notlike "*$tunnelUrl*") {
            $newCors = "CORS_ORIGINS=$currentCors,$tunnelUrl"
            $envContent = $envContent -replace "CORS_ORIGINS=.+", $newCors
            Set-Content $envFile $envContent -NoNewline
            Write-Host "   ✓ CORS actualizado en backend/.env" -ForegroundColor Green
        } else {
            Write-Host "   ✓ CORS ya contiene la URL del túnel" -ForegroundColor Green
        }
    }
}

# Actualizar frontend/.env.production
if (Test-Path $envProdFile) {
    $prodContent = "# URL del backend a través del túnel de Cloudflare`nVITE_API_URL=$tunnelUrl"
    Set-Content $envProdFile $prodContent
    Write-Host "   ✓ frontend/.env.production actualizado" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/3] Estado del sistema:" -ForegroundColor Yellow
Write-Host "   ✓ Túnel Cloudflare: ACTIVO (PID: $($process.Id))" -ForegroundColor Green
Write-Host "   ! Asegúrate de que FastAPI esté corriendo en el puerto 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  PRÓXIMOS PASOS" -ForegroundColor Cyan  
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Copia esta URL: $tunnelUrl" -ForegroundColor White
Write-Host "  2. Ve a Vercel → Settings → Environment Variables" -ForegroundColor White
Write-Host "     Nombre: VITE_API_URL" -ForegroundColor White
Write-Host "     Valor:  $tunnelUrl" -ForegroundColor Cyan
Write-Host "  3. Redeploy en Vercel" -ForegroundColor White
Write-Host ""
Write-Host "  Presiona Ctrl+C para detener el túnel" -ForegroundColor Gray
Write-Host ""

# Guardar URL en archivo para referencia
"$tunnelUrl" | Set-Content "$PSScriptRoot\ultima_url_tunel.txt"
Write-Host "  (URL guardada en: cloudflare\ultima_url_tunel.txt)" -ForegroundColor Gray
Write-Host ""

# Mantener el script activo mientras el túnel corre
try {
    $process.WaitForExit()
} catch {
    # Ctrl+C presionado
}

Write-Host ""
Write-Host "[INFO] Túnel detenido." -ForegroundColor Yellow
