<div align="center">
  <img src="vitrine_frontend/public/vitrine_logo.svg" alt="Vitrine" width="120" />
  <h1 align="center">Vitrine</h1>
  <p align="center">
    <strong>Sistema de consulta de produtos, BI e gestão para varejo</strong>
    <br />
    Plataforma moderna e offline-first para operadores de supermercado
  </p>

  [![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
  [![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
  [![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
  [![Tailwind](https://img.shields.io/badge/Tailwind_v4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
  [![Vite](https://img.shields.io/badge/Vite_8-646CFF?logo=vite&logoColor=white)](https://vite.dev)
  [![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
  [![License](https://img.shields.io/badge/Licen%C3%A7a-MIT-f5de19)](LICENSE)
</div>

---

## Visão geral

O **Vitrine** resolve um problema real de varejo: operadores precisam consultar preço, estoque, markup e margem de produtos rapidamente — via **código de barras (EAN)** ou **código interno (PLU)** — sem depender de conectividade contínua com o banco de dados principal.

Além da consulta rápida, oferece:

- 📊 **Business Intelligence** — relatórios analíticos de vendas com comparação **YoY** (ano contra ano)
- 📋 **Inventário multi-usuário** — contagem colaborativa com sessões, convites e consolidado
- 🏷️ **Geração de etiquetas** — formatação profissional para impressão
- 📱 **Leitor de código de barras via câmera** — sem hardware dedicado
- ⚙️ **Configurações via UI** — 6 abas com encriptação Fernet, fallback `.env` e teste de conexão
- 📧 **Notificações agendadas** — relatórios por WhatsApp (Twilio) e Email (SMTP) com templates Jinja2
- 🏠 **Enriquecimento de endereço** — consulta automática a BrasilAPI + ViaCEP (IBGE, DDD, coordenadas)

> Projeto desenvolvido para um problema real: operadores precisam de informações rápidas sem depender do banco principal.

---

## Stack

### Backend

| Camada | Tecnologia |
|--------|-----------|
| API | **FastAPI** |
| ORM | **SQLAlchemy 2.0** (mapped columns, relationships) |
| Validação | **Pydantic v2** |
| Config | **pydantic-settings** + `.env` + **SQLite** (UI editável) |
| Cache | **SQLite** (offline-first) |
| Fonte | **PostgreSQL** |
| Auth | **JWT** (PyJWT) + **bcrypt** |
| Scheduler | **APScheduler** (ETL + notificações dinâmicas) |
| Notificações | **Twilio** (WhatsApp) + **SMTP** (email) + **Jinja2** (templates) |
| Encriptação | **Fernet** (cryptography) — senhas em repouso |
| Testes | **pytest** |
| Gerenciador | **uv** |

### Frontend

| Camada | Tecnologia |
|--------|-----------|
| Framework | **React 19** |
| Linguagem | **TypeScript** |
| Build | **Vite 8** |
| Estilos | **Tailwind v4** (`@theme` custom, dark mode) |
| Gráficos | **Recharts** |
| HTTP | **Axios** |
| Ícones | **Lucide React** |
| Planilhas | **SheetJS** (xlsx) |
| Código de barras | **@zxing/browser** + **@zxing/library** |
| Cache | AbortController + stale-while-revalidate |
| Componentes | Design system próprio (Button, Card, Input, Modal, Skeleton, CmdK…) |

---

## Funcionalidades

| Módulo | Funcionalidades |
|--------|----------------|
| 🔍 **Consulta** | Busca por EAN, PLU, nome. Exibe preço, estoque, markup, margem |
| 🏷️ **Etiquetas** | Geração de etiquetas profissionais para impressão |
| 📋 **Inventário** | Sessões multi-usuário, código de convite, consolidado geral |
| 📊 **BI** | Dashboard, receita, ranking, curva ABC, análise SKU, trocas, perdas, consumo, distribuição temporal |
| 📈 **YoY** | Comparação ano contra ano com alinhamento de dia da semana (offset ±3d) e fallback 29/fev |
| 📎 **Exportação** | Excel (.xlsx) para todos os relatórios de BI e inventário |
| 📱 **Câmera** | Leitura contínua de código de barras via câmera do dispositivo |
| ⚙️ **Configurações** | 6 abas (Geral, Endereço, ERP, WhatsApp, Email, Sistema) com encriptação Fernet + fallback `.env` |
| 🔬 **Teste de conexão** | Testa ERP (PostgreSQL), WhatsApp, Email, Anthropic com feedback visual |
| 🏠 **Endereço** | Enriquecimento automático via BrasilAPI + ViaCEP (IBGE, DDD, coordenadas) |
| 📧 **Notificações** | Relatórios agendados via WhatsApp (Twilio) e Email (SMTP) com templates Jinja2 |
| 🔄 **ETL** | Pipeline PostgreSQL → Transform → SQLite com agendamento configurável (mín. 10 min) |
| ⏰ **Scheduler** | Jobs dinâmicos via APScheduler com intervalo definido pela UI |
| 🔐 **Auth** | JWT com 3 roles (operador, supervisor, admin) |

---

## Arquitetura

```
PostgreSQL (fonte)
    │
    ▼
ETL Pipeline
┌─────────────────────────────┐
│  Extract → Transform → Load │
└─────────────────────────────┘
    │
    ▼
SQLite (cache local — offline-first)
    │
    ▼
FastAPI (API REST — SQLAlchemy + Pydantic)
    │
    ▼
React 19 + TypeScript + Vite 8 (SPA)
    │
    ▼
Operador / Supervisor / Admin
```

### Backend

O backend segue **arquitetura em camadas** com separação clara de responsabilidades:

```
app/
├── domain/              # Entidades ORM + Value Objects + Enums + Domain Services
│   ├── models/          # SQLAlchemy models
│   ├── value_objects/   # Codigo (EAN/PLU), Endereco (CEP, UF, 3 níveis de dados)
│   ├── services/        # enriquecer_endereco (BrasilAPI + ViaCEP)
│   └── enums.py         # RolesEnum
├── application/         # Casos de uso
│   ├── services/        # Regras de negócio (auth, produto, config)
│   ├── bi/              # Business Intelligence (factory, loader, analytics, reporting)
│   ├── etl/             # Pipeline de sincronização (Extract → Transform → Load)
│   ├── scheduler/       # Agendamento dinâmico (APScheduler)
│   └── notifications/   # Email (SMTP), WhatsApp (Twilio), templates (Jinja2)
├── infrastructure/      # Banco (SQLite), repositórios, PostgreSQL loader
├── api/                 # Rotas FastAPI + injeção de dependência
├── core/                # Config, logging, error handling, rate limiter
└── schemas/             # Pydantic DTOs (contratos da API)
```

### Frontend

Organização modular por funcionalidade com design system próprio:

```
src/
├── api/          # Axios instance + módulos de endpoint (admin, auth, bi, produtos, …)
├── components/   # Design system (ui/) + feature-specific (bi/, scanner, admin)
│   └── ui/       # Button, Card, Input, Modal, Skeleton, CmdK, EmptyState…
├── hooks/        # Custom hooks (useAuth, useToast, useCountUp, useLocalStorage)
├── pages/        # Páginas (consulta, admin, BI, login, configurações, …)
│   └── bi/       # Dashboard, Ranking, Receita, CurvaAbc, Sku, Trocas, PerdasConsumo, Temporal
├── stores/       # Cache frontend (biCache com stale-while-revalidate + configStore)
├── types/        # TypeScript interfaces (admin, auth, bi, inventario, produto)
└── utils/        # Formatadores, cores, CSV
```

### Fluxo de requisição

```
Usuário (câmera / input)
    └─► React (consulta)
            └─► Axios GET /api/produtos/{codigo}
                    └─► Caddy reverse proxy (produção) / Vite proxy (dev)
                            └─► FastAPI Route → Service → Repository → SQLite
                    └─► JSON Response
            └─► React renderiza resultado
```

---

## Quick start (desenvolvimento)

```bash
# Clone
git clone https://github.com/PedroLucasSinuso/vitrine.git
cd vitrine

# Backend
cd vitrine_backend
cp .env.example .env        # Configure suas credenciais
uv sync                     # Instala dependências
uv run python -m app.etl.run_etl  # Popula cache SQLite
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (outro terminal)
cd vitrine_frontend
npm install
npm run dev                 # → http://localhost:5173
```

---

## Deploy em produção (Windows Server)

Deploy automatizado em servidor Windows limpo — sem precisar instalar Python, Node ou Docker manualmente:

| Componente | Função |
|-----------|--------|
| **Python Embedded** | Runtime portátil (~30 MB) |
| **Caddy** | Servidor web (1 .exe, zero config) |
| **NSSM** | Serviços Windows que iniciam com o sistema |
| **Cloudflare Tunnel** | Acesso HTTPS público (opcional) |

```powershell
# No PC de desenvolvimento, gere o pacote:
.\deploy\package.ps1
# → gera vitrine-deploy.zip

# No servidor, extraia e execute:
.\deploy\install.ps1
# → tudo automático: Git, Python, Caddy, NSSM, clone, deps, serviços
```

> 📖 Instruções detalhadas em [`deploy/README.md`](deploy/README.md)

---

## API

A documentação interativa da API (Swagger UI) fica disponível em:

```
http://localhost:8000/docs
```

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/token` | Login (JWT) |
| `GET` | `/produtos/{codigo}` | Consulta por EAN ou PLU |
| `GET` | `/produtos/busca?q=` | Busca por nome |
| `GET` | `/bi/kpis` | KPIs financeiros |
| `GET` | `/bi/kpis/comparativo` | KPIs com YoY |
| `GET` | `/bi/receita` | Receita por dimensão |
| `GET` | `/bi/curva-abc` | Classificação ABC |
| `GET` | `/bi/sku` | Análise detalhada de SKU |
| `POST` | `/admin/sync` | Disparar ETL manual |
| `GET` | `/admin/cache/status` | Status do cache (último sync, TTL) |
| `POST` | `/admin/testar-anthropic` | Testar conexão com Anthropic |
| `PATCH` | `/admin/endereco` | Atualizar endereço da loja |
| `GET` | `/config` | Listar configurações (admin) |
| `PUT` | `/config` | Atualizar configurações |
| `GET` | `/contatos/email` | Listar contatos de email |
| `POST` | `/contatos/email` | Adicionar contato de email |
| `GET` | `/contatos/whatsapp` | Listar contatos de WhatsApp |
| `POST` | `/contatos/whatsapp` | Adicionar contato de WhatsApp |

> 🔗 Lista completa de endpoints e parâmetros: [`docs/API.md`](docs/API.md) _(em breve)_ ou diretamente no Swagger UI.

### Autenticação

A API utiliza **JWT** com 3 níveis de acesso:

| Role | Acesso |
|------|--------|
| `operador` | Consulta, inventário (apenas bipar) |
| `supervisor` | Consulta completa + BI + inventário completo |
| `admin` | Tudo + gestão de usuários + configurações |

```bash
# Criar primeiro admin via CLI
cd vitrine_backend
uv run python -m app.cli admin "Admin" sua_senha
```

---

## Testes

```bash
cd vitrine_backend
uv run pytest
```

| Categoria | Casos |
|-----------|-------|
| Autenticação | Token, credenciais, registro, permissões |
| Produtos | Busca por código/nome, paginação, detalhes |
| Códigos | Validação EAN-13/8/12, PLU-6, checksum |
| BI | KPIs, receita, ranking, curva ABC, SKU, trocas, exportação |
| Inventário | Sessões, itens, consolidado multi-usuário |
| ETL | Transformação de dados |
| CORS | Headers em requisições OPTIONS |
| Config Service | CRUD, encriptação Fernet, fallback `.env`, senhas sensíveis |
| Cache Status | Admin com/sem registro, supervisor 403, operador 403, sem auth 401 |
| Contatos Email | CRUD completo |
| Contatos WhatsApp | CRUD completo |
| Value Objects | Endereco (CEP, UF, formatação, 3 níveis de dados) |

---

## Business Intelligence

### Relatórios disponíveis

- **Dashboard** — KPIs financeiros + ranking do período
- **Receita por dimensão** — grupo, família ou produto, com filtros hierárquicos
- **Ranking** — Top N produtos por receita ou quantidade
- **Curva ABC** — Classificação A/B/C automática
- **Análise SKU** — Receita diária, distribuição por hora, ranking de dias
- **Trocas** — Total, taxa e produtos mais trocados
- **Perdas e consumo** — Produtos com maior perda/consumo
- **Distribuição temporal** — Por hora e dia da semana
- **Exportação** — Todos os relatórios em `.xlsx`

### YoY (comparação ano contra ano)

O dashboard compara KPIs do período atual com o mesmo período do ano anterior:

| KPI | Atual | Anterior | Variação |
|-----|-------|----------|----------|
| Receita Total | R$ 1.250.000 | R$ 1.100.000 | ▲ 13.6% |
| Ticket Médio | R$ 47,80 | R$ 45,20 | ▲ 5.8% |
| Itens por Venda | 8.2 | 8.5 | ▼ -3.5% |
| Margem Média | 34.2% | 33.8% | ▲ 1.2% |

> Endpoint dedicado `GET /bi/kpis/comparativo` com `VariacaoKpi` tipado e badges visuais no frontend (▲ verde / ▼ vermelho).

**Ajustes de qualidade:** A data comparativa é calculada com `_ajustar_mesmo_dia_semana()` que desloca ±3 dias para alinhar ao mesmo dia da semana do período atual — padrão de indústria para varejo. Datas 29/fevereiro têm fallback automático para 28/fevereiro em ano não bissexto. O filtro de hora futura é aplicado simetricamente nos dois períodos (antes só no anterior, o que inflava o resultado atual).

---

## ETL

Pipeline de sincronização do PostgreSQL para o SQLite local:

1. **Extract** — queries SQL externas no Postgres
2. **Transform** — agrupa códigos, converte para DTOs
3. **Load** — trunca e reinsere no SQLite, registra timestamp

```bash
cd vitrine_backend
uv run python -m app.etl.run_etl
```

Pode ser executado manualmente, via scheduler interno (intervalo configurável pela UI, mínimo 10 min) ou via API (`POST /admin/sync`).

---

## Design decisions

| Decisão | Motivo |
|---------|--------|
| **SQLite como cache** | Desacopla API da disponibilidade do PostgreSQL. Consultas locais são rápidas e não geram carga no banco operacional |
| **Separação Model / Schema** | `Produto` (ORM) ≠ `ProdutoResponse` (Pydantic). Métricas computadas (`markup`, `margem`) como `@property` no model |
| **Camadas domain/application/infrastructure** | Isola regras de negócio de detalhes técnicos (SOLID) |
| **Injeção de dependência** | Sessão gerenciada por `Depends` do FastAPI, repositório desacoplado do ciclo de vida da request |
| **Value Objects (`Codigo`, `Endereco`)** | Encapsulam validação e invariantes do domínio (EAN/PLU, CEP/UF) sem poluir o service |
| **Domain Services (`enriquecer_endereco`)** | Orquestra chamadas externas (BrasilAPI → ViaCEP) mantendo o VO imutável |
| **Fernet para senhas em repouso** | ConfigService encripta valores sensíveis (senha ERP) com chave de `ERPS_ENCRYPTION_KEY` — única proteção em DB SQLite sem segredo |
| **Sentinel `***configurado***`** | A UI exibe `••••••` em vez de retornar a senha descriptada; o valor enviado de volta é ignorado pelo backend se igual ao sentinel |
| **ConfigService com fallback `.env`** | Lê de `.env` se a chave não existe no banco; ao salvar pela UI, escreve no SQLite e sobrescreve o `.env` |
| **Templates Jinja2 para relatórios** | `relatorio_email.j2` / `relatorio_semanal.j2` permitem customizar o HTML sem recompilar |
| **APScheduler para jobs dinâmicos** | ETL e notificações agendados com intervalo configurável pela UI (mín. 10 min), sem reiniciar o servidor |
| **Cache frontend com AbortController** | Stale-while-revalidate com cancelamento de requests duplicadas (evita waterfall em navegação de BI) |
| **Componentização do BI** | `KpiCard`, `PeriodoForm`, `BiSubNav`, `BiSideRail` — componentes puros e reutilizáveis |
| **Design system próprio (`ui/`)** | `Button`, `Card`, `Input`, `Modal`, `Skeleton`, `CmdK` — consistência visual sem dependência pesada de UI library |

---

## Licença

Distribuído sob licença **MIT**. Veja [`LICENSE`](LICENSE) para mais informações.

---

<div align="center">
  <br />
  <p>
    Desenvolvido por <strong>Pedro Lucas</strong>
    <br />
    <a href="mailto:pedrolucas.sinuso@gmail.com">pedrolucas.sinuso@gmail.com</a>
    &nbsp;·&nbsp;
    <a href="https://linkedin.com/in/pedro-sinuso">LinkedIn</a>
    &nbsp;·&nbsp;
    <a href="https://github.com/PedroLucasSinuso">GitHub</a>
  </p>
  <p>
    <sub>Gostou do projeto? ⭐ Deixe uma estrela no repositório!</sub>
  </p>
  <br />
</div>
