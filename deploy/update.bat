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
"%VITRINE%\python\python.exe" -m pip install -r "%VITRINE%\code\deploy\requirements.txt" --no-warn-script-location
echo [OK] Dependencias atualizadas
echo.

REM Copiar .env e configs
echo [3/4] Copiando configuracoes...
if exist "%VITRINE%\data\.env" (
    copy /Y "%VITRINE%\data\.env" "%VITRINE%\code\vitrine_backend\.env" >nul
) else (
    echo [AVISO] .env nao encontrado em %VITRINE%\data\
)
copy /Y "%VITRINE%\code\deploy\Caddyfile" "%VITRINE%\bin\Caddyfile" >nul 2>&1
echo [OK] Configuracoes copiadas
echo.

REM Reiniciar servicos
echo [4/4] Reiniciando servicos...
%VITRINE%\bin\nssm.exe restart VitrineBackend
%VITRINE%\bin\nssm.exe restart VitrineFrontend
echo [OK] Servicos reiniciados
echo.

echo ============================================
echo   Atualizacao concluida!
echo   Frontend: http://localhost:8080
echo ============================================
echo.
pause
