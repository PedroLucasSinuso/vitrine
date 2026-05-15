@echo off
title Vitrine - Reiniciando
set VITRINE=C:\Vitrine
echo Reiniciando servicos Vitrine...
%VITRINE%\bin\nssm.exe restart VitrineFrontend
%VITRINE%\bin\nssm.exe restart VitrineBackend
echo.
echo Frontend: http://localhost:8080
echo Backend:  http://localhost:8000
echo.
pause
