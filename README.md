# Vitrine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6.svg)](https://www.typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema completo de consulta de produtos, Business Intelligence, etiquetas, inventário multi-usuário e gestão para varejo. **Vitrine** (antigo Price Checker) unifica um backend em Python/FastAPI com um frontend React para oferecer uma plataforma moderna e offline-first para operadores de supermercado.

> Projeto de portfólio desenvolvido para resolver um problema real de varejo: operadores precisam consultar informações rápidas sem depender de conectividade constante com o banco principal.

---

## Visão geral

O **Vitrine** resolve um problema real de varejo: operadores precisam consultar preço, estoque, markup e margem de produtos rapidamente — via código de barras (EAN) ou código interno (PLU) — sem depender de conectividade contínua com o banco de dados principal. Inclui também um módulo completo de **Business Intelligence** com relatórios analíticos de vendas, incluindo **comparação YoY** (ano contra ano) para análise de sazonalidade e crescimento.

### Arquitetura

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
  SQLite (cache local)
      │
      ▼
  FastAPI (API REST)
      │
      ▼
  React 19 + TypeScript + Vite 8 (Frontend SPA)
      │
      ▼
  Operador / Supervisor / Admin
```

---

## Stack

### Backend

| Camada | Tecnologia |
|---|---|
| API | FastAPI |
| ORM | SQLAlchemy 2.0 (Mapped columns, relacionamentos) |
| Cache | SQLite |
| Fonte de dados | PostgreSQL |
| Validação | Pydantic v2 |
| Configuração | pydantic-settings + `.env` |
| Testes | pytest |
| Autenticação | JWT (PyJWT) + bcrypt |
| Gerenciador | uv |

### Frontend

| Camada | Tecnologia |
|---|---|
| Framework | React 19 |
| Linguagem | TypeScript 6 |
| Build | Vite 8 |
| Estilos | Tailwind v4 (dark mode, `@theme` custom) |
| Gráficos | Recharts |
| HTTP | Axios |
| Planilhas | SheetJS (xlsx) |
| Código de barras | @zxing/browser + @zxing/library |
| Cache frontend | AbortController + stale-while-revalidate |

---

## Arquitetura

O backend segue arquitetura em camadas com separação clara de responsabilidades, aplicando princípios SOLID e DRY. O frontend segue uma organização modular por funcionalidade.

### Backend (`vitrine_backend/`)

```
app/
├── domain/
│   ├── models/              # Entidades ORM (SQLAlchemy)
│   │   ├── cache_status.py
│   │   ├── configuracao.py
│   │   ├── inventario.py
│   │   ├── produto.py
│   │   └── usuario.py
│   ├── value_objects/       # Objetos de valor (ex: validação de códigos)
│   │   └── codigo.py
│   └── enums.py             # RolesEnum (escalável para SaaS)
├── application/
│   ├── services/            # Regras de negócio
│   │   ├── auth_service.py
│   │   └── produto_service.py
│   ├── bi/                  # Business Intelligence (relatórios)
│   │   ├── domain/          # Domínios de negócio (vendas, trocas, etc.)
│   │   ├── queries/         # SQLs externos
│   │   └── reporting/       # Relatórios por dimensão
│   ├── etl/
│   │   ├── extract/         # Extração do Postgres
│   │   ├── transform/       # Transformação para DTOs
│   │   ├── load/            # Persistência no SQLite
│   │   ├── queries/         # Queries SQL (QueryLoader)
│   │   ├── dto.py
│   │   ├── interfaces.py
│   │   ├── pipeline.py      # Orquestrador ETL
│   │   └── query_loader.py
│   ├── loaders/
│   │   └── query_loader.py  # BaseQueryLoader
│   └── utils/
│       ├── jwt_handler.py
│       └── security.py
├── infrastructure/
│   ├── db/                  # SQLAlchemy setup + session factory
│   │   ├── bootstrap.py
│   │   ├── database.py
│   │   └── session.py
│   ├── repositories/        # Acesso a dados
│   │   ├── interfaces.py
│   │   ├── produto_repository.py
│   │   └── usuario_repository.py
│   └── postgres/            # Executor de queries
│       └── loader.py
├── api/
│   ├── deps.py              # Injeção de dependência + require_role helper
│   └── routes/              # Endpoints FastAPI
│       ├── admin.py
│       ├── auth.py
│       ├── bi.py            # Business Intelligence (todos os endpoints)
│       ├── cache_status.py
│       ├── configuracoes.py
│       ├── inventario.py    # Inventário multi-usuário com sessões
│       └── produtos.py
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── error_handler.py
│   ├── logging_config.py
│   └── timer.py
├── schemas/                 # Schemas Pydantic (contratos da API)
│   ├── auth_schema.py
│   ├── bi_schema.py         # DTOs de BI
│   ├── configuracao_schema.py
│   ├── inventario_schema.py
│   ├── produto_schema.py
│   ├── sync_schema.py
│   └── usuario_schema.py
├── cli.py                   # CLI (create-admin)
├── main.py
└── etl/
    └── run_etl.py
```

### Frontend (`vitrine_frontend/`)

```
src/
├── api/                     # Cliente HTTP + funções por módulo
│   ├── client.ts            # Axios instance + interceptors (auth, 401 redirect)
│   ├── admin.ts             # Sync, configurações, inventário (sessões + itens)
│   ├── auth.ts              # Login
│   ├── bi.ts                # KPIs, receita, ranking, SKU, trocas, etc.
│   ├── produtos.ts          # Consulta de produtos por código/nome
│   └── usuarios.ts          # CRUD de usuários
├── components/              # Componentes reutilizáveis
│   ├── AdminHeader.tsx      # Header com nav grid, dropdown, logo, dark mode
│   ├── LeitorCodigo.tsx     # Leitor de código de barras via câmera
│   ├── ProtectedRoute.tsx   # Guard de rota por role
│   ├── ToastContainer.tsx
│   ├── bi/                  # Componentes de BI
│   │   ├── BiSubNav.tsx
│   │   ├── KpiCard.tsx      # KPI opcional com badge de variação (▲▼ YoY)
│   │   └── PeriodoForm.tsx  # Seletor de período com presets
│   └── ui/
│       ├── ScrollToTop.tsx
│       └── Skeleton.tsx
├── hooks/                   # Hooks customizados
│   ├── useAuth.ts           # Auth context (JWT decode, role, expiração)
│   ├── useCountUp.ts        # Animação de contagem
│   ├── useLocalStorage.ts
│   └── useToast.tsx         # Sistema de toast (feedback visual)
├── pages/                   # Páginas
│   ├── Admin.tsx            # Sync ETL
│   ├── Busca.tsx            # Consulta de produtos por código/nome
│   ├── Configuracoes.tsx    # Configurações do sistema (admin)
│   ├── Etiquetas.tsx        # Geração de etiquetas
│   ├── Home.tsx             # Pós-login com cards de navegação
│   ├── Inventario.tsx       # Inventário multi-usuário com sessões
│   ├── Login.tsx
│   ├── NotFound.tsx
│   ├── Usuarios.tsx         # Gestão de usuários (admin)
│   └── bi/                  # BI (Dashboard, Receita, Ranking, etc.)
│       ├── Dashboard.tsx    # Dashboard com toggle YoY
│       └── ...
├── stores/
│   └── biCache.tsx          # Cache de requests BI (abort + stale-while-revalidate)
├── types/                   # Tipos TypeScript
│   ├── admin.ts
│   ├── auth.ts
│   ├── bi.ts
│   ├── index.ts
│   ├── inventario.ts
│   └── produto.ts
└── utils/
    ├── csv.ts
    └── formatters.ts
```

**Fluxo de uma requisição:**

```
Usuário (câmera / input)
    └─► React (Busca.tsx)
            └─► Axios GET /api/produtos/{codigo}
                    └─► FastAPI Route (produtos.py)
                            └─► ProdutoService
                                    └─► Codigo (valida e normaliza o código)
                                    └─► ProdutoRepository
                                            └─► SQLite (cache)
                                    └─► ProdutoResponse (Pydantic)
                            └─► JSON Response
            └─► React renderiza resultado
```

---

## Endpoints da API

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| `POST` | `/auth/token` | Login e geração de token JWT | Público |
| `POST` | `/auth/register` | Criar novo usuário | Admin |
| `GET` | `/auth/usuarios` | Lista todos os usuários | Admin |
| `PATCH` | `/auth/usuarios/{usuario_id}` | Atualiza dados de um usuário | Admin |
| `DELETE` | `/auth/usuarios/{usuario_id}` | Exclui um usuário | Admin |
| `GET` | `/produtos/` | Lista produtos com paginação | Autenticado |
| `GET` | `/produtos/busca` | Busca produtos por nome (`?q=`, `limit`, `offset`) | Autenticado |
| `GET` | `/produtos/{codigo}` | Busca produto por EAN ou PLU | Autenticado |
| `GET` | `/produtos/{codigo}/completo` | Busca produto com custo, markup e margem | Supervisor/Admin |
| `POST` | `/produtos/nao-encontrado` | Registra produto não encontrado | Autenticado |
| `GET` | `/status/` | Data/hora da última atualização do cache | Público |
| `POST` | `/admin/sync` | Dispara sync em background | Admin |
| `GET` | `/admin/sync/{job_id}` | Verifica status de um job | Admin |
| `GET` | `/admin/sync/` | Lista histórico de jobs | Admin |
| `GET` | `/bi/kpis` | KPIs financeiros do período | Supervisor/Admin |
| `GET` | `/bi/kpis/comparativo` | KPIs com comparação YoY (ano anterior) | Supervisor/Admin |
| `GET` | `/bi/receita` | Receita por dimensão | Supervisor/Admin |
| `GET` | `/bi/quantidade` | Quantidade vendida por dimensão | Supervisor/Admin |
| `GET` | `/bi/curva-abc` | Classificação ABC por dimensão | Supervisor/Admin |
| `GET` | `/bi/ranking` | Ranking de produtos | Supervisor/Admin |
| `GET` | `/bi/sku` | Análise detalhada de SKU | Supervisor/Admin |
| `GET` | `/bi/trocas` | Relatório de trocas | Supervisor/Admin |
| `GET` | `/bi/perdas` | Relatório de perdas | Supervisor/Admin |
| `GET` | `/bi/consumo` | Relatório de consumo | Supervisor/Admin |
| `GET` | `/bi/diario` | Série diária de receita/quantidade | Supervisor/Admin |
| `GET` | `/bi/diario/produto` | Série diária de um produto | Supervisor/Admin |
| `GET` | `/bi/temporal/hora` | Distribuição por hora | Supervisor/Admin |
| `GET` | `/bi/temporal/dia-semana` | Distribuição por dia da semana | Supervisor/Admin |
| `GET` | `/bi/exportar/excel` | Exporta relatório como `.xlsx` | Supervisor/Admin |
| `GET` | `/admin/inventario/sessoes` | Lista sessões ativas | Autenticado |
| `POST` | `/admin/inventario/sessoes` | Cria nova sessão | Supervisor/Admin |
| `POST` | `/admin/inventario/sessoes/entrar` | Entrar em sessão por código de convite | Autenticado |
| `PATCH` | `/admin/inventario/sessoes/{id}` | Encerrar sessão | Supervisor/Admin |
| `GET` | `/admin/inventario/sessoes/{id}/itens` | Lista itens da sessão | Autenticado |
| `POST` | `/admin/inventario/sessoes/{id}/itens` | Adicionar/bipar item | Autenticado |
| `PATCH` | `/admin/inventario/sessoes/{id}/itens/{codigo}` | Atualizar quantidade | Autenticado |
| `DELETE` | `/admin/inventario/sessoes/{id}/itens` | Limpar itens do usuário | Autenticado |
| `GET` | `/admin/inventario/consolidado-geral` | Soma de todas as sessões ativas | Supervisor/Admin |

### Parâmetros de listagem

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `limit` | int | 50 | Máximo de resultados (clamped entre 1–100) |
| `offset` | int | 0 | Paginação por offset |

### Exemplo de resposta — `GET /produtos/{codigo}`

```json
{
  "codigo_chamada": "000123",
  "nome": "Smartphone XYZ",
  "grupo": "Eletrônicos",
  "familia": "Smartphones",
  "preco_venda": 1599.90,
  "preco_custo": 980.00,
  "estoque": 42.0,
  "markup": 0.6326,
  "margem": 0.3876,
  "codigo_buscado": "7891234567890"
}
```

### Códigos de status

| Status | Situação |
|---|---|
| `200` | Produto encontrado |
| `400` | Código inválido (formato não reconhecido) |
| `404` | Produto não encontrado no cache |

---

## Rotas do Frontend

| Rota | Página | Descrição | Acesso |
|---|---|---|---|
| `/login` | Login | Autenticação do usuário | Público |
| `/` | Home | Cards de navegação por role | Autenticado |
| `/busca` | Busca | Consulta de produtos por código/nome | Autenticado |
| `/etiquetas` | Etiquetas | Geração de etiquetas | Supervisor/Admin |
| `/inventario` | Inventário | Sessões de contagem multi-usuário | Autenticado |
| `/configuracoes` | Configurações | Upload de logo, nome do mercado, tema | Admin |
| `/admin` | Admin | Sync ETL manual | Admin |
| `/usuarios` | Usuários | CRUD de usuários | Admin |
| `/bi/dashboard` | Dashboard | KPIs financeiros com toggle YoY | Supervisor/Admin |
| `/bi/receita` | Receita | Receita por dimensão | Supervisor/Admin |
| `/bi/ranking` | Ranking | Top N produtos | Supervisor/Admin |
| `/bi/curva-abc` | Curva ABC | Classificação A/B/C | Supervisor/Admin |
| `/bi/sku` | Análise SKU | Detalhamento por produto | Supervisor/Admin |
| `/bi/trocas` | Trocas | Relatório de trocas | Supervisor/Admin |
| `/bi/perdas` | Perdas | Relatório de perdas | Supervisor/Admin |
| `/bi/consumo` | Consumo | Relatório de consumo | Supervisor/Admin |

---

## Validação de códigos

A classe `Codigo` em `app/domain/value_objects/codigo.py` valida e normaliza automaticamente os formatos suportados:

| Formato | Tamanho | Validação |
|---|---|---|
| EAN-13 | 13 dígitos | Checksum módulo 10 |
| EAN-12 | 12 dígitos | Checksum módulo 10 |
| EAN-8 | 8 dígitos | Checksum módulo 10 |
| PLU-6 | 6 dígitos | Apenas numérico |

Espaços e hífens são removidos automaticamente na normalização. O campo `codigo_buscado` na resposta reflete o código após normalização.

---

## Autenticação

A API utiliza **JWT (JSON Web Token)** para controle de acesso. O fluxo é:

1. **Login** — `POST /auth/token` com `username` e `password` retorna o `access_token`
2. **Uso** — informe o token no header `Authorization: Bearer <token>`

### Roles e Permissões

O sistema usa `RolesEnum` (enum escalável) para controle de acesso:

| Role | Descrição | Permissões |
|---|---|---|
| `operador` | Consulta básica | Vê preço, estoque (sem custo/margem), inventário (apenas bipar) |
| `supervisor` | Gerência | Consulta completa + relatórios + inventário completo |
| `admin` | Administrador | Tudo + gerenciamento de usuários + configurações |

O `require_role()` helper centraliza a lógica de permissões, eliminando strings hardcoded.

### Criando o primeiro admin

```bash
cd vitrine_backend
uv run python -m app.cli admin "Administrador" sua_senha
```

---

## Inventário Multi-usuário

O módulo de inventário permite contagem colaborativa com sessões:

### Conceito

- **Supervisor** cria uma sessão, obtém um código de convite de 6 caracteres e distribui para os operadores
- **Operadores** entram na sessão pelo código e bipam produtos — cada um vê apenas seus próprios itens
- **Consolidado** — supervisor vê a soma total de todos os operadores dentro da sessão
- **Relatório Geral** (`GET /consolidado-geral`) — soma todos os itens de **todas as sessões ativas**, agrupando por código

### Regras de negócio

- Mesmo código bipado **pelo mesmo usuário** na mesma sessão → soma (upsert)
- Mesmo código bipado **por usuários diferentes** → soma apenas no consolidado
- Quantidade `≤ 0` na atualização → remove o item
- Apenas o **criador** pode encerrar a sessão
- Sessão encerrada não aparece na lista, mas os dados persistem

### Exportação

| Formato | Onde | Conteúdo | Uso |
|---|---|---|---|
| `.txt` | Dentro da sessão | `codigo;quantidade` | Coletor / sistema legado |
| `.xlsx` | Dentro da sessão | `código \| grupo \| família \| produto` | Planilha Excel |
| `.txt` | Consolidado Geral | `codigo;quantidade` | ERP (ajuste de estoque apurado) |
| `.xlsx` | Consolidado Geral | `código \| produto \| grupo \| família \| quantidade` | Análise humana |

---

## Configuração

### Backend (`.env` em `vitrine_backend/`)

```env
POSTGRES_URL=postgresql://usuario:senha@host:5432/banco
SQLITE_URL=sqlite:///./data/vitrine.db
CACHE_REFRESH_INTERVAL=3600
JWT_SECRET=sua-chave-secreta-grande-e-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=["http://localhost:5173"]
ALLOW_ORIGIN_REGEX=https://.*\.trycloudflare\.com
```

| Variável | Obrigatória | Descrição |
|---|---|---|
| `POSTGRES_URL` | Sim (para ETL) | Connection string do banco de origem |
| `SQLITE_URL` | Sim | Caminho do banco SQLite local |
| `CACHE_REFRESH_INTERVAL` | Não | Intervalo de refresh do cache em segundos (padrão: 3600) |
| `JWT_SECRET` | Sim | Chave secreta para assinar tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não | Tempo de expiração do token (padrão: 60) |
| `ALLOWED_ORIGINS` | Sim | Lista de origens permitidas para CORS |
| `ALLOW_ORIGIN_REGEX` | Não | Regex de origens permitidas para CORS (ex: tunnel Cloudflare) |

### Frontend (`.env` em `vitrine_frontend/`)

```env
VITE_API_URL=/api
```

- Em desenvolvimento, o Vite faz proxy de `/api` para `http://localhost:8000` e `/static` para `http://localhost:8000/static`
- Em produção, a API e os arquivos estáticos devem estar no mesmo domínio ou atrás de um reverse proxy

---

## Instalação e execução

### Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/PedroLucasSinuso/vitrine.git
cd vitrine

# Backend
cd vitrine_backend
uv sync                             # Instala dependências
cp .env.example .env                # Configure o .env
uv run python -m app.etl.run_etl    # Popula o cache SQLite
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (outro terminal)
cd vitrine_frontend
npm install                         # Instala dependências
npm run dev                         # Dev server em localhost:5173
```

### Docker

```bash
# Da raiz do projeto
docker compose up --build
```

A documentação interativa da API estará disponível em `http://localhost:8000/docs`.

---

## Testes

### Backend

```bash
cd vitrine_backend
uv run pytest
```

A suíte cobre: validação de códigos (EAN/PLU), métricas do model (markup, margem, edge cases), serialização do schema Pydantic, regras de negócio do service (mock de repositório, clamp de paginação, código inválido) e transformação ETL, além de segurança (hash de senhas) e autenticação JWT.

#### Testes de Integração API

```
tests/
├── api/
│   ├── conftest.py              # Fixtures (client, usuários, tokens)
│   ├── test_api.py              # 26 casos (autenticação, CRUD, sync)
│   ├── test_bi_endpoints.py     # 29 casos (relatórios BI)
│   └── test_inventario.py       # 13 casos (sessões, itens, consolidado)
├── etl/
│   └── test_transform.py
├── models/
│   └── test_produto_model.py
├── schemas/
│   └── test_produto_schema.py
├── services/
│   ├── test_produto_service.py
│   └── test_auth_service.py
└── utils/
    ├── test_codigo.py
    └── test_security.py
```

| Categoria | Casos |
|---|---|
| Autenticação (token) | Validação, credenciais inválidas, usuário inexistente, campos vazios |
| Registro de usuário | Admin cria usuário, sem autenticação, role inválida |
| Listagem de produtos | Autenticado, sem autenticação, paginação |
| Busca de produto | Por código válido, inexistente, código inválido |
| Detalhes completos | Supervisor/Admin acessa, Operador bloqueado, sem autenticação |
| Status do cache | Acesso público |
| Admin Sync | Trigger, permissões, histórico, status de job |
| CORS | Headers em requisições OPTIONS |
| BI Endpoints | KPIs, receita, ranking, curva ABC, SKU, trocas, perdas, consumo, temporal, exportação |
| Inventário | Sessões, itens, consolidado multi-usuário |

### Frontend

```bash
cd vitrine_frontend
npm run build      # TypeScript check + Vite build
```

---

## Business Intelligence

O módulo BI permite análise de vendas com relatórios analíticos e exportação:

### Relatórios Disponíveis

- **Dashboard** — KPIs financeiros + ranking de produtos do período
- **Receita por Dimensão** — Receita e quantidade vendida agrupadas por grupo, família ou produto, com filtros hierárquicos
- **Ranking** — Top N produtos por receita ou quantidade
- **Curva ABC** — Classificação automática A/B/C por dimensão
- **Análise de SKU** — Detalhamento por produto (receita diária, distribuição por hora, ranking de dias)
- **Trocas** — Total e taxa de troca, produtos mais trocados
- **Perdas e Consumo** — Produtos com maior perda e consumo
- **Distribuição Temporal** — Série por hora e por dia da semana

### Comparação YoY (Ano contra Ano)

O **diferencial mais poderoso** do Vitrine: o dashboard de BI permite comparar KPIs do período atual com o mesmo período do ano anterior, revelando sazonalidade, tendências de crescimento e oportunidades de ajuste.

**Como funciona:**
- Endpoint `GET /bi/kpis/comparativo` retorna os mesmos KPIs do período atual lado a lado com os do ano anterior
- Cada KPI inclui um campo `variacao` (percentual) — positivo (▲ verde) ou negativo (▼ vermelho)
- O frontend exibe badges intuitivos: ▲ 12.5% ou ▼ -3.2%

| KPI | Período Atual | Período Anterior | Variação |
|---|---|---|---|
| Receita Total | R$ 1.250.000 | R$ 1.100.000 | ▲ 13.6% |
| Ticket Médio | R$ 47,80 | R$ 45,20 | ▲ 5.8% |
| Itens por Venda | 8.2 | 8.5 | ▼ -3.5% |
| Margem Média | 34.2% | 33.8% | ▲ 1.2% |

**Arquitetura:**
- `app/application/bi/factory.py` → `criar_dominio_comparativo()` isola a lógica de espelhar períodos
- `app/application/bi/reporting/relatorio.py` → `comparar_kpis()` calcula as variações
- `app/schemas/bi_schema.py` → `KpisComparativoDTO`, `VariacaoKpi` (schemas tipados)
- `app/api/routes/bi.py` → `GET /bi/kpis/comparativo` (endpoint dedicado)
- Frontend: `Dashboard.tsx` com toggle "Comparar com ano anterior" e `KpiCard.tsx` com badge de variação

### Arquitetura

```
app/application/bi/
├── domain/          # Domínios de negócio (vendas, trocas, perdas, consumo)
├── queries/         # SQLs externos (BiQueryLoader)
└── reporting/       # Relatórios por dimensão
```

- SQLs organizados em `bi/queries/` com `BiQueryLoader` (herda de `BaseQueryLoader`)
- Relatórios implementados em `app/application/bi/reporting/` com interface padronizada
- Endpoints REST em `app/api/routes/bi.py`
- Schemas Pydantic em `app/schemas/bi_schema.py`
- Exportação Excel via `app/application/bi/reporting/exportador.py`
- Cache de resultados com `TTLCache` em `app/application/bi/loader.py` (invalidado via `limpar_cache_bi()`)

---

## ETL

O pipeline ETL sincroniza dados do PostgreSQL para o SQLite local. Por padrão é executado manualmente; a configuração `cache_refresh_interval` (em segundos) está disponível para agendamento externo.

```bash
cd vitrine_backend
uv run python -m app.etl.run_etl
```

**Fases:**

1. **Extract** — `ProdutoExtractor` executa as queries SQL externas no Postgres (via `QueryLoader`)
2. **Transform** — agrupa códigos de barras por produto, converte para DTOs
3. **Load** — trunca e reinsere produtos e códigos no SQLite, registra timestamp em `CacheStatus`

> Queries SQL foram extraídas para arquivos `.sql` seguindo padrão DRY com `BaseQueryLoader`.

---

## Scripts

### Backend

| Comando | Descrição |
|---|---|
| `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Servidor de desenvolvimento |
| `uv run python -m app.cli <username> <nome> <senha>` | Criar admin via CLI |
| `uv run python -m app.etl.run_etl` | Executar ETL manualmente |
| `uv run pytest` | Rodar testes |

### Frontend

| Comando | Descrição |
|---|---|
| `npm run dev` | Dev server (Vite, proxy `/api` → `localhost:8000`) |
| `npm run build` | TypeScript check + Vite build |
| `npm run preview` | Preview do build de produção |

---

## Decisões de design

**SQLite como cache** — desacopla a API da disponibilidade do banco de origem. Consultas locais são rápidas e não geram carga no Postgres operacional.

**Separação Model / Schema** — `Produto` (SQLAlchemy) representa a entidade persistida; `ProdutoResponse` (Pydantic) define o contrato da API. Métricas computadas (`markup`, `margem`) ficam como `@property` no model e são expostas pelo schema via `from_attributes`.

**Arquitetura em camadas** — o backend segue a estrutura domain/application/infrastructure, isolando regras de negócio de detalhes técnicos.

**Injeção de dependência** — a sessão do banco é gerenciada pelo `Depends` do FastAPI (`deps.py`), mantendo o repositório desacoplado do ciclo de vida da request.

**Transform puro** — a camada de transformação ETL recebe apenas DTOs (não dicts), garantindo tipagem consistente e testes mais confiáveis.

**Classe `Codigo`** — encapsula validação, normalização e detecção de tipo de código de barras como Value Object imutável, isolando essa lógica do service.

**Cache frontend com AbortController** — o hook `biCache.tsx` implementa stale-while-revalidate com cancelamento de requests duplicadas, evitando waterfall em navegação rápida entre abas de BI.

**Componentização do BI** — `KpiCard`, `PeriodoForm`, `BiSubNav` são componentes puros e reutilizáveis, permitindo composição flexível dos dashboards.

**Leitor de código de barras via câmera** — `@zxing/browser` + `@zxing/library` permitem leitura em tempo real sem dependência de hardware dedicado.

---

## Melhorias planejadas

- [x] Testes de integração da API com `TestClient` e banco SQLite em memória
- [x] Refatoração SQL (BaseQueryLoader + Herança)
- [x] RolesEnum para escalabilidade SaaS
- [x] Proxy Vite para tunnel único (Cloudflare)
- [x] Logging detalhado por fase ETL
- [x] Endpoint de busca por nome (`GET /produtos/busca?q=`)
- [x] Endpoints de BI (receita, ranking, curva-abc, sku, trocas, perdas, consumo, temporal, exportação Excel)
- [x] Comparação YoY (ano contra ano) no dashboard
- [ ] Relatórios agendados via WhatsApp
- [ ] Filtros por grupo e família em `GET /produtos/`
- [ ] Frontend mobile (PWA) com leitura de código de barras pela câmera
- [ ] Agendamento automático do ETL via scheduler interno
- [ ] Endpoint para cancelar job em andamento
- [ ] Notificação (WebSocket) ao completar sync
- [ ] Cache distributed (Redis) para múltiplas instâncias

---

## Lições Aprendidas

- SQL hardcoded é um pesadelo de manutenção → refatorei para arquivos externos com herança
- Strings hardcoded de roles limitam escalabilidade → criei RolesEnum
- Testes não são opcionais → cobrem 55+ casos de uso
- Documentação é parte do código → README vivo e atualizado
- Comparação YoY transforma dados operacionais em insight estratégico — um período isolado não conta a história completa

---

## Autor

Desenvolvido por **Pedro Lucas** como case técnico de backend Python / análise de dados.

- Contato: pedrolucas.sinuso@gmail.com
- LinkedIn: [linkedin.com/in/pedro-sinuso](https://www.linkedin.com/in/pedro-sinuso)
- GitHub: [github.com/PedroLucasSinuso](https://github.com/PedroLucasSinuso)

> Gostou do projeto? Deixe uma estrela e me conte o que melhoraria!
