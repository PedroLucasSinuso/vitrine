@echo off
title Vitrine - Iniciando
echo Iniciando servicos Vitrine...
nssm start VitrineBackend
if errorlevel 1 echo [AVISO] Falha ao iniciar backend (talvez ja esteja rodando)
timeout /t 3 >nul
nssm start VitrineFrontend
if errorlevel 1 echo [AVISO] Falha ao iniciar frontend (talvez ja esteja rodando)
echo.
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8000
echo.
pause
