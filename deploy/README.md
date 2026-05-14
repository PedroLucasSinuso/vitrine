# Vitrine - Deploy Windows Server

## Pré-requisitos

Baixar e colocar na pasta `deploy/`:

| Arquivo | Onde baixar |
|---------|-------------|
| `python-3.11.*-embed-amd64.zip` | https://www.python.org/downloads/windows/ → Windows embeddable package |
| `caddy.exe` | https://caddyserver.com/download (Windows amd64) |
| `nssm.exe` | https://nssm.cc/download |
| `cloudflared.exe` | `winget install cloudflare.cloudflared` ou https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ |

Também precisa do **Git for Windows**: https://git-scm.com/download/win

## Estrutura esperada no servidor

```
C:\Vitrine\
├── python\              ← Extraia o embeddable zip AQUI
│   └── python.exe
├── code\                ← Criado pelo setup (git clone + scripts)
│   ├── vitrine_backend\
│   ├── vitrine_frontend\dist\   ← Build do React (copiar manualmente)
│   ├── caddy.exe
│   ├── nssm.exe
│   └── Caddyfile
├── data\                ← CRIAR MANUALMENTE
│   ├── .env             ← Copiar do dev (ou criar do zero)
│   ├── price_checker.db ← Copiar do dev (SQLite)
│   └── logs\
└── deploy\              ← Esta pasta (pendrive / git clone)
    ├── setup.bat
    ├── Caddyfile
    ├── start.bat
    ├── stop.bat
    ├── restart.bat
    └── requirements.txt
```

## Setup passo a passo

### 1. Preparar o servidor

```batch
:: Criar pastas
mkdir C:\Vitrine\data\logs
mkdir C:\Vitrine\python

:: Extrair Python embedded em C:\Vitrine\python\
:: (extraia o .zip direto na pasta)

:: Copiar .env e price_checker.db do dev para C:\Vitrine\data\
```

### 2. Executar setup

```batch
:: No servidor, dentro da pasta deploy\
C:\Vitrine\deploy\setup.bat
```

O setup faz automaticamente:
- Clona o repositório em `C:\Vitrine\code\`
- Habilita site-packages no Python Embedded
- Instala pip
- Instala dependências Python
- Copia Caddyfile, nssm.exe, caddy.exe para `C:\Vitrine\code\`
- Copia `.env` de `C:\Vitrine\data\` para o backend
- Registra 2 serviços Windows (VitrineBackend + VitrineFrontend)

### 3. Build do frontend (no PC dev)

```bash
cd vitrine_frontend
npm run build
:: Copiar a pasta dist\ gerada para C:\Vitrine\code\vitrine_frontend\dist\ no servidor
```

### 4. Iniciar

```batch
C:\Vitrine\deploy\start.bat
```

Acessar: http://localhost:8080

### 5. Cloudflare Tunnel (acesso externo)

```batch
:: Autenticar (abre browser)
cloudflared tunnel login

:: Criar tunnel
cloudflared tunnel create vitrine

:: Apontar DNS (vitrine.seudominio.com -> tunnel)
cloudflared tunnel route dns vitrine vitrine.seudominio.com

:: Configurar como servico Windows (inicia automaticamente)
cloudflared service install

:: Iniciar
net start cloudflared
```

## Gerenciamento

| Ação | Comando |
|------|---------|
| Iniciar serviços | `start.bat` ou `nssm start VitrineBackend` + `nssm start VitrineFrontend` |
| Parar serviços | `stop.bat` ou `nssm stop VitrineBackend` + `nssm stop VitrineFrontend` |
| Reiniciar | `restart.bat` |
| Ver logs | `C:\Vitrine\data\logs\backend.log` e `caddy.log` |
| Status serviços | `nssm status VitrineBackend` ou services.msc |

## Atualizar (após alterações no código)

```batch
:: No servidor
cd C:\Vitrine\code
git pull

:: Se houver novas dependencias Python
C:\Vitrine\python\python.exe -m pip install -r C:\Vitrine\deploy\requirements.txt

:: Se houver alteracoes no frontend
:: Copiar dist\ novo para C:\Vitrine\code\vitrine_frontend\dist\

:: Reiniciar
C:\Vitrine\deploy\restart.bat
```

Os dados em `C:\Vitrine\data\` (SQLite + .env) **nunca são afetados** pelo git pull.
