@echo off
title Vitrine - Parando
echo Parando servicos Vitrine...
nssm stop VitrineFrontend
nssm stop VitrineBackend
echo Servicos parados.
pause
