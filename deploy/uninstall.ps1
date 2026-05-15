#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Remove o Vitrine do servidor: para servicos, remove registros do NSSM,
    e opcionalmente deleta C:\Vitrine\ inteiro.

.EXAMPLE
    .\uninstall.ps1
#>

param(
    [switch]$Force
)

$VITRINE = "C:\Vitrine"

$nssmGlobal = Get-Command nssm -ErrorAction SilentlyContinue
$nssmLocaL = "$VITRINE\bin\nssm.exe"
$NSSM = if ($nssmGlobal) { $nssmGlobal.Source } elseif (Test-Path $nssmLocaL) { $nssmLocaL } else { $null }

if (-not $NSSM) {
    Write-Host "[!] NSSM nao encontrado no sistema nem em $nssmLocaL" -ForegroundColor Yellow
    Write-Host "[!] Servicos podem precisar ser removidos manualmente com sc.exe" -ForegroundColor Yellow
}

Write-Host ">>> Desinstalando Vitrine..." -ForegroundColor Cyan

# Stop services
if ($NSSM) {
    Write-Host "  Parando servicos..."
    & $NSSM stop VitrineFrontend 2>$null
    & $NSSM stop VitrineBackend 2>$null
    Write-Host "  [OK] Servicos parados" -ForegroundColor Green

    Write-Host "  Removendo servicos..."
    & $NSSM remove VitrineFrontend confirm 2>$null
    & $NSSM remove VitrineBackend confirm 2>$null
    Write-Host "  [OK] Servicos removidos do NSSM" -ForegroundColor Green
}

# Try direct sc delete as fallback
sc delete VitrineFrontend 2>$null | Out-Null
sc delete VitrineBackend 2>$null | Out-Null

# Ask before deleting files
if ($Force) {
    $delete = "s"
} else {
    $delete = Read-Host "`nDeletar C:\Vitrine\ inteiro? (s/N)"
}
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
