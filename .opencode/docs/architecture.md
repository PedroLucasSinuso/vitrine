# Architecture

> Audit realizada em 2026-05-20. Documento vivo — atualizar conforme mudanças arquiteturais.

---

## 1. Stack Overview

| Camada | Tecnologia | Localização |
|---|---|---|
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind 4 | `vitrine_frontend/` |
| Backend | Python 3.11+, FastAPI, SQLAlchemy | `vitrine_backend/` |
| Database (app) | SQLite (temporário) | Configurado via `sqlite_url` |
| Database (ERP) | PostgreSQL (cliente legado) | Configurado via `erp_host/port/database/user/password` |
| Auth | JWT (PyJWT) + bcrypt | `app/application/utils/` |
| Scheduler | APScheduler (in-process) | `app/application/scheduler.py` |
| Rate Limiting | slowapi | `app/limiter.py` |
| BI/Analytics | Pandas + openpyxl | `app/application/bi/` |
| Notifications | Twilio (WhatsApp) + SMTP (email) | `app/application/notifications/` |

---

## 2. Layer Architecture (Backend)

```
┌─────────────────────────────────────────────────────────────┐
│                      api/routes/                             │
│  (produto, auth, admin, bi, whatsapp, email, inventario…)    │
├─────────────────────────────────────────────────────────────┤
│                      api/deps.py                              │
│  (DI: get_db, get_current_user, require_role, adapters)      │
├─────────────────────────────────────────────────────────────┤
│                    application/                               │
│  services/ │ bi/ │ notifications/ │ sync_service.py          │
│  config_service.py │ scheduler* │ utils/                     │
├─────────────────────────────────────────────────────────────┤
│                      domain/                                  │
│  models/ (SQLAlchemy ORM) │ enums.py │ value_objects/        │
│  services/enriquecer_endereco.py                              │
├─────────────────────────────────────────────────────────────┤
│                   infrastructure/                             │
│  db/ (session, database, bootstrap)                           │
│  repositories/ (interfaces.py, produto, usuario)              │
│  postgres/                                                    │
├─────────────────────────────────────────────────────────────┤
│                     adapters/                                 │
│  alterdata/ (product_source, transaction_source, db, config)  │
├─────────────────────────────────────────────────────────────┤
│                      core/                                    │
│  config.py │ error_handler.py │ interfaces/source.py          │
│  models/ (Product, Transaction — Pure Python)                 │
│  logging_config.py │ timer.py                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Module Boundaries & Separation of Concerns

### 3.1 O que está correto

- **API layer (routes) → Application layer → Domain layer → Infrastructure**: fluxo de dependência descendente. Routes chamam services, services operam em domain models, repositories abstraem DB.
- **Interfaces para adapters de ERP**: `core/interfaces/source.py` define `ProductSource` e `TransactionSource` como ABCs. `adapters/alterdata/` as implementa. Trocar de ERP significa criar novo adapter.
- **Injeção de dependência via FastAPI `Depends`**: `deps.py` centraliza construção de dependências (session, repositories, adapters).
- **Error handling centralizado**: `error_handler.py` sanitiza exceções para mensagens públicas.

### 3.2 Violações de Separação

#### 🔴 Domain models acoplados ao SQLAlchemy ORM
Todos os models em `domain/models/` herdam de `Base` (SQLAlchemy `declarative_base`).

```python
from app.infrastructure.db.database import Base

class Produto(Base): ...   # ← domínio depende de infraestrutura
class Usuario(Base): ...
```

**Consequência:**
- Testes unitários de `ProdutoService` e `AuthService` exigem sessão SQLAlchemy.
- Trocar de ORM (ex: SQLAlchemy 2.x → async, ou trocar para SQLModel) exige reescrever o domínio.
- Regras de negócio (ex: `Produto.markup`, `Produto.margem`) estão no model ORM, não separadas.

**Tentativa de mitigação:** `core/models/product.py` e `core/models/transaction.py` são Pure Python dataclasses usados pelos adapters — mas isso cria duplicação conceitual entre `core/models/product.py` e `domain/models/produto.py`.

#### 🟡 `application/` como pasta guarda-chuva

`application/` contém 11 subdiretórios/arquivos de primeira linha com responsabilidades distintas:

| Submódulo | Responsabilidade |
|---|---|
| `services/` | Use cases (auth, produto) |
| `bi/` | BI analytics (domain + reporting + export) |
| `notifications/` | Email, WhatsApp, relatórios agendados |
| `sync_service.py` | ETL / sincronização com ERP |
| `config_service.py` | Config management (CRUD + cache + crypto) |
| `scheduler.py` / `scheduler_manager.py` | APScheduler lifecycle |
| `loaders/` | (não analisado em profundidade) |
| `utils/` | JWT handler, security (hashing) |

**Risco:** Sem uma separação mais granular (ex: um módulo `bounded_context/` por domínio), `application/` continuará crescendo e acumulando responsabilidades não relacionadas.

---

## 4. Coupling Analysis

### 4.1 Acoplamentos Fortes

| Origem | Depende de | Risco |
|---|---|---|
| `domain/models/*` | `infrastructure.db.database.Base` | ORM acoplado ao domínio |
| `config_service.py` | `core.config.settings` (global) | Imports diretos de singleton |
| `sync_service.run_sync_scheduled()` | `AlterdataProductSource` + `get_alterdata_engine` | Função de topo hardcoded ao adapter |
| `admin._run_sync_background()` | `AlterdataProductSource` + `get_alterdata_engine` | Mesma duplicação |
| `deps._ADAPTER_CACHE` | dicionário global no módulo | Não escala com múltiplos workers |
| `ProdutoRepository` retorna `Produto` (ORM) | `ProdutoService` depende de model ORM | Service não pode operar em modelo puro |

### 4.2 Acoplamentos Fracos (bons)

| Origem | Depende de | Benefício |
|---|---|---|
| `ProdutoService` | `IProdutoRepository` (ABC) | Troca de implementação possível |
| `AuthService` | `UsuarioRepository` | Troca de implementação possível |
| `SyncService` | `ProductSource` (ABC) | Troca de ERP possível |
| BI `Relatorio` | `Vendas` + `Trocas` (Pure Python) | Domínio de BI isolado do ORM |
| `criar_dominio()` | `TransactionSource` (ABC) | Troca de ERP possível |
| BI Reporting | `Relatorio`, `RelatorioDiario`, `RelatorioTemporal`, etc. | Cada relatório é isolado |

### 4.3 Inventário de Acoplamento — Alterdata ERP

**22 arquivos/ocorrências** dependem direta ou indiretamente do esquema Alterdata (PostgreSQL legado). Abaixo, a relação completa:

| Arquivo | O quê depende? | Específico Alterdata? |
|---|---|---|
| `adapters/alterdata/queries/produto.sql` | SQL de SELECT de produtos com 15 colunas (`detalhe.stcodigo`, `detalhe.stdescrproduto`, `detalhe.stdet`... `deptos.stdepto`, `familias.stfamilia`) | ✅ Sim — nomes de tabelas/colunas do schema Alterdata |
| `adapters/alterdata/queries/vendas.sql` | SQL de SELECT de vendas (12 colunas, `notafiscal.stnumeronf`, `itensnotafiscal.stcodigoproduto`, etc) | ✅ Sim |
| `adapters/alterdata/queries/trocas.sql` | SQL de SELECT de trocas (7 colunas, `trocaprodutostrocados.stcodigoprodutoretornado`) | ✅ Sim |
| `adapters/alterdata/queries/itens.sql` | SQL de SELECT de itens por nota (4 colunas) | ✅ Sim |
| `adapters/alterdata/product_source.py` | `PRODUTO_QUERY`, mapeamento de colunas para `Product` DTO (G1 a G4, 15 campos) | ✅ Sim — nomes de colunas do schema |
| `adapters/alterdata/transaction_source.py` | `VENDAS_QUERY`, `TROCAS_QUERY`, `ITENS_QUERY`; mapeamento para `TransactionItem` DTO | ✅ Sim |
| `adapters/alterdata/db.py` | `get_alterdata_engine()` — constrói `create_engine(postgres_url)` com config do SQLite | ✅ Sim — driver PostgreSQL, schema público |
| `adapters/alterdata/config.py` | `get_erp_config()`, `montar_url_postgres()` — lê `erp_host/port/database/user/password` do SQLite | ✅ Sim — estrutura de config específica |
| `app/etl/run_etl.py` | Script CLI que importa `AlterdataProductSource` e `get_alterdata_engine` | ✅ Sim |
| `app/api/deps.py` | `get_product_source()`, `get_transaction_source()` com `_ADAPTER_CACHE` para instâncias Alterdata | ✅ Sim |
| `app/application/sync_service.py` | `_run_sync_background()`, `run_sync_scheduled()` criam engine + source Alterdata | ✅ Sim |
| `app/api/routes/admin.py` | `_run_sync_background()` igual | ✅ Sim |
| `app/application/config_service.py` | `montar_url_postgres()` — formata URL PostgreSQL | ✅ Sim |
| `app/application/bi/reporting/relatorio.py` | `relatorio_sku()` consulta tabela `Produto` do SQLite (não ERP) via ORM | 🟡 Indireto |
| `app/domain/models/produto.py` | Campo `codigo_chamada` e `preco_custo` populados pelo adapter Alterdata | 🟡 Indireto |
| `core/models/product.py` | Dataclass `Product` com campos mapeados do Alterdata (G1-G4, `ativo`) | 🟡 Indireto — genérico p/ qualquer ERP mas campos nomeados como Alterdata |
| `core/models/transaction.py` | Dataclass `TransactionItem` com campos mapeados do Alterdata | 🟡 Indireto |
| `app/adapters/alterdata/__init__.py` | Vazio (marcador de pacote) | 🟢 Nulo |
| `app/adapters/__init__.py` | Vazio | 🟢 Nulo |
| `app/adapters/alterdata/tests/` | Testes específicos do adapter (se existirem) | 🟢 Nulo |
| `app/etl/__init__.py` | Vazio | 🟢 Nulo |
| `tests/etl/` | Testes de ETL que mockam adapter | 🟢 Nulo |

**Risco de troca de ERP:** ~15 arquivos precisariam ser alterados ou estendidos. O padrão ABC em `core/interfaces/source.py` mitiga parcialmente — um novo adapter implementaria as mesmas interfaces e seria plugado em `deps.py`.

**Específico Alterdata (não generalizável):**
- `stdetalheativo` — flag de ativo no ERP
- `stcodigo`, `stdescrproduto`, `stdet` — nomenclatura de colunas
- `notafiscal`, `itensnotafiscal`, `trocaprodutostrocados` — nomes de tabelas
- `G1/G2/G3/G4` — grupo de produtos (conceito específico do Alterdata)
- Agrupamento por departamento + familia + codigo_grupo (hierarquia Alterdata)

### 4.4 Inventário de Acoplamento — ORM (SQLAlchemy)

**Todos os 14 models em `domain/models/` herdam de `Base`** (`SQLAlchemy.declarative_base()`):

| Model | Arquivo | Herda de | Uso |
|---|---|---|---|
| `Produto` | `domain/models/produto.py` | `Base` | Principal entidade de produto |
| `ProdutoCodigo` | `domain/models/produto.py` | `Base` | Códigos adicionais (EAN, etc) |
| `Usuario` | `domain/models/usuario.py` | `Base` | Autenticação RBAC |
| `SessaoInventario` | `domain/models/inventario.py` | `Base` | Sessão de contagem |
| `ItemInventario` | `domain/models/inventario.py` | `Base` | Item de contagem |
| `Configuracao` | `domain/models/configuracao.py` | `Base` | Configurações chave-valor |
| `SyncJob` | `domain/models/sync_job.py` | `Base` | Job de sincronização |
| `CacheStatus` | `domain/models/cache_status.py` | `Base` | Status do cache BI |
| `TokenBlacklist` | `domain/models/token_blacklist.py` | `Base` | Revogação de tokens |
| `RelatorioAgendado` | `domain/models/relatorio_agendado.py` | `Base` | Relatórios programados |
| `LogEnvioRelatorio` | `domain/models/relatorio_agendado.py` | `Base` | Log de envio |
| `ErroImportacao` | `domain/models/erro_importacao.py` | `Base` | Erros de ETL |
| `ImportacaoArquivo` | `domain/models/erro_importacao.py` | `Base` | Arquivos de importação |
| `HistoricoPreco` | `domain/models/historico_preco.py` | `Base` | Snapshot de preços p/ sync |

**Consequências do acoplamento ORM:**
- Qualquer teste unitário que cria `Produto(codigo_chamada="X")` precisa de `session.add()` + `session.flush()` — não é unit test puro.
- `ProdutoService`, `AuthService`, `SyncService` — todos exigem sessão real.
- Trocar ORM (ex: SQLAlchemy → asyncpg, ou SQLite → PostgreSQL) exige migrar 14 models.

**Mitigação parcial:** `core/models/product.py` (`Product` dataclass) e `core/models/transaction.py` (`TransactionItem` dataclass) são Pure Python e usados pelos adapters. Mas:
- `SyncService.sync()` recebe `Product` do adapter e já mapeia para ORM `Produto` dentro do sync
- `ProdutoRepository` opera em `Produto` (ORM) e retorna `Produto` (ORM)
- `ProdutoService` recebe `Produto` (ORM) do repository

**C3 — `HistoricoPreco` como reserva para AI futura:**
- O model `HistoricoPreco` existe e é populado durante o sync (snapshot de `preco_venda`, `preco_custo`, `markup`, `margem` por `codigo_chamada`).
- Atualmente **não é lido por nenhuma rota ou serviço** — é puramente escrita.
- **Intenção:** Servir como dataset histórico para futura query de IA/análise de tendência de preços (ex: "qual produto teve maior markup nos últimos 6 meses?").
- **Risco:** Como a escrita ocorre **fora** da transação atômica do sync (C1, ver seção 8), pode haver inconsistência entre o snapshot de preços e os produtos sincronizados.

---

## 5. Auth Architecture

### 5.1 Fluxo

```
[Browser] → POST /auth/token (username+password) 
         → [Backend] AuthService.autenticar() 
         → bcrypt.verify() → PyJWT.encode() 
         → {access_token} (JWT com sub, role, nome_exibicao)
         → [Frontend] localStorage.setItem('token', token)
```

### 5.2 Configuração

| Parâmetro | Valor | Observação |
|---|---|---|
| Algoritmo | HS256 (PyJWT default) | |
| Expiração | 10080 min (7 dias) | **Longo demais** para segurança |
| Secret mínimo | 32 caracteres | Validado em `Settings.validar_jwt_secret()` |
| Rate limit login | 10/min | Slowapi |
| Refresh token | ❌ Não implementado | |
| Revogação | ❌ Não implementada | Sem blacklist, sem allowlist |
| Role hierarchy | `RolesEnum.get_hierarchy()` definido mas **não usado** no backend | Backend usa `require_role()` manual |

### 5.3 Hotspots

- **Token de 7 dias sem refresh**: se vazar, janela de exposição muito longa. Único mecanismo de logout é remover do localStorage.
- **Role armazenado em paralelo no localStorage**: `useAuth.getRole()` faz fallback para `localStorage.getItem('role')` se o JWT falhar — pode esconder tokens inválidos.
- **Logout via interceptor**: `client.ts` faz `window.location.href = '/login'` em 401 — full page reload, destrói estado React.

---

## 6. State Management

### 6.1 Backend

| Cache | Localização | TTL | Problema |
|---|---|---|---|
| Config (`config_service._cache`) | Módulo global (dict) | 30s | Não compartilhado entre workers |
| Adapter (`deps._ADAPTER_CACHE`) | Módulo global (dict) | Indeterminado | Não compartilhado entre workers |
| Transações (`transaction_source._cache`) | Módulo global (TTLCache) | 3600s (1h) | Não compartilhado entre workers; dados obsoletos se sync rodar |

### 6.2 Frontend

| Estado | Mecanismo | Reativo? |
|---|---|---|
| Token/Role | `localStorage` | ❌ |
| Config (marketName, logo) | `localStorage` + singleton `_cache` | ❌ |
| BI responses | `Map` em `useRef` via Context | ❌ (não trigger re-render) |
| Dark mode | `localStorage` + DOM direct | ❌ |
| Toast | Context + state | ✅ |

### 6.3 Hotspot: Múltiplas Fontes de Verdade para Config

```
.env (Settings)
  → SQLite (configuracoes table)
     → _cache dict (backend, TTL 30s)
        → API response
           → localStorage vitrine_config (frontend)
              → app_marketName / app_marketLogoUrl (localStorage itens individuais)
```

Cada camada adiciona latência e possibilidade de inconsistência.

---

## 7. Frontend / Backend Responsibilities

| Responsabilidade | Layer | Notas |
|---|---|---|
| UI Rendering | Frontend | React + Tailwind |
| Session State | Frontend | localStorage + hooks |
| Route Protection | Frontend (UX) + Backend (Security) | `ProtectedRoute` + `require_role()` |
| Business Rules | Backend | Services + Domain |
| Persistence | Backend | SQLAlchemy + SQLite/PostgreSQL |
| ERP Integration | Backend | Adapters |
| BI Data Aggregation | Backend | Pandas + Reporting |
| BI Visualization | Frontend | Recharts |
| Export Excel | Backend | openpyxl |
| Notifications | Backend | Twilio + SMTP |
| Scheduler | Backend | APScheduler |
| Config Management | Frontend (UI) + Backend (CRUD + env) | |

**Nota:** BI cache está no frontend (`biCache.tsx`), mas a fonte de dados (`TransactionSource`) está no backend. Se o backend rodar sync, o cache do frontend fica obsoleto até o usuário navegar para outra rota.

---

## 8. Scalability Risks

| Risco | Detalhe | Gravidade |
|---|---|---|
| **SQLite como DB principal** | Não suporta concorrência. `check_same_thread=False` é workaround. | 🔴 |
| **Cache global em processo** | `_ADAPTER_CACHE`, `_cache`, `TTLCache` — cada worker tem sua própria cópia | 🔴 |
| **APScheduler multi-worker** | Scheduler inicia em TODOS os workers — sync executa N vezes | 🔴 |
| **ETL full-reload** | DELETE + INSERT sem transação atômica — dados inconsistentes durante sync | 🟡 |
| **ThreadPoolExecutor single** | `max_workers=1` — sync enfileira sem feedback para o usuário | 🟡 |
| **BI sem cache server-side** | Cada requisição consulta o PostgreSQL do ERP diretamente. Múltiplos dashboards simultâneos sobrecarregam o ERP | 🟡 |
| **SyncService sem incremental** | `get_all_products()` sempre faz full load. Para 50k+ produtos, operação lenta | 🟡 |

---

## 9. Maintainability Concerns

- **`config_service.py`**: 432 linhas, 6 responsabilidades (CRUD, cache, criptografia, migração, parsing de URL, sentinel handling). Violação de SRP.
- **`application/bi/`**: 7 subdiretórios, 3 níveis de profundidade. Adicionar um relatório novo exige tocar em múltiplos arquivos.
- **Duplicação de lógica**: `run_sync_scheduled()` em `sync_service.py` vs `_run_sync_background()` em `admin.py` fazem a mesma operação com logging diferente.
- **Domain models acoplados ao ORM**: impede testes unitários puros.

---

## 10. Operational Risks

| Risco | Impacto |
|---|---|
| Fernet key não configurada → senhas em texto plano no SQLite | Exposição de credenciais do ERP |
| Perda da Fernet key → senhas criptografadas ilegíveis | Perda de acesso ao ERP |
| SQLite sem backup | Perda de dados de configuração, usuários, cache |
| JWT 7 dias sem revogação | Incapacidade de bloquear acesso de admin desligado |
| CORS configurado via regex e lista | Correto, mas requer atenção em deploy |

---

## 11. Hotspot Registry (Prioritário)

```
ID  | Prioridade | Hotspot
────┼────────────┼─────────────────────────────────────────────────────
H01 │ 🔴 P1     │ Domain models acoplados ao SQLAlchemy ORM
H02 │ 🔴 P1     │ Cache global em memória (não compartilhado entre workers)
H03 │ 🔴 P1     │ APScheduler executa em todos os workers simultaneamente
H04 │ 🟡 P2     │ JWT 7 dias sem refresh/revogação
H05 │ 🟡 P2     │ application/ como pasta guarda-chuva (baixa coesão)
H06 │ 🟡 P2     │ Config management com múltiplas fontes de verdade
H07 │ 🟡 P2     │ SyncService full-reload sem transação atômica
H08 │ 🟡 P2     │ Frontend cacheia BI sem invalidação server-side
H09 │ 🟢 P3     │ Role hierarchy definida mas não usada no backend
H10 │ 🟢 P3     │ Token/role duplicado em localStorage + JWT decode
H11 │ 🟢 P3     │ config_service.py com 432 linhas (SRP violation)
H12 │ 🟢 P3     │ ConfigService fallback silencioso para texto plano sem Fernet key
```

---

> ⚠️ **Nota sobre escala atual:** Este sistema foi projetado para operação em loja única com poucos usuários simultâneos (~1-5). Muitos dos hotspots acima (H01-H03) só se tornarão problemas reais com expansão para múltiplas lojas, múltiplos workers, ou aumento significativo de carga. A decisão de endereçá-los agora vs depois depende do roadmap de negócio.
