@echo off
title Vitrine - Iniciando
set VITRINE=C:\Vitrine
echo Iniciando servicos Vitrine...
%VITRINE%\bin\nssm.exe start VitrineBackend
if errorlevel 1 echo [AVISO] Falha ao iniciar backend (talvez ja esteja rodando)
timeout /t 3 >nul
%VITRINE%\bin\nssm.exe start VitrineFrontend
if errorlevel 1 echo [AVISO] Falha ao iniciar frontend (talvez ja esteja rodando)
echo.
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8000
echo.
pause
