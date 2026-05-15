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

> Projeto desenvolvido para um problema real: operadores precisam de informações rápidas sem depender do banco principal.

---

## Stack

### Backend

| Camada | Tecnologia |
|--------|-----------|
| API | **FastAPI** |
| ORM | **SQLAlchemy 2.0** (mapped columns, relationships) |
| Validação | **Pydantic v2** |
| Config | **pydantic-settings** + `.env` |
| Cache | **SQLite** (offline-first) |
| Fonte | **PostgreSQL** |
| Auth | **JWT** (PyJWT) + **bcrypt** |
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
| Planilhas | **SheetJS** (xlsx) |
| Código de barras | **@zxing/browser** + **@zxing/library** |
| Cache | AbortController + stale-while-revalidate |

---

## Funcionalidades

| Módulo | Funcionalidades |
|--------|----------------|
| 🔍 **Consulta** | Busca por EAN, PLU, nome. Exibe preço, estoque, markup, margem |
| 🏷️ **Etiquetas** | Geração de etiquetas profissionais para impressão |
| 📋 **Inventário** | Sessões multi-usuário, código de convite, consolidado geral |
| 📊 **BI** | Dashboard, receita, ranking, curva ABC, análise SKU, trocas, perdas, consumo, distribuição temporal |
| 📈 **YoY** | Comparação ano contra ano nos KPIs do dashboard |
| 📎 **Exportação** | Excel (.xlsx) para todos os relatórios de BI e inventário |
| 📱 **Câmera** | Leitura contínua de código de barras via câmera do dispositivo |
| ⏰ **Agendamento** | ETL e relatórios agendados via WhatsApp/Email com intervalo configurável pela UI |
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
├── domain/              # Entidades ORM + Value Objects + Enums
│   ├── models/          # SQLAlchemy models
│   ├── value_objects/   # Codigo (validação EAN/PLU)
│   └── enums.py         # RolesEnum
├── application/         # Casos de uso
│   ├── services/        # Regras de negócio
│   ├── bi/              # Business Intelligence
│   ├── etl/             # Pipeline de sincronização
│   └── scheduler/       # Agendamento dinâmico
├── infrastructure/      # Banco, repositórios, PostgreSQL
├── api/                 # Rotas FastAPI + injeção de dependência
├── core/                # Config, logging, error handling
└── schemas/             # Pydantic DTOs (contratos da API)
```

### Frontend

Organização modular por funcionalidade com componentes reutilizáveis:

```
src/
├── api/          # Axios instance + módulos de endpoint
├── components/   # Componentes reutilizáveis (UI, BI, leitor)
├── hooks/        # Custom hooks (auth, toast, countUp)
├── pages/        # Páginas (consulta, admin, BI, login)
├── stores/       # Cache frontend (stale-while-revalidate)
├── types/        # TypeScript interfaces
└── utils/        # Formatadores, CSV
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
| Códigos | Validação EAN-13/8, PLU, checksum |
| BI | KPIs, receita, ranking, curva ABC, SKU, trocas, exportação |
| Inventário | Sessões, itens, consolidado multi-usuário |
| ETL | Transformação de dados |
| CORS | Headers em requisições OPTIONS |

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
| **Value Object `Codigo`** | Encapsula validação e normalização de EAN/PLU, isolando do service |
| **Cache frontend com AbortController** | Stale-while-revalidate com cancelamento de requests duplicadas (evita waterfall em navegação de BI) |
| **Componentização do BI** | `KpiCard`, `PeriodoForm`, `BiSubNav` — componentes puros e reutilizáveis |

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
