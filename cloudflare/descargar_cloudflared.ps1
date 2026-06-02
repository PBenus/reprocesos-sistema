# =============================================================
#  descargar_cloudflared.ps1
#  Descarga cloudflared.exe de Cloudflare (solo correr una vez)
# =============================================================

$dest = "$PSScriptRoot\cloudflared.exe"
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

Write-Host ""
Write-Host "Descargando cloudflared.exe..." -ForegroundColor Cyan

if (Test-Path $dest) {
    Write-Host "cloudflared.exe ya existe. Omitiendo descarga." -ForegroundColor Green
    exit 0
}

try {
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    Write-Host "Descarga completa: $dest" -ForegroundColor Green
    Write-Host ""
    Write-Host "Versión instalada:" -ForegroundColor White
    & $dest --version
} catch {
    Write-Host "[ERROR] No se pudo descargar: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Presiona Enter para salir"
