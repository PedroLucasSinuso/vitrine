# Vitrine - Deploy Windows Server

## Instalação nova (1 comando)

> **Requisito:** Windows 10+ ou Server 2019+ com PowerShell 5.1+

### Preparar o pendrive

No PC de desenvolvimento, copiar para um pendrive:

```
pendrive\
├── .env                            ← credenciais (obrigatório)
├── price_checker.db                ← dados SQLite (opcional)
└── dist\                           ← build do frontend (npm run build)
```

### No servidor (PowerShell como Administrador)

```powershell
# Baixar a pasta deploy/ mais recente do GitHub
Invoke-WebRequest -Uri "https://github.com/PedroLucasSinuso/vitrine/archive/refs/heads/main.zip" -OutFile "$env:TEMP\vitrine.zip"
Expand-Archive -Path "$env:TEMP\vitrine.zip" -DestinationPath "$env:TEMP\vitrine" -Force
cd "$env:TEMP\vitrine\vitrine-main\deploy"

# Instalar (pendrive na letra D:\)
.\install.ps1 -DistPath D:\
```

O script faz **tudo automático**:

| Etapa | O que faz |
|-------|-----------|
| 1 | Instala Git for Windows (se não tiver) |
| 2 | Cria pastas `C:\Vitrine\` |
| 3 | Baixa Python embeddable 3.11 |
| 4 | Baixa Caddy (servidor web) |
| 5 | Detecta NSSM do sistema ou baixa |
| 6 | `git clone` do repositório |
| 7 | Habilita `site-packages` no Python |
| 8 | Instala `pip` |
| 9 | Instala dependências Python |
| 10 | Copia configurações (Caddyfile) |
| 11 | Copia `.env` e dados do pendrive |
| 12 | Copia `dist/` do frontend |
| 13 | Registra serviços Windows (NSSM) |
| — | Inicia os serviços |

**Pronto.** Acessar: `http://localhost:8080`

---

## Desinstalar

```powershell
.\uninstall.ps1
```

Para serviços, remove do NSSM, e pergunta se quer deletar `C:\Vitrine\`.

---

## Sem pendrive

Se não tiver pendrive, rode sem `-DistPath` e copie os arquivos depois:

```powershell
.\install.ps1
# Depois:
#   Copie .env  → C:\Vitrine\data\.env
#   Copie dist\ → C:\Vitrine\code\vitrine_frontend\dist\
```

---

## Gerenciamento diário

| Ação | Comando |
|------|---------|
| Iniciar serviços | `start.bat` |
| Parar serviços | `stop.bat` |
| Reiniciar | `restart.bat` |
| Atualizar (git pull) | `update.bat` |
| Ver logs | `C:\Vitrine\data\logs\backend.log` e `caddy.log` |

## Cloudflare Tunnel (acesso externo)

```batch
cloudflared tunnel login
cloudflared tunnel create vitrine
cloudflared tunnel route dns vitrine vitrine.seudominio.com
cloudflared service install
net start cloudflared
```
