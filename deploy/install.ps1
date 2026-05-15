#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Instala o Vitrine em Windows Server - Python, Caddy, NSSM, backend e frontend.

.PARAMETER DistPath
    Caminho com .env, dist\ e price_checker.db.
    Se omitido, usa a pasta pai de deploy\ (extração do zip).

.EXAMPLE
    .\install.ps1 -DistPath D:\
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$DistPath = ""
)

# ---------- CONFIG ----------
$VITRINE = "C:\Vitrine"
$BIN = "$VITRINE\bin"
$CODE = "$VITRINE\code"
$PYTHON_DIR = "$VITRINE\python"
$DATA_DIR = "$VITRINE\data"
$LOGS_DIR = "$DATA_DIR\logs"
$BACKEND_DIR = "$CODE\vitrine_backend"
$FRONTEND_DIR = "$CODE\vitrine_frontend"

$CaddyVersion = "v2.11.3"
$PythonVersion = "3.11.9"

$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$CaddyUrl = "https://github.com/caddyserver/caddy/releases/download/$CaddyVersion/caddy_$($CaddyVersion.Substring(1))_windows_amd64.zip"
$NssmUrl = "https://github.com/plossys/nssm/releases/download/v2.24.8/nssm.exe"
$GitUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.48.1-64-bit.exe"
$RepoUrl = "https://github.com/PedroLucasSinuso/vitrine.git"

$ProgressPreference = "SilentlyContinue"

# ---------- HELPERS ----------
function Write-Step { param($Msg) Write-Host ">>> $Msg" -ForegroundColor Cyan }
function Write-OK   { Write-Host "  [OK] $($args -join ' ')" -ForegroundColor Green }
function Write-Warn { Write-Host "  [!] $($args -join ' ')" -ForegroundColor Yellow }
function Write-Err  { Write-Host "  [ERRO] $($args -join ' ')" -ForegroundColor Red; exit 1 }

# ---------- 0. DISTPATH ----------
if (-not $DistPath) {
    $scriptParent = Split-Path -Parent $MyInvocation.MyCommand.Path
    $DistPath = Resolve-Path "$scriptParent\.."
    Write-OK "DistPath auto-detected: $DistPath"
}

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

# ---------- 2. PASTAS E FIREWALL ----------
Write-Step "2/13 - Criando estrutura de pastas..."
@($BIN, $CODE, $PYTHON_DIR, $LOGS_DIR) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}
Write-OK "Pastas criadas em $VITRINE"

Write-Host "  Configurando firewall para porta 8080..."
$fwRule = Get-NetFirewallRule -DisplayName "Vitrine Web (8080)" -ErrorAction SilentlyContinue
if (-not $fwRule) {
    New-NetFirewallRule -DisplayName "Vitrine Web (8080)" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow | Out-Null
    Write-OK "Regra de firewall criada para porta 8080"
} else {
    Write-OK "Regra de firewall ja existe"
}

Write-Host "  Adicionando $BIN ao PATH do sistema..."
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($currentPath -notlike "*$BIN*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$BIN", "Machine")
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    Write-OK "$BIN adicionado ao PATH"
} else {
    Write-OK "$BIN ja esta no PATH"
}

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
Write-Step "4/13 - Instalando Caddy..."
$caddyPath = "$BIN\caddy.exe"
if (Test-Path $caddyPath) {
    Write-OK "Caddy ja existe em $caddyPath"
} elseif (Test-Path "$PSScriptRoot\caddy.exe") {
    Copy-Item "$PSScriptRoot\caddy.exe" $caddyPath -Force
    Write-OK "Caddy copiado do bundle local"
} else {
    Write-Host "  Baixando Caddy online..."
    $caddyZip = "$env:TEMP\caddy.zip"
    try {
        Invoke-WebRequest -Uri $CaddyUrl -OutFile $caddyZip -TimeoutSec 60
        Expand-Archive -Path $caddyZip -DestinationPath $BIN -Force
        Remove-Item $caddyZip -Force
        Write-OK "Caddy baixado e extraido"
    } catch {
        Write-Warn "Falha ao baixar Caddy ($($_.Exception.Message))"
        Write-Warn "Baixe manualmente: $CaddyUrl"
        Write-Warn "Extraia caddy.exe para $caddyPath"
    }
}

# ---------- 5. NSSM ----------
Write-Step "5/13 - Verificando NSSM..."
$nssmPath = "$BIN\nssm.exe"
$nssmGlobal = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssmGlobal) {
    $nssmPath = $nssmGlobal.Source
    Write-OK "NSSM encontrado no sistema: $nssmPath"
} elseif (Test-Path $nssmPath) {
    Write-OK "NSSM ja existe em $nssmPath"
} elseif (Test-Path "$PSScriptRoot\nssm.exe") {
    Copy-Item "$PSScriptRoot\nssm.exe" $nssmPath -Force
    Write-OK "NSSM copiado do bundle local"
} else {
    Write-Host "  Baixando NSSM online..."
    try {
        Invoke-WebRequest -Uri $NssmUrl -OutFile $nssmPath -TimeoutSec 60
        Write-OK "NSSM baixado para $nssmPath"
    } catch {
        Write-Warn "Falha ao baixar NSSM ($($_.Exception.Message))"
        Write-Warn "Tente baixar manualmente de $NssmUrl e salve como $nssmPath"
    }
}
$NSSM = $nssmPath

# ---------- 6. CLONE ----------
Write-Step "6/13 - Clonando repositorio..."
if (Test-Path "$CODE\.git") {
    Write-OK "Repositorio ja clonado, atualizando..."
    Push-Location $CODE
    git pull
    Pop-Location
} elseif ((Test-Path $CODE) -and (@(Get-ChildItem $CODE).Count -gt 0)) {
    Write-Warn "$CODE ja existe e nao esta vazio (mas nao e um clone git)"
    Write-Warn "Remova manualmente o conteudo de $CODE e reexecute, ou clone manualmente:"
    Write-Warn "  git clone $RepoUrl $CODE"
} else {
    git clone $RepoUrl $CODE
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Falha ao clonar repositorio (exit code: $LASTEXITCODE)"
    }
    Write-OK "Repositorio clonado"
}
if (Test-Path "$CODE\.git") {
    git config --global --add safe.directory $CODE 2>$null
}
if (-not (Test-Path "$BACKEND_DIR\main.py")) {
    Write-Warn "Backend nao encontrado em $BACKEND_DIR apos clone - algo deu errado"
}

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
    try {
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -TimeoutSec 60
        & "$PYTHON_DIR\python.exe" $getPip --no-warn-script-location
        Write-OK "pip instalado"
    } catch {
        Write-Warn "Falha ao baixar/instalar pip ($($_.Exception.Message))"
    }
} else {
    Write-OK "pip ja instalado ($($pipCheck.Trim()))"
}

# ---------- 9. REQUIREMENTS ----------
Write-Step "9/13 - Instalando dependencias do backend..."
$reqFile = "$CODE\deploy\requirements.txt"
if (Test-Path $reqFile) {
    & "$PYTHON_DIR\python.exe" -m pip install -r $reqFile --no-warn-script-location
    Write-OK "Dependencias instaladas"
} elseif (Test-Path "$BACKEND_DIR\pyproject.toml") {
    Write-OK "Usando pyproject.toml para dependencias..."
    Push-Location $BACKEND_DIR
    & "$PYTHON_DIR\python.exe" -m pip install . --no-warn-script-location
    Pop-Location
} else {
    Write-Warn "requirements.txt e pyproject.toml nao encontrados"
}

# ---------- 10. CONFIGS ----------
Write-Step "10/13 - Copiando configuracoes..."
if (Test-Path "$PSScriptRoot\Caddyfile") {
    Copy-Item "$PSScriptRoot\Caddyfile" "$BIN\Caddyfile" -Force
    if (Test-Path $caddyPath) {
        & "$caddyPath" fmt --overwrite "$BIN\Caddyfile" 2>$null
    }
    Write-OK "Caddyfile copiado para $BIN"
} elseif (Test-Path "$BACKEND_DIR\..\deploy\Caddyfile") {
    Copy-Item "$BACKEND_DIR\..\deploy\Caddyfile" "$BIN\Caddyfile" -Force
    if (Test-Path $caddyPath) {
        & "$caddyPath" fmt --overwrite "$BIN\Caddyfile" 2>$null
    }
    Write-OK "Caddyfile copiado do repositorio para $BIN"
} else {
    Write-Warn "Caddyfile nao encontrado"
}

# ---------- 11. .ENV + DADOS ----------
Write-Step "11/13 - Copiando .env e dados..."
if ($DistPath -and (Test-Path $DistPath)) {
    if (Test-Path "$DistPath\.env") {
        if (-not (Test-Path $BACKEND_DIR)) { New-Item -ItemType Directory -Path $BACKEND_DIR -Force | Out-Null }
        Copy-Item "$DistPath\.env" "$BACKEND_DIR\.env" -Force
        Copy-Item "$DistPath\.env" "$DATA_DIR\.env" -Force
        Write-OK ".env copiado de $DistPath"
    } else {
        Write-Warn ".env nao encontrado em $DistPath"
    }
    if (Test-Path "$DistPath\price_checker.db") {
        Copy-Item "$DistPath\price_checker.db" "$DATA_DIR\price_checker.db" -Force
        if (-not (Test-Path "$BACKEND_DIR\data")) { New-Item -ItemType Directory -Path "$BACKEND_DIR\data" -Force | Out-Null }
        Copy-Item "$DistPath\price_checker.db" "$BACKEND_DIR\data\price_checker.db" -Force
        Write-OK "price_checker.db copiado (data/ e backend/data/)"
    }
} else {
    Write-Warn "DistPath nao informado. Copie .env para $BACKEND_DIR\.env manualmente."
}

# ---------- 12. FRONTEND ----------
Write-Step "12/13 - Copiando frontend..."
if ($DistPath -and (Test-Path "$DistPath\dist")) {
    if (-not (Test-Path $FRONTEND_DIR)) { New-Item -ItemType Directory -Path $FRONTEND_DIR -Force | Out-Null }
    $distDest = "$FRONTEND_DIR\dist"
    if (Test-Path $distDest) {
        Remove-Item -Recurse $distDest -Force
    }
    Copy-Item -Recurse "$DistPath\dist" $distDest
    Write-OK "Frontend dist copiado de $DistPath"
} else {
    Write-Warn "dist nao encontrado em $DistPath. Copie manualmente para $FRONTEND_DIR\dist\ depois."
}

# ---------- 13. SERVICOS ----------
Write-Step "13/13 - Registrando servicos Windows..."
if (!(Test-Path $NSSM)) {
    Write-Warn "NSSM nao encontrado em $NSSM. Registro de servicos pulado."
    Write-Warn "Baixe manualmente de $NssmUrl e extraia nssm.exe para $BIN"
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
    if (Test-Path $caddyPath) {
        & $NSSM install VitrineFrontend "$caddyPath" "run --config $BIN\Caddyfile"
        & $NSSM set VitrineFrontend AppDirectory $FRONTEND_DIR
        & $NSSM set VitrineFrontend AppStdout "$LOGS_DIR\caddy.log"
        & $NSSM set VitrineFrontend AppStderr "$LOGS_DIR\caddy-error.log"
        & $NSSM set VitrineFrontend Start SERVICE_AUTO_START
        & $NSSM set VitrineFrontend ObjectName LocalSystem
        & $NSSM set VitrineFrontend AppRestartDelay 5000
        Write-OK "Servico VitrineFrontend registrado"
    } else {
        Write-Warn "Caddy nao encontrado em $caddyPath - servico VitrineFrontend pulado"
    }

    # ---------- INICIAR ----------
    Write-Step "- Iniciando servicos..."
    & $NSSM start VitrineBackend
    Start-Sleep -Seconds 5
    if (Test-Path $caddyPath) {
        & $NSSM start VitrineFrontend
        Start-Sleep -Seconds 3
    }

    # ---------- HEALTH CHECK ----------
    Write-Step "- Verificando servicos..."
    $backendOk = $false
    $frontendOk = $false
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        $backendOk = $r.StatusCode -eq 200
    } catch {}
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        $frontendOk = $r.StatusCode -eq 200
    } catch {}

    if ($backendOk) { Write-OK "Backend OK - http://localhost:8000" }
    else { Write-Warn "Backend nao respondeu em http://localhost:8000 - veja $LOGS_DIR\backend.log" }

    if ($frontendOk) { Write-OK "Frontend OK - http://localhost:8080" }
    else { Write-Warn "Frontend nao respondeu em http://localhost:8080 - veja $LOGS_DIR\caddy.log" }
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
Write-Host "  Binarios:        $BIN (caddy.exe, nssm.exe)"
Write-Host "  Repositorio:     $CODE"
Write-Host "  Python:          $PYTHON_DIR"
Write-Host "  Dados (.env):    $DATA_DIR"
Write-Host ""
Write-Host "Comandos rapidos:"
Write-Host "  restart.bat      -> reinicia servicos"
Write-Host "  update.bat       -> git pull + copia configs"
Write-Host "  uninstall.ps1    -> remove tudo"
Write-Host ""
