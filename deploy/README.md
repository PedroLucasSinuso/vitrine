# ⚡ Vitrine — Deploy Windows Server

> Instalação automatizada em servidores Windows — Python, Caddy, NSSM, backend e frontend.

---

## 📋 Pré-requisitos

- Windows 10+ ou Server 2019+
- PowerShell 5.1+ (executado como **Administrador**)
- Acesso à internet no momento da instalação (Git, Python)

---

## 🚀 Instalação em 2 passos

### 1. Gerar o pacote (no PC de desenvolvimento)

```powershell
.\deploy\package.ps1
```

O script:
1. Builda o frontend (`npm run build`)
2. Baixa **Caddy** + **NSSM** já compilados
3. Empacota `.env`, `dist/` e a pasta `deploy/` num único arquivo:
   **`vitrine-deploy.zip`**

### 2. Instalar no servidor

```powershell
# Extrair o zip em qualquer pasta
Expand-Archive -Path vitrine-deploy.zip -DestinationPath C:\Vitrine -Force
cd C:\Vitrine\deploy

# Executar o instalador
.\install.ps1
```

> `-DistPath` não é mais necessário — o script detecta automaticamente a pasta de extração.

---

## 🔧 O que o instalador faz

| # | Etapa | Detalhes |
|---|-------|----------|
| 1 | **Git** | Verifica/instala Git for Windows |
| 2 | **Pastas + Firewall** | Cria `C:\Vitrine\`, libera porta **8080** no Firewall, adiciona `bin\` ao **PATH** |
| 3 | **Python** | Baixa e extrai Python **3.11 embeddable** |
| 4 | **Caddy** | Instala servidor web Caddy **v2.11.3** |
| 5 | **NSSM** | Instala o gerenciador de serviços Windows |
| 6 | **Git clone** | Clona o repositório do Vitrine |
| 7 | **site-packages** | Habilita `import site` no Python embeddable |
| 8 | **pip** | Instala pip + setuptools + wheel |
| 9 | **Dependências** | `pip install -r requirements.txt` |
| 10 | **Configs** | Copia `Caddyfile` para `C:\Vitrine\bin\` |
| 11 | **.env + dados** | Copia `.env` e `price_checker.db` do bundle |
| 12 | **Frontend** | Copia `dist/` do bundle |
| 13 | **Serviços** | Registra e inicia serviços no **NSSM** |

### ✅ Health check automático

Ao final, o script testa:
- **Backend** → `http://localhost:8000/docs`
- **Frontend** → `http://localhost:8080`

Cada serviço é marcado como **OK** (verde) ou exibe o caminho do log pra debug.

---

## 🏗️ Estrutura após instalação

```
C:\Vitrine\
├── bin\                      ← Binários (caddy.exe, nssm.exe, Caddyfile)
├── code\                     ← Repositório git clonado
│   ├── vitrine_backend\      
│   └── vitrine_frontend\dist\ ← Build do frontend
├── python\                   ← Python 3.11 embeddable
├── data\
│   ├── .env                  ← Credenciais
│   ├── logs\                 ← Logs dos serviços
│   │   ├── backend.log
│   │   └── caddy.log
│   └── price_checker.db      ← Dados SQLite
```

### Fluxo de requisição

```
Navegador → :8080 → Caddy
                        ├── /api/*    → (strip /api) → backend :8000
                        ├── /static/* → (strip /static) → backend :8000
                        └── /*        → file_server → dist/index.html (SPA)
```

---

## 🛠️ Gerenciamento diário

| Ação | Comando |
|------|---------|
| **Iniciar** serviços | `start.bat` |
| **Parar** serviços | `stop.bat` |
| **Reiniciar** serviços | `restart.bat` |
| **Atualizar** (git pull + deps) | `update.bat` |
| **Ver logs** | `C:\Vitrine\data\logs\backend.log` / `caddy.log` |

---

## 🗑️ Desinstalar

```powershell
.\deploy\uninstall.ps1
```

Para remoção silenciosa (sem confirmação):

```powershell
.\deploy\uninstall.ps1 -Force
```

O script:
1. Para e remove os serviços do NSSM
2. Tenta `sc delete` como fallback
3. Pergunta se deseja excluir `C:\Vitrine\` inteiro

---

## ☁️ Cloudflare Tunnel (acesso externo)

> ⚠️ Necessário ter um domínio configurado no Cloudflare.

```powershell
cloudflared tunnel login
cloudflared tunnel create vitrine
cloudflared tunnel route dns vitrine vitrine.exemplo.com
cloudflared service install
```
