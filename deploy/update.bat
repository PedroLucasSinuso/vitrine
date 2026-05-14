@echo off
title Vitrine - Atualizando
cd /d "%~dp0"
set VITRINE=C:\Vitrine

echo ============================================
echo   Vitrine - Atualizar
echo ============================================
echo.

REM Pull do repositorio
echo [1/4] Atualizando codigo...
cd /d "%VITRINE%\code"
git pull
if errorlevel 1 (
    echo [ERRO] Falha no git pull. Resolva os conflitos manualmente.
    pause
    exit /b 1
)
echo [OK] Codigo atualizado
echo.

REM Dependencias Python
echo [2/4] Atualizando dependencias Python...
"%VITRINE%\python\python.exe" -m pip install -r "%~dp0requirements.txt" --no-warn-script-location
echo [OK] Dependencias atualizadas
echo.

REM Copiar .env se necessario
echo [3/4] Verificando .env...
if exist "%VITRINE%\data\.env" (
    copy /Y "%VITRINE%\data\.env" "%VITRINE%\code\vitrine_backend\.env" >nul
) else (
    echo [AVISO] .env nao encontrado em %VITRINE%\data\
)
echo [OK] .env verificado
echo.

REM Reiniciar servicos
echo [4/4] Reiniciando servicos...
nssm restart VitrineBackend
nssm restart VitrineFrontend
echo [OK] Servicos reiniciados
echo.

echo ============================================
echo   Atualizacao concluida!
echo   Frontend: http://localhost:8080
echo ============================================
echo.
pause
