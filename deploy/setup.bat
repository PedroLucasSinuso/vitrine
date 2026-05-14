@echo off
title Vitrine - Setup
cd /d "%~dp0"
set VITRINE=C:\Vitrine

echo ============================================
echo   Vitrine - Setup do Servidor
echo ============================================
echo.
echo Esse script configura o servidor Windows para
echo rodar o Vitrine em producao.
echo.
echo Requisitos:
echo   - Python Embedded 3.11+ (ja baixado em %VITRINE%\python\)
echo   - Caddy (ja baixado em %VITRINE%\code\caddy.exe)
echo   - NSSM (ja baixado em %VITRINE%\code\nssm.exe)
echo   - Cloudflared (ja instalado)
echo.
echo Pressione ENTER para continuar ou CTRL+C para cancelar.
pause >nul
echo.

REM ---- 1. Verificar estrutura ----
if not exist "%VITRINE%\python\python.exe" (
    echo [ERRO] Python nao encontrado em %VITRINE%\python\
    echo Baixe o "Windows embeddable package" em python.org e extraia em %VITRINE%\python\
    pause
    exit /b 1
)
if not exist "%~dp0caddy.exe" (
    echo [ERRO] caddy.exe nao encontrado junto com este script
    echo Baixe em https://caddyserver.com/download e coloque na pasta deploy\
    pause
    exit /b 1
)
if not exist "%~dp0nssm.exe" (
    echo [ERRO] nssm.exe nao encontrado junto com este script
    echo Baixe em https://nssm.cc/download e coloque na pasta deploy\
    pause
    exit /b 1
)
if not exist "%VITRINE%\code\.git" (
    echo [INFO] Clonando repositorio...
    git clone https://github.com/PedroLucasSinuso/vitrine.git "%VITRINE%\code"
    if errorlevel 1 (
        echo [ERRO] Falha ao clonar repositorio
        pause
        exit /b 1
    )
)
echo [OK] Estrutura verificada
echo.

REM ---- 2. Habilitar site-packages no Python Embedded ----
echo [2/6] Configurando Python Embedded...
set PYTHON_PTH=%VITRINE%\python\python._pth
if exist "%PYTHON_PTH%" (
    findstr /C:"#import site" "%PYTHON_PTH%" >nul
    if not errorlevel 1 (
        copy "%PYTHON_PTH%" "%PYTHON_PTH%.bak" >nul
        powershell -Command "(Get-Content '%PYTHON_PTH%') -replace '#import site', 'import site' | Set-Content '%PYTHON_PTH%'"
        echo [OK] site-packages habilitado
    ) else (
        echo [OK] site-packages ja habilitado
    )
)
echo.

REM ---- 3. Baixar get-pip e instalar pip ----
echo [3/6] Instalando pip...
"%VITRINE%\python\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile '%TEMP%\get-pip.py'"
    "%VITRINE%\python\python.exe" "%TEMP%\get-pip.py" --no-warn-script-location
    del "%TEMP%\get-pip.py" 2>nul
    echo [OK] pip instalado
) else (
    echo [OK] pip ja instalado
)
echo.

REM ---- 4. Instalar dependencias do backend ----
echo [4/6] Instalando dependencias do backend...
"%VITRINE%\python\python.exe" -m pip install -r "%~dp0requirements.txt" --no-warn-script-location
if errorlevel 1 (
    echo [AVISO] Algumas dependencias podem nao ter instalado corretamente
) else (
    echo [OK] Dependencias instaladas
)
echo.

REM ---- 5. Copiar configs ----
echo [5/6] Configurando ambiente...

if not exist "%VITRINE%\data\logs" mkdir "%VITRINE%\data\logs"

copy /Y "%~dp0Caddyfile" "%VITRINE%\code\Caddyfile" >nul
echo [OK] Caddyfile copiado

if exist "%VITRINE%\data\.env" (
    copy /Y "%VITRINE%\data\.env" "%VITRINE%\code\vitrine_backend\.env" >nul
    echo [OK] .env copiado de %VITRINE%\data\
) else (
    echo [AVISO] Arquivo .env nao encontrado em %VITRINE%\data\
    echo Crie o arquivo %VITRINE%\data\.env com as configuracoes necessarias
    echo Exemplo:
    echo   POSTGRES_URL=postgresql+psycopg2://usuario:senha@servidor:5432/banco
    echo   SQLITE_URL=sqlite:///./data/price_checker.db
    echo   JWT_SECRET=uma-chave-secreta-aqui
    echo   ALLOWED_ORIGINS=["http://localhost:8080"]
)
echo.

REM ---- 6. Registrar servicos no NSSM ----
echo [6/6] Registrando servicos Windows...

nssm stop VitrineBackend 2>nul
nssm remove VitrineBackend confirm 2>nul
nssm install VitrineBackend "%VITRINE%\python\python.exe" "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"
nssm set VitrineBackend AppDirectory "%VITRINE%\code\vitrine_backend"
nssm set VitrineBackend AppEnvironmentExtra PYTHONPATH=%VITRINE%\code\vitrine_backend;%VITRINE%\python\Lib\site-packages
nssm set VitrineBackend AppStdout "%VITRINE%\data\logs\backend.log"
nssm set VitrineBackend AppStderr "%VITRINE%\data\logs\backend-error.log"
nssm set VitrineBackend Start SERVICE_AUTO_START
nssm set VitrineBackend ObjectName LocalSystem
nssm set VitrineBackend AppRestartDelay 5000
echo [OK] Servico VitrineBackend registrado

nssm stop VitrineFrontend 2>nul
nssm remove VitrineFrontend confirm 2>nul
md "%VITRINE%\code" 2>nul
copy /Y "%~dp0nssm.exe" "%VITRINE%\code\nssm.exe" >nul
copy /Y "%~dp0caddy.exe" "%VITRINE%\code\caddy.exe" >nul

nssm install VitrineFrontend "%VITRINE%\code\caddy.exe" "run --config %VITRINE%\code\Caddyfile"
nssm set VitrineFrontend AppDirectory "%VITRINE%\code"
nssm set VitrineFrontend AppStdout "%VITRINE%\data\logs\caddy.log"
nssm set VitrineFrontend AppStderr "%VITRINE%\data\logs\caddy-error.log"
nssm set VitrineFrontend Start SERVICE_AUTO_START
nssm set VitrineFrontend ObjectName LocalSystem
nssm set VitrineFrontend AppRestartDelay 5000
echo [OK] Servico VitrineFrontend registrado

echo.
echo ============================================
echo   Setup concluido!
echo ============================================
echo.
echo Proximos passos:
echo   1. Verifique se o .env esta correto
echo   2. Copie o frontend buildado para %VITRINE%\code\vitrine_frontend\dist\
echo   3. Execute start.bat para iniciar os servicos
echo   4. Acesse http://localhost:8080
echo.
echo Para configurar o Cloudflare Tunnel:
echo   cloudflared tunnel login
echo   cloudflared tunnel create vitrine
echo   cloudflared tunnel route dns vitrine seu-dominio.com
echo   cloudflared service install
echo.
pause
