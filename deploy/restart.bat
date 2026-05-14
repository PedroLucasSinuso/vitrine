@echo off
title Vitrine - Reiniciando
echo Reiniciando servicos Vitrine...
nssm restart VitrineFrontend
nssm restart VitrineBackend
echo.
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8000
echo.
pause
