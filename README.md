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

O Vitrine nasceu de um problema prático de supermercado: operadores precisam consultar preço, estoque, markup e margem de produtos sem depender de conexão direta com o banco do ERP. A consulta aceita código de barras (EAN) ou código interno (PLU).

Além da consulta, o sistema faz:

- **BI** — relatórios de vendas com comparação ano contra ano (YoY)
- **Inventário** — contagem colaborativa com sessões e consolidação
- **Etiquetas** — formatação para impressão profissional
- **Leitor de código de barras via câmera** — sem hardware dedicado
- **Configurações via UI** — 6 abas com encriptação das senhas e fallback para `.env`
- **Notificações agendadas** — relatórios por WhatsApp e email
- **Enriquecimento de endereço** — consulta automática a BrasilAPI + ViaCEP

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
| Scheduler | **APScheduler** (sync + notificações dinâmicas) |
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
| Planilhas | **openpyxl** (geração no backend) |
| Código de barras | **@zxing/browser** + **@zxing/library** |
| Cache | AbortController + TTL 30s + stale-while-revalidate |
| Componentes | Design system próprio (Button, Card, Input, Modal, Skeleton, CmdK…) |

---

## Funcionalidades

| Módulo | Funcionalidades |
|--------|----------------|
| **Consulta** | Busca por EAN, PLU, nome. Exibe preço, estoque, markup, margem |
| **Etiquetas** | Geração de etiquetas para impressão |
| **Inventário** | Sessões multi-usuário, código de convite, consolidado geral |
| **BI** | Dashboard com meta/projeção, receita, ranking, curva ABC, análise SKU, trocas, perdas, consumo, distribuição temporal, tendências (ticket médio + tickets) |
| **YoY** | Comparação ano contra ano com alinhamento de dia da semana (offset ±3d) e fallback 29/fev |
| **Exportação** | Excel (.xlsx) para relatórios de BI e inventário (com abas: Contagem, Delta, Observações) |
| **Câmera** | Leitura única de código de barras via câmera do dispositivo (cooldown 2s entre leituras) |
| **Configurações** | 6 abas (Geral, Endereço, ERP, WhatsApp, Email, Sistema) com encriptação Fernet + fallback `.env` |
| **Teste de conexão** | Testa ERP, WhatsApp, Email, Anthropic com feedback visual |
| **Endereço** | Enriquecimento automático via BrasilAPI + ViaCEP |
| **Notificações** | Relatórios agendados via WhatsApp (Twilio) e Email (SMTP) com templates Jinja2 |
| **Sync** | Sincronização de produtos via adapter com agendamento configurável (mín. 10 min) |
| **Auth** | JWT com 3 roles (operador, supervisor, admin) |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    ERP (PostgreSQL)                  │
│              ┌──────────────────────┐                │
│              │   Adapter Alterdata  │                │
│              │  (ProductSource +    │                │
│              │   TransactionSource) │                │
│              └──────────┬───────────┘                │
└─────────────────────────┼───────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
     SQLite (cache)  BI (domínios)  SyncService
     produtos,       vendas/trocas/  (products →
     config, users   perdas/consumo   SQLite)
            │             │
            └─────────────┘
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

O backend segue **arquitetura em camadas + adapter pattern** para desacoplamento do ERP:

```
app/
├── core/                # Config, logging, error handling, rate limiter
│   ├── interfaces/      # Portas (ProductSource, TransactionSource) — ABCs
│   └── models/          # DTOs genéricos (Product, TransactionItem, OperationType)
├── adapters/            # Implementações das interfaces por ERP
│   └── alterdata/       # Adapter Alterdata (config, db, product_source, transaction_source, queries/)
├── domain/              # Entidades ORM + Value Objects + Enums + Domain Services
│   ├── models/          # SQLAlchemy models (SQLite)
│   ├── value_objects/   # Codigo (EAN/PLU), Endereco (CEP, UF, 3 níveis de dados)
│   ├── services/        # enriquecer_endereco (BrasilAPI + ViaCEP)
│   └── enums.py         # RolesEnum
├── application/         # Casos de uso
│   ├── services/        # Regras de negócio (auth, produto, config)
│   ├── bi/              # Business Intelligence (factory, analytics, reporting)
│   ├── sync_service.py  # Sincronização de produtos (substitui ETL)
│   ├── scheduler.py     # Agendamento dinâmico (APScheduler)
│   └── notifications/   # Email (SMTP), WhatsApp (Twilio), templates (Jinja2)
├── infrastructure/      # Banco (SQLite), repositórios
├── api/                 # Rotas FastAPI + injeção de dependência
└── schemas/             # Pydantic DTOs (contratos da API)
```

### Frontend

Organização modular por funcionalidade com design system próprio:

```
src/
├── api/          # Axios instance + módulos de endpoint (admin, auth, bi, produtos, …)
├── components/   # Design system (ui/) + feature-specific (bi/, scanner, admin)
│   ├── ui/       # Button, Card, Input, Modal, Skeleton, CmdK, EmptyState…
│   └── layout/   # Sidebar, AppHeader, AppLayout, MobileNav
├── hooks/        # Custom hooks (useAuth, useToast, useCountUp, useLocalStorage)
├── themes/       # tokens.css, theme-flagship.css, theme-vitrine.css, ThemeProvider, useTheme
├── pages/        # Páginas (consulta, admin, BI, login, configurações, …)
│   └── bi/       # Dashboard (com meta/projeção/tendências), Ranking, Receita, CurvaAbc, Sku, Trocas, PerdasConsumo, Temporal, DashboardConsolidado
├── config/       # chartTheme.ts (tema dos gráficos Recharts)
├── stores/       # Cache frontend (biCache com stale-while-revalidate + configStore)
├── types/        # TypeScript interfaces (admin, auth, bi, inventario, produto)
└── utils/        # Formatadores, cores, CSV
```

### Fluxo de requisição

```
Usuário (câmera / input)
    └─► React (consulta)
            └─► Axios GET /api/produtos/{codigo}
                    └─► Vite proxy (dev) / FastAPI static (produção)
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
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Após iniciar, crie um admin:
# uv run python -m app.cli admin "Nome" minha_senha

# Frontend (outro terminal)
cd vitrine_frontend
npm install
npm run dev                 # → http://localhost:5173
```

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
| `POST` | `/auth/logout` | Revogar token |
| `POST` | `/auth/logout-all` | Invalidar todos os tokens |
| `GET` | `/produtos/{codigo}` | Consulta por EAN ou PLU |
| `GET` | `/produtos/{codigo}/completo` | Consulta completa (supervisor+) |
| `GET` | `/produtos/busca` | Busca por nome |
| `GET` | `/produtos/` | Listagem paginada |
| `GET` | `/bi/kpis` | KPIs financeiros |
| `GET` | `/bi/kpis/comparativo` | KPIs com YoY |
| `GET` | `/bi/receita` | Receita por dimensão |
| `GET` | `/bi/curva-abc` | Classificação ABC |
| `GET` | `/bi/sku` | Análise detalhada de SKU |
| `GET` | `/bi/diario/comparativo` | Comparação diária YoY |
| `GET` | `/bi/tabela-produtos` | Tabela de preços (paginada) |
| `GET` | `/bi/exportar/excel` | Exportar relatório em .xlsx |
| `POST` | `/admin/sync` | Disparar sync manual |
| `GET` | `/admin/sync/{job_id}` | Status de sync |
| `GET` | `/admin/configuracoes` | Listar configurações |
| `PATCH` | `/admin/configuracoes` | Atualizar configurações |
| `POST` | `/admin/configuracoes/testar-erp` | Testar conexão ERP |
| `GET` | `/admin/inventario/sessoes` | Listar sessões de inventário |
| `POST` | `/admin/inventario/sessoes` | Criar sessão |
| `GET` | `/admin/inventario/sessoes/{id}/exportar-excel` | Exportar inventário |
| `GET` | `/status/` | Status do cache |

> Documentação completa em `http://localhost:8000/docs` (Swagger UI).

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
uv run pytest          # 184+ testes
```

> Estado atual: **184 testes passando**, 0 erros TypeScript, 0 lint warnings.

| Categoria | Casos |
|-----------|-------|
| Autenticação | Token, credenciais, registro, permissões, logout, revogação |
| Produtos | Busca por código/nome, paginação, detalhes |
| Códigos | Validação EAN-13/8/12, PLU-6, checksum |
| BI | KPIs, receita, ranking, curva ABC, SKU, trocas, exportação, comparativo YoY |
| Inventário | Sessões, itens, consolidado multi-usuário |
| Sync | Sincronização de produtos |
| CORS | Headers em requisições OPTIONS |
| Config Service | CRUD, encriptação Fernet, fallback `.env`, chaves somente-env |
| Cache Status | Admin com/sem registro, supervisor 403, operador 403, sem auth 401 |
| Contatos Email | CRUD completo |
| Contatos WhatsApp | CRUD completo |
| Value Objects | Endereco (CEP, UF, formatação, 3 níveis de dados) |
| Bootstrap | Init DB idempotente, migrations |

---

## Business Intelligence

### Relatórios disponíveis

- **Dashboard** — KPIs financeiros + meta de faturamento (progresso + projeção) + tendências (ticket médio, tickets) + mini ranking
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

**Ajustes de qualidade:** A data comparativa é calculada com `_ajustar_mesmo_dia_semana()` que desloca ±3 dias para alinhar ao mesmo dia da semana do período atual — padrão de indústria para varejo. Datas 29/fevereiro têm fallback automático para 28/fevereiro em ano não bissexto. O filtro de hora futura é aplicado simetricamente nos dois períodos para comparação justa.

---

## Sincronização (SyncService)

O antigo pipeline ETL foi substituído pelo **SyncService**, que usa o `ProductSource` do adapter para buscar produtos diretamente do ERP e sincronizar com o SQLite local:

1. **Adapter** — `AlterdataProductSource.get_all_products()` retorna `list[Product]`
2. **SyncService** — deleta registros antigos e insere os novos no SQLite
3. **Cache** — invalida cache de transações para forçar refresh no próximo acesso

```bash
cd vitrine_backend
uv run python -m app.etl.run_etl
```

Pode ser executado manualmente, via scheduler interno (intervalo configurável pela UI, mínimo 10 min) ou via API (`POST /admin/sync`).

---

## Design decisions

| Decisão | Motivo |
|---------|--------|
| **Adapter Pattern para ERP** | `ProductSource` / `TransactionSource` isolam o core do Vitrine dos detalhes de cada ERP. Trocar de ERP = novo adapter, sem mexer no core |
| **SQLite como cache** | Desacopla API da disponibilidade do PostgreSQL. Consultas locais são rápidas e não geram carga no banco operacional |
| **Separação Model / Schema** | `Produto` (ORM) ≠ `ProdutoResponse` (Pydantic). Métricas computadas (`markup`, `margem`) calculadas no schema/response |
| **Camadas domain/application/infrastructure** | Isola regras de negócio de detalhes técnicos (SOLID) |
| **Injeção de dependência** | Sessão gerenciada por `Depends` do FastAPI, repositório desacoplado do ciclo de vida da request |
| **Value Objects (`Codigo`, `Endereco`)** | Encapsulam validação e invariantes do domínio (EAN/PLU, CEP/UF) sem poluir o service |
| **Domain Services (`enriquecer_endereco`)** | Orquestra chamadas externas (BrasilAPI → ViaCEP) mantendo o VO imutável |
| **Fernet para senhas em repouso** | ConfigService encripta valores sensíveis (senha ERP) com chave de `ERPS_ENCRYPTION_KEY` — única proteção em DB SQLite sem segredo. ⚠️ **NÃO altere a chave após o primeiro uso** — senhas criptografadas se tornarão permanentemente ilegíveis |
| **Sentinel `***configurado***`** | A UI exibe `••••••` em vez de retornar a senha descriptada; o valor enviado de volta é ignorado pelo backend se igual ao sentinel |
| **ConfigService com fallback `.env` e SQLite** | Chaves operacionais editáveis via UI. Lê de `.env` se não existe no SQLite. Ao salvar pela UI, escreve apenas no SQLite — `.env` permanece imutável. `jwt_secret` é exclusivamente `.env` (não pode ser lido/alterado via UI) |
| **Templates Jinja2 para relatórios** | `relatorio_email.j2` / `relatorio_semanal.j2` permitem customizar o HTML sem recompilar |
| **APScheduler para jobs dinâmicos** | Sync e notificações agendados com intervalo configurável pela UI (mín. 10 min), sem reiniciar o servidor |
| **Cache frontend com TTL 30s** | configStore com cache em memória + localStorage + debounce de requisições paralelas. BI cache FIFO com 50 entradas |
| **Componentização do BI** | `KpiCard`, `PeriodoForm`, `BiSubNav`, `BiSideRail` — componentes puros e reutilizáveis |
| **Design system próprio (`ui/`)** | `Button`, `Card`, `Input`, `Modal`, `Skeleton`, `CmdK` — consistência visual sem dependência pesada de UI library |

---

## ⚠️ Atenção: Chave Fernet (ERPS_ENCRYPTION_KEY)

A senha do ERP (`erp_password`) é criptografada em repouso usando a chave definida em `ERPS_ENCRYPTION_KEY` no `.env`.

**Esta chave NÃO pode ser alterada após o primeiro uso.** Se a chave for modificada:

- Todas as senhas de ERP já armazenadas no banco de dados se tornarão permanentemente ilegíveis.
- Não há mecanismo de recuperação — a chave antiga é necessária para descriptografar.
- A conexão com o ERP será perdida até que uma nova senha seja fornecida pela interface de Configurações.

### Boas práticas

1. **Gere a chave uma única vez** na instalação inicial e mantenha-a fixa.
2. **Faça backup** do arquivo `.env` (ou ao menos da linha `ERPS_ENCRYPTION_KEY`) junto com o banco de dados.
3. **NÃO rotacione a chave** — diferente de boas práticas de segurança tradicionais, a implementação atual não suporta re-criptografia dos valores existentes com uma nova chave. (Esta limitação é conhecida e está documentada como C2 em `known-issues.md`.)

---

## Backup do Banco de Dados

O SQLite `price_checker.db` contém todas as configurações, cache, histórico de inventário e sincronia. A pasta `data/` fica em `vitrine_backend/data/`.

### Backup manual

```powershell
cd vitrine_backend
uv run python -m app.tasks.backup_db
```

Cria um arquivo `data/backups/price_checker_YYYYMMDD_HHMMSS.db` e mantém os 7 mais recentes (podagem automática).

### Agendamento automático (Windows Task Scheduler)

1. Abra **Task Scheduler**
2. "Create Basic Task..."
3. Nome: "Vitrine Backup DB"
4. Trigger: **Daily** às **03:00**
5. Action: **Start a program**
   - Program/script: `C:\Users\luizp\AppData\Local\uv\uv.exe` (ajuste o path)
   - Arguments: `run python -m app.tasks.backup_db`
   - Start in: `C:\caminho\para\vitrine\vitrine_backend`

### Opções

| Flag | Padrão | Descrição |
|---|---|---|
| `--keep N` | `7` | Máximo de backups a manter |
| `--backup-dir DIR` | `data/backups/` | Diretório de destino |

Também é possível usar `--backup-dir D:\backups` para salvar em outro disco.

---

## Licença

Distribuído sob licença **MIT**. Veja [`LICENSE`](LICENSE) para mais informações.

---

<div align="center">
  <br />
  <p>
    <a href="mailto:pedrolucassinuso@gmail.com">pedrolucassinuso@gmail.com</a>
    &nbsp;·&nbsp;
    <a href="https://linkedin.com/in/pedro-sinuso">LinkedIn</a>
    &nbsp;·&nbsp;
    <a href="https://github.com/PedroLucasSinuso">GitHub</a>
  </p>
  <br />
</div>
