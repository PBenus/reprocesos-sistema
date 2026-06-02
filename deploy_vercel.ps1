# =============================================================
#  deploy_vercel.ps1
#  Build del frontend y deploy a Vercel.
#  Prerrequisito: npm instalado, proyecto subido a GitHub.
# =============================================================

$frontendDir = "$PSScriptRoot\frontend"
$envProdFile = "$frontendDir\.env.production"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Deploy Frontend → Vercel                 " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que .env.production tiene URL real (no placeholder)
if (Test-Path $envProdFile) {
    $envContent = Get-Content $envProdFile -Raw
    if ($envContent -match "PENDIENTE_URL_TUNEL") {
        Write-Host "[ADVERTENCIA] El archivo frontend\.env.production aun tiene URL placeholder." -ForegroundColor Yellow
        Write-Host "              Primero ejecuta cloudflare\iniciar_tunel.ps1 para obtener la URL real." -ForegroundColor Yellow
        Write-Host ""
        $continuar = Read-Host "¿Continuar de todas formas? (s/N)"
        if ($continuar -ne "s") { exit 0 }
    } else {
        if ($envContent -match "VITE_API_URL=(.+)") {
            Write-Host "[OK] URL del backend: $($Matches[1].Trim())" -ForegroundColor Green
        }
    }
}

# Paso 1: Build de producción
Write-Host ""
Write-Host "[1/3] Construyendo frontend para producción..." -ForegroundColor Yellow
Set-Location $frontendDir
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] El build falló. Revisa los errores arriba." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "[OK] Build completado en frontend/dist/" -ForegroundColor Green

# Paso 2: Verificar/instalar Vercel CLI
Write-Host ""
Write-Host "[2/3] Verificando Vercel CLI..." -ForegroundColor Yellow
$vercelAvailable = $false
try {
    $v = vercel --version 2>&1
    Write-Host "[OK] Vercel CLI: $v" -ForegroundColor Green
    $vercelAvailable = $true
} catch {
    Write-Host "Instalando Vercel CLI globalmente..." -ForegroundColor Yellow
    npm install -g vercel
    $vercelAvailable = $true
}

# Paso 3: Deploy
if ($vercelAvailable) {
    Write-Host ""
    Write-Host "[3/3] Iniciando deploy en Vercel..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "IMPORTANTE: Si es el primer deploy, Vercel te preguntará:" -ForegroundColor Cyan
    Write-Host "  - Set up and deploy? → Y" -ForegroundColor White
    Write-Host "  - Which scope? → Tu cuenta personal" -ForegroundColor White
    Write-Host "  - Link to existing project? → N (crear nuevo)" -ForegroundColor White
    Write-Host "  - Project name → reprocesos-sistema" -ForegroundColor White
    Write-Host "  - Directory? → ./ (este directorio)" -ForegroundColor White
    Write-Host "  - Override settings? → N" -ForegroundColor White
    Write-Host ""
    
    Set-Location $frontendDir
    vercel --prod
    
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  Deploy completado!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "RECUERDA: Después de cada reinicio de tu PC o del túnel," -ForegroundColor Yellow
    Write-Host "  1. La URL del túnel puede cambiar" -ForegroundColor Yellow
    Write-Host "  2. Ve a vercel.com → tu proyecto → Settings → Environment Variables" -ForegroundColor Yellow
    Write-Host "     y actualiza VITE_API_URL con la nueva URL del túnel" -ForegroundColor Yellow
    Write-Host "  3. Haz Redeploy desde el dashboard de Vercel" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Presiona Enter para salir"
