# =============================================================
#  setup_git_github.ps1
#  Inicializa el repositorio Git y lo sube a GitHub.
#  Prerrequisito: tener Git y GitHub CLI instalados.
#  Ejecución: powershell -ExecutionPolicy Bypass -File setup_git_github.ps1
# =============================================================

$projectRoot = $PSScriptRoot
$repoName = "reprocesos-sistema"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Configuración Git + GitHub               " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar git
try {
    $gitVersion = git --version 2>&1
    Write-Host "[OK] Git instalado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Git no está instalado. Instálalo desde https://git-scm.com" -ForegroundColor Red
    exit 1
}

# Verificar GitHub CLI
$ghAvailable = $false
try {
    $ghVersion = gh --version 2>&1
    Write-Host "[OK] GitHub CLI instalado" -ForegroundColor Green
    $ghAvailable = $true
} catch {
    Write-Host "[INFO] GitHub CLI no encontrado. Se usará proceso manual." -ForegroundColor Yellow
}

# Inicializar Git si no está inicializado
if (-not (Test-Path "$projectRoot\.git")) {
    Write-Host ""
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Yellow
    git -C $projectRoot init
    git -C $projectRoot branch -M main
    Write-Host "[OK] Repositorio Git inicializado" -ForegroundColor Green
} else {
    Write-Host "[OK] Repositorio Git ya existe" -ForegroundColor Green
}

# Agregar todos los archivos y hacer primer commit
Write-Host ""
Write-Host "Agregando archivos al commit inicial..." -ForegroundColor Yellow
git -C $projectRoot add .
git -C $projectRoot commit -m "feat: sistema de reprocesos - configuración inicial de despliegue"
Write-Host "[OK] Commit inicial creado" -ForegroundColor Green

if ($ghAvailable) {
    Write-Host ""
    Write-Host "Creando repositorio privado en GitHub..." -ForegroundColor Yellow
    gh repo create $repoName --private --source $projectRoot --remote origin --push
    Write-Host ""
    Write-Host "[OK] Repositorio subido a GitHub!" -ForegroundColor Green
    Write-Host "     URL: https://github.com/$(gh api user --jq .login)/$repoName" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host "  PASOS MANUALES PARA GITHUB               " -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Ve a https://github.com/new" -ForegroundColor White
    Write-Host "2. Nombre del repo: $repoName" -ForegroundColor Cyan
    Write-Host "3. Privado: SI" -ForegroundColor White
    Write-Host "4. NO inicialices con README (ya tienes código)" -ForegroundColor White
    Write-Host "5. Copia los comandos de GitHub y pégalos aquí:" -ForegroundColor White
    Write-Host ""
    Write-Host "   git remote add origin https://github.com/TU_USUARIO/$repoName.git" -ForegroundColor Gray
    Write-Host "   git push -u origin main" -ForegroundColor Gray
    Write-Host ""
}

Write-Host ""
Write-Host "Listo! Ahora puedes conectar el repo a Vercel." -ForegroundColor Green
Write-Host ""
Read-Host "Presiona Enter para salir"
