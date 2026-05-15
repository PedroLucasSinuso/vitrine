#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Remove o Vitrine do servidor: para servicos, remove registros do NSSM,
    e opcionalmente deleta C:\Vitrine\ inteiro.

.EXAMPLE
    .\uninstall.ps1
#>

$VITRINE = "C:\Vitrine"

$nssmGlobal = Get-Command nssm -ErrorAction SilentlyContinue
$NSSM = if ($nssmGlobal) { $nssmGlobal.Source } else { "$VITRINE\code\nssm.exe" }

Write-Host ">>> Desinstalando Vitrine..." -ForegroundColor Cyan

# Stop services
Write-Host "  Parando servicos..."
& $NSSM stop VitrineFrontend 2>$null
& $NSSM stop VitrineBackend 2>$null

# Remove services
Write-Host "  Removendo servicos..."
& $NSSM remove VitrineFrontend confirm 2>$null
& $NSSM remove VitrineBackend confirm 2>$null
Write-Host "  [OK] Servicos removidos" -ForegroundColor Green

# Ask before deleting files
$delete = Read-Host "`nDeletar C:\Vitrine\ inteiro? (s/N)"
if ($delete -eq "s" -or $delete -eq "S") {
    if (Test-Path $VITRINE) {
        Write-Host "  Deletando $VITRINE ..."
        Remove-Item -Recurse $VITRINE -Force
        Write-Host "  [OK] $VITRINE deletado" -ForegroundColor Green
    }
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  Desinstalacao concluida!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para remover o Git for Windows, va em:"
Write-Host "  Painel de Controle > Programas > Desinstalar > Git"
Write-Host ""
