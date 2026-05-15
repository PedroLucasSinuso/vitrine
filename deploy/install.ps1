#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Instala o Vitrine em Windows Server - Python, Caddy, NSSM, backend e frontend.

.PARAMETER DistPath
    Caminho do pendrive contendo .env, price_checker.db e a pasta dist\.
    Exemplo: D:\
    Se omitido, .env e dist/ precisam ser copiados manualmente depois.

.EXAMPLE
    .\install.ps1 -DistPath D:\
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$DistPath = ""
)

# ---------- CONFIG ----------
$VITRINE = "C:\Vitrine"
$CODE = "$VITRINE\code"
$PYTHON_DIR = "$VITRINE\python"
$DATA_DIR = "$VITRINE\data"
$LOGS_DIR = "$DATA_DIR\logs"
$BACKEND_DIR = "$CODE\vitrine_backend"
$FRONTEND_DIR = "$CODE\vitrine_frontend"
$DEPLOY_DIR = "$CODE\deploy"

$PythonVersion = "3.11.9"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$CaddyUrl = "https://github.com/caddyserver/caddy/releases/latest/download/caddy_windows_amd64.zip"
$NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$GitUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.48.1-64-bit.exe"
$RepoUrl = "https://github.com/PedroLucasSinuso/vitrine.git"

$ProgressPreference = "SilentlyContinue"

# ---------- HELPERS ----------
function Write-Step { param($Msg) Write-Host ">>> $Msg" -ForegroundColor Cyan }
function Write-OK   { Write-Host "  [OK] $($args -join ' ')" -ForegroundColor Green }
function Write-Warn { Write-Host "  [!] $($args -join ' ')" -ForegroundColor Yellow }
function Write-Err  { Write-Host "  [ERRO] $($args -join ' ')" -ForegroundColor Red; exit 1 }

# ---------- 1. GIT ----------
Write-Step "1/13 - Verificando Git..."
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "  Instalando Git via winget..."
        winget install --id Git.Git -e --source winget --accept-package-agreements | Out-Null
    } else {
        Write-Host "  Baixando Git portable..."
        $gitInstaller = "$env:TEMP\git-installer.exe"
        Invoke-WebRequest -Uri $GitUrl -OutFile $gitInstaller
        $gitArgs = '/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
        Start-Process -Wait -FilePath $gitInstaller -ArgumentList $gitArgs
    }
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
$gitVer = git --version
Write-OK "Git: $gitVer"

# ---------- 2. PASTAS ----------
Write-Step "2/13 - Criando estrutura de pastas..."
@($CODE, $PYTHON_DIR, $LOGS_DIR) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}
Write-OK "Pastas criadas em $VITRINE"

# ---------- 3. PYTHON ----------
Write-Step "3/13 - Baixando Python embeddable $PythonVersion..."
$pythonZip = "$env:TEMP\python-$PythonVersion-embed-amd64.zip"
if (!(Test-Path "$PYTHON_DIR\python.exe")) {
    Invoke-WebRequest -Uri $PythonUrl -OutFile $pythonZip
    Expand-Archive -Path $pythonZip -DestinationPath $PYTHON_DIR -Force
    Write-OK "Python $PythonVersion extraido em $PYTHON_DIR"
} else {
    Write-OK "Python ja existe em $PYTHON_DIR"
}

# ---------- 4. CADDY ----------
Write-Step "4/13 - Baixando Caddy..."
$caddyPath = "$CODE\caddy.exe"
if (!(Test-Path $caddyPath)) {
    $caddyZip = "$env:TEMP\caddy.zip"
    try {
        Invoke-WebRequest -Uri $CaddyUrl -OutFile $caddyZip -TimeoutSec 60
        Expand-Archive -Path $caddyZip -DestinationPath $CODE -Force
        Remove-Item $caddyZip -Force
        Write-OK "Caddy baixado e extraido"
    } catch {
        Write-Warn "Falha ao baixar Caddy ($($_.Exception.Message))"
        Write-Warn "Baixe manualmente de $CaddyUrl, extraia caddy.exe e salve em $caddyPath"
    }
} else {
    Write-OK "Caddy ja existe"
}

# ---------- 5. NSSM ----------
Write-Step "5/13 - Verificando NSSM..."
$nssmPath = "$CODE\nssm.exe"
$nssmGlobal = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssmGlobal) {
    $nssmPath = $nssmGlobal.Source
    Write-OK "NSSM encontrado no sistema: $nssmPath"
} elseif (Test-Path $nssmPath) {
    Write-OK "NSSM ja existe em $nssmPath"
} else {
    Write-Host "  Baixando NSSM..."
    $nssmZip = "$env:TEMP\nssm-2.24.zip"
    $nssmTemp = "$env:TEMP\nssm"
    Invoke-WebRequest -Uri $NssmUrl -OutFile $nssmZip
    Expand-Archive -Path $nssmZip -DestinationPath $nssmTemp -Force
    Copy-Item "$nssmTemp\nssm-2.24\win64\nssm.exe" $nssmPath -Force
    Write-OK "NSSM baixado para $nssmPath"
}
$NSSM = $nssmPath

# ---------- 6. CLONE ----------
Write-Step "6/13 - Clonando repositorio..."
if (Test-Path "$CODE\.git") {
    Write-OK "Repositorio ja clonado, atualizando..."
    Push-Location $CODE
    git pull
    Pop-Location
} else {
    git clone $RepoUrl $CODE
    Write-OK "Repositorio clonado"
}
git config --global --add safe.directory $CODE 2>$null

# ---------- 7. SITE-PACKAGES ----------
Write-Step "7/13 - Habilitando site-packages no Python..."
$pythonPth = Get-ChildItem "$PYTHON_DIR\*._pth" | Select-Object -First 1 -ExpandProperty FullName
if ($pythonPth) {
    $content = Get-Content $pythonPth -Raw
    if ($content -match '#import site') {
        $content = $content -replace '#import site', 'import site'
        Set-Content -Path $pythonPth -Value $content
        Write-OK "site-packages habilitado ($pythonPth)"
    } else {
        Write-OK "site-packages ja habilitado"
    }
} else {
    Write-Warn "Arquivo ._pth nao encontrado em $PYTHON_DIR"
}

# ---------- 8. PIP ----------
Write-Step "8/13 - Instalando pip..."
$pipCheck = & "$PYTHON_DIR\python.exe" -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    $getPip = "$env:TEMP\get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip
    & "$PYTHON_DIR\python.exe" $getPip --no-warn-script-location
    Write-OK "pip instalado"
} else {
    Write-OK "pip ja instalado ($($pipCheck.Trim()))"
}

# ---------- 9. REQUIREMENTS ----------
Write-Step "9/13 - Instalando dependencias do backend..."
$reqFile = "$CODE\deploy\requirements.txt"
if (Test-Path $reqFile) {
    & "$PYTHON_DIR\python.exe" -m pip install -r $reqFile --no-warn-script-location
    Write-OK "Dependencias instaladas"
} else {
    Write-Warn "requirements.txt nao encontrado em $reqFile - ignorando"
}

# ---------- 10. CONFIGS ----------
Write-Step "10/13 - Copiando configuracoes..."
Copy-Item "$CODE\deploy\Caddyfile" "$CODE\Caddyfile" -Force
Write-OK "Caddyfile copiado"

# ---------- 11. .ENV + DADOS ----------
Write-Step "11/13 - Copiando .env e dados..."
if ($DistPath -and (Test-Path $DistPath)) {
    if (Test-Path "$DistPath\.env") {
        Copy-Item "$DistPath\.env" "$DATA_DIR\.env" -Force
        Write-OK ".env copiado de $DistPath"
    } else {
        Write-Warn ".env nao encontrado em $DistPath"
    }
    if (Test-Path "$DistPath\price_checker.db") {
        Copy-Item "$DistPath\price_checker.db" "$DATA_DIR\price_checker.db" -Force
        Write-OK "price_checker.db copiado"
    }
} else {
    Write-Warn "DistPath nao informado. Copie .env para $DATA_DIR\.env manualmente."
}
if (Test-Path "$DATA_DIR\.env") {
    Copy-Item "$DATA_DIR\.env" "$BACKEND_DIR\.env" -Force
}

# ---------- 12. FRONTEND ----------
Write-Step "12/13 - Copiando frontend..."
if ($DistPath -and (Test-Path "$DistPath\dist")) {
    $distDest = "$FRONTEND_DIR\dist"
    if (Test-Path $distDest) {
        Remove-Item -Recurse $distDest -Force
    }
    Copy-Item -Recurse "$DistPath\dist" $distDest
    Write-OK "Frontend dist copiado de $DistPath"
} else {
    Write-Warn "dist nao encontrado. Copie manualmente para $FRONTEND_DIR\dist\ depois."
}

# ---------- 13. SERVICOS ----------
Write-Step "13/13 - Registrando servicos Windows..."
if (!(Test-Path $NSSM)) {
    Write-Warn "NSSM nao encontrado em $NSSM. Registro de servicos pulado."
    Write-Warn "Baixe manualmente de $NssmUrl e extraia nssm.exe para $CODE"
} else {
    & $NSSM stop VitrineBackend 2>$null
    & $NSSM remove VitrineBackend confirm 2>$null
    & $NSSM stop VitrineFrontend 2>$null
    & $NSSM remove VitrineFrontend confirm 2>$null

    # Backend (Uvicorn)
    & $NSSM install VitrineBackend "$PYTHON_DIR\python.exe" "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    & $NSSM set VitrineBackend AppDirectory $BACKEND_DIR
    & $NSSM set VitrineBackend AppEnvironmentExtra "PYTHONPATH=$BACKEND_DIR;$PYTHON_DIR\Lib\site-packages"
    & $NSSM set VitrineBackend AppStdout "$LOGS_DIR\backend.log"
    & $NSSM set VitrineBackend AppStderr "$LOGS_DIR\backend-error.log"
    & $NSSM set VitrineBackend Start SERVICE_AUTO_START
    & $NSSM set VitrineBackend ObjectName LocalSystem
    & $NSSM set VitrineBackend AppRestartDelay 5000
    Write-OK "Servico VitrineBackend registrado"

    # Frontend (Caddy)
    & $NSSM install VitrineFrontend "$CODE\caddy.exe" "run --config $CODE\Caddyfile"
    & $NSSM set VitrineFrontend AppDirectory $CODE
    & $NSSM set VitrineFrontend AppStdout "$LOGS_DIR\caddy.log"
    & $NSSM set VitrineFrontend AppStderr "$LOGS_DIR\caddy-error.log"
    & $NSSM set VitrineFrontend Start SERVICE_AUTO_START
    & $NSSM set VitrineFrontend ObjectName LocalSystem
    & $NSSM set VitrineFrontend AppRestartDelay 5000
    Write-OK "Servico VitrineFrontend registrado"

    # ---------- INICIAR ----------
    Write-Step "- Iniciando servicos..."
    & $NSSM start VitrineBackend
    Start-Sleep -Seconds 3
    & $NSSM start VitrineFrontend
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Instalacao concluida!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://localhost:8080"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Logs:     $LOGS_DIR"
Write-Host ""
