@echo off
title Vitrine - Parando
set VITRINE=C:\Vitrine
echo Parando servicos Vitrine...
%VITRINE%\bin\nssm.exe stop VitrineFrontend
%VITRINE%\bin\nssm.exe stop VitrineBackend
echo Servicos parados.
pause
