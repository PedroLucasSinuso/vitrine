#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Gera o pacote vitrine-deploy.zip para levar ao servidor.
.DESCRIPTION
    1. Builda o frontend (npm run build)
    2. Coleta .env, price_checker.db e dist/
    3. Embrulha tudo num zip pronto pra copiar pro servidor
.EXAMPLE
    .\package.ps1
.EXAMPLE
    .\package.ps1 -OutputPath C:\Users\luizp\Desktop\vitrine-deploy.zip
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Resolve-Path "$ScriptDir\.."
$FRONTEND_DIR = "$PROJECT_ROOT\vitrine_frontend"
$BACKEND_DIR  = "$PROJECT_ROOT\vitrine_backend"
$DEPLOY_DIR   = "$PROJECT_ROOT\deploy"

$TEMP_ZIP_DIR = "$env:TEMP\vitrine-package"

Write-Host ">>> [1/4] Buildando frontend..." -ForegroundColor Cyan
Push-Location $FRONTEND_DIR
npm run build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Build falhou" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "[OK] Frontend buildado" -ForegroundColor Green
Write-Host ""

Write-Host ">>> [2/4] Baixando binarios e preparando arquivos..." -ForegroundColor Cyan
if (Test-Path $TEMP_ZIP_DIR) {
    Remove-Item -Recurse $TEMP_ZIP_DIR -Force
}
New-Item -ItemType Directory -Path "$TEMP_ZIP_DIR\deploy" -Force | Out-Null

# Baixa Caddy e inclui no bundle
Write-Host "  Baixando Caddy..."
try {
    Invoke-WebRequest -Uri "https://github.com/caddyserver/caddy/releases/download/v2.11.3/caddy_2.11.3_windows_amd64.zip" -OutFile "$env:TEMP\caddy.zip" -TimeoutSec 60
    Expand-Archive -Path "$env:TEMP\caddy.zip" -DestinationPath "$TEMP_ZIP_DIR\deploy" -Force
    Remove-Item "$env:TEMP\caddy.zip" -Force
    Write-Host "  [OK] Caddy baixado" -ForegroundColor Green
} catch {
    Write-Host "  [AVISO] Falha ao baixar Caddy ($($_.Exception.Message))" -ForegroundColor Yellow
}

# Baixa NSSM e inclui no bundle
Write-Host "  Baixando NSSM..."
try {
    Invoke-WebRequest -Uri "https://github.com/plossys/nssm/releases/download/v2.24.8/nssm.exe" -OutFile "$TEMP_ZIP_DIR\deploy\nssm.exe" -TimeoutSec 60
    Write-Host "  [OK] NSSM baixado" -ForegroundColor Green
} catch {
    Write-Host "  [AVISO] Falha ao baixar NSSM ($($_.Exception.Message))" -ForegroundColor Yellow
}

# Copia scripts do deploy
Copy-Item -Recurse "$DEPLOY_DIR\*" "$TEMP_ZIP_DIR\deploy\"

$envSource = "$BACKEND_DIR\.env"
if (Test-Path $envSource) {
    Copy-Item $envSource "$TEMP_ZIP_DIR\.env"
    Write-Host "[OK] .env copiado" -ForegroundColor Green
} else {
    Write-Host "[AVISO] .env nao encontrado em $envSource" -ForegroundColor Yellow
}

if (Test-Path "$FRONTEND_DIR\dist") {
    Copy-Item -Recurse "$FRONTEND_DIR\dist" "$TEMP_ZIP_DIR\dist"
    Write-Host "[OK] dist/ copiado" -ForegroundColor Green
} else {
    Write-Host "[ERRO] dist/ nao encontrado" -ForegroundColor Red
    Remove-Item -Recurse $TEMP_ZIP_DIR -Force
    exit 1
}

if (Test-Path "$BACKEND_DIR\price_checker.db") {
    Copy-Item "$BACKEND_DIR\price_checker.db" "$TEMP_ZIP_DIR\price_checker.db"
    Write-Host "[OK] price_checker.db copiado" -ForegroundColor Green
} else {
    Write-Host "[AVISO] price_checker.db nao encontrado" -ForegroundColor Yellow
}
Write-Host ""

Write-Host ">>> [3/4] Compactando..." -ForegroundColor Cyan
if (-not $OutputPath) {
    $OutputPath = "$PROJECT_ROOT\vitrine-deploy.zip"
}
if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TEMP_ZIP_DIR, $OutputPath)
Write-Host "[OK] Zip gerado: $OutputPath" -ForegroundColor Green
Write-Host ""

Write-Host ">>> [4/4] Limpando temporarios..." -ForegroundColor Cyan
Remove-Item -Recurse $TEMP_ZIP_DIR -Force
Write-Host "[OK] Temp limpo" -ForegroundColor Green
Write-Host ""

$item = Get-Item $OutputPath
$size = [math]::Round($item.Length / 1MB, 1)
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Pacote gerado!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "Arquivo: $OutputPath"
Write-Host "Tamanho: $size MB"
Write-Host ""
Write-Host 'No servidor, extraia e execute:'
Write-Host '  .\deploy\install.ps1 -DistPath .\'
Write-Host ""
