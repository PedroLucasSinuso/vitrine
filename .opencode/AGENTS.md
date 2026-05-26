# AGENTS.md — Vitrine

> Compact onboarding for OpenCode sessions. If it's not here, it's either obvious or already in `/.opencode/docs/`.

---

## Repository Layout

```
/
├── vitrine_backend/       # Python 3.11+ / FastAPI / SQLAlchemy / SQLite
├── vitrine_frontend/      # React 19 / TypeScript 6 / Vite 8 / Tailwind 4
├── .opencode/             # Agent config, skills, docs (architecture, decisions, context)
├── iniciar.ps1            # Dev launcher (backend + cloudflare tunnel, Q to quit, R to restart)
├── README.md              # Full documentation — read this first for architecture & features
└── TUTORIAL_INVENTARIO.md # User tutorial for inventory module (operators + supervisors)
```

---

## Commands

### Backend (cd `vitrine_backend/`)

| Action | Command |
|---|---|
| Install deps | `uv sync` |
| Run dev server | `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Run all tests | `uv run pytest` |
| Run single test file | `uv run pytest tests/api/test_api.py -v` |
| Run single test | `uv run pytest tests/api/test_api.py::test_name -v` |
| Run tests with coverage | `uv run pytest --cov` |
| Create admin user | `uv run create-admin admin "Nome" minha_senha` (ou `uv run python -m app.cli`) |
| Sync products from ERP | `uv run python -m app.etl.run_etl` |
| OpenAPI docs | `http://localhost:8000/docs` |

**Test note:** Tests use SQLite `:memory:` with `StaticPool` (see `tests/api/conftest.py`). `RATE_LIMIT_ENABLED=0` is set before import in conftest. Fixtures create 3 user roles (`usuario_operador`, `usuario_supervisor`, `usuario_admin`) with token helpers. `httpx` is available for test client usage. Tests live under: `tests/api/`, `tests/services/`, `tests/models/`, `tests/schemas/`, `tests/etl/`, `tests/repositories/`, `tests/value_objects/`, `tests/utils/`.

### Frontend (cd `vitrine_frontend/`)

| Action | Command |
|---|---|
| Install deps | `npm install` |
| Dev server | `npm run dev` → `http://localhost:5173` |
| Build | `npm run build` (runs `tsc -b && vite build`) |
| Lint | `npm run lint` (ESLint) |

**Dev proxy:** Vite proxies `/api/*` → `http://localhost:8000` (strips `/api` prefix). Also proxies `/static/*`. Vite server runs with `host: true` and `allowedHosts: ['.trycloudflare.com']` for tunnel access.

### Quick start (dev)

```powershell
# Option A — manual (2 terminals)
# Terminal 1
cd vitrine_backend; cp .env.example .env  # edit credentials
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd vitrine_frontend; npm install; npm run dev

# Option B — single script (backend + cloudflare tunnel)
.\iniciar.ps1          # Q+Enter to quit, R+Enter to restart backend
```

---

## Architecture (Key Facts)

### Backend Layers (`app/`)

```
api/routes/ → api/deps.py (DI) → application/ → domain/ → infrastructure/
                                                → adapters/ → ERP (PostgreSQL)
↕                                                   ↕
core/ (config, logging, interfaces)              core/models/ (Pure Python DTOs)
```

**Critical:** Domain models (`domain/models/`) inherit from SQLAlchemy `declarative_base`. This means unit tests require a DB session. `core/models/` has Pure Python DTOs used by adapters — this creates duplication with `domain/models/`.

**Good separation:** Adapters implement ABCs from `core/interfaces/source.py` (`ProductSource`, `TransactionSource`). BI domain is Pure Python, decoupled from ORM. Error handling centralized in `core/error_handler.py`.

### Frontend (`vitrine_frontend/src/`)

```
api/ → types/ → pages/ → components/
hooks/ (useAuth, useToast)   stores/ (biCache, configStore)
utils/ (formatters, colors)
```

**State management:** Raw `localStorage` + `Map` in `useRef` for BI cache. No reactive library (no Redux/Zustand/Jotai). `configStore.ts` is a mutable singleton — component re-renders are not triggered on cache change.

### Key Dependencies

- **uv** (Python package manager, not pip/poetry)
- **SQLAlchemy 2.0** (mapped_column, explicit session)
- **Pydantic v2** (settings, schema validation)
- **PyJWT** + **bcrypt** (auth, no refresh tokens)
- **APScheduler** (in-process scheduler with PID lock file — `.scheduler.lock`)
- **slowapi** (rate limiting)
- **Pandas 3.x** + **openpyxl** (BI/Excel)
- **Twilio** (WhatsApp notifications) + **smtplib** (email)
- **Jinja2** (email templates)
- **Pillow** (logo image processing)
- **cryptography** / **Fernet** (optional encryption for ERP passwords in SQLite)
- **httpx** (test client)
- **Recharts** (frontend charts)
- **@zxing/browser** (camera barcode scanning)
- **Tailwind v4** + `@theme` custom design tokens

---

## Hotspots (Don't Break These)

### 🔴 P1 — Architectural Debt (single-worker assumption)

1. **Domain models inherit from SQLAlchemy `Base`** — any change to the ORM model changes the domain. Tests need DB sessions.
2. **Global in-process caches** — `_ADAPTER_CACHE` (deps.py), `_cache` (config_service.py), `TTLCache` (transaction_source.py) — all per-process, not shared across uvicorn workers.
3. ~~**APScheduler starts in every worker** — sync/notifications fire N times if running with `--workers N`.~~ ✅ **Mitigado Sprint 4** — Scheduler lock `.scheduler.lock` com PID check (ver `app.main.py` lifespan). Apenas 1 worker adquire o lock; os demais logam warning e não agendam.

### 🟡 P2 — Design Smells

4. ~~**JWT 7-day expiry, no refresh, no revocation.**~~ ✅ **Resolvido Sprint 2** — Revogação implementada (blacklist + token_version + role change invalidation). Refresh token permanece pendente (backlog).
5. **`application/` is a catch-all** — ~12 submodules + loose service files (config_service.py, sync_service.py, scheduler.py, scheduler_manager.py).
6. **Config has 4+ sources of truth** (`.env` → SQLite → backend cache → localStorage).
7. **ETL is full DELETE+INSERT** (no incremental sync, not atomic).
8. **BI cache is frontend-only** (no server-side invalidation after sync).

### 🟢 P3 — Minor Issues

9. ~~`RolesEnum.get_hierarchy()` defined but not used in backend authorization.~~ ✅ **Resolvido Sprint 4** — removed (dead code).
10. `config_service.py` ~430 lines (SRP violation).
11. `localStorage.removeItem('role')` still present in `src/api/client.ts` line 20 — dead code, `role` hasn't been stored separately since Sprint 4. 🟡 **Pendente limpeza** — inofensivo mas sujo.
12. **Scheduler/email tinha 2 bugs silenciosos** (session fora do `with` + assinatura `criar_dominio` errada) — ✅ **Corrigido Hotfix 2026-05-22**. Email chegava vazio (MIME order) — ✅ **Corrigido**.

### Operational Risks

- Fernet key missing → ERP passwords stored in plain text in SQLite.
- Fernet key lost → encrypted passwords unreadable.
- SQLite used as primary app DB — no concurrent write support, no PITR.
- No backup strategy for `price_checker.db`.

---

## Key Constraints from `.opencode/`

- **Default agent:** `architect` (backend + architecture focus).
- **Model:** `openrouter/deepseek/deepseek-v4-flash:free` (default), `openrouter/qwen/qwen3-coder:free` (small — usado pelo orchestrator para tasks frontend).
- **Perms:** edit/write allowed, bash requires confirmation.
- **Skills available (7):** adversarial-review, anti-overengineering, brainstorming, cross-layer-review, frontend-design, performance-review, security-review. Carregadas sob demanda via `/skill`.
- **Stitch tools disponíveis:** `stitch_create_design_system`, `stitch_generate_screen_from_text`, `stitch_edit_screens`, `stitch_list_projects`, etc — para geração/edição de telas e temas.
- **Docs in `.opencode/docs/`:** `architecture.md` (full audit), `decisions.md` (15 ADRs), `context.md` (current status + next steps), `api-contracts.md` (formal API contracts), `coding-standards.md` (keep it simple), `known-issues.md` (fix history + active bugs + all sprints corrections), `hotfix-resumo-dia-parcial.md` (partial day comparison fix).

---

## Design System (Temas/Skins)

> Implementação de arquitetura de temas, começando com o tema "Flagship" (inspirado na proposta Stitch).

### Comandos do Orchestrator

| Entrada | Ação |
|---|---|
| `"design system"` ou `"DS"` | Dispara todas as 6 fases em ondas |
| `"DS fase 0"` (ou 1-5) | Dispara apenas a fase específica |
| `"DS 4.1, 4.2"` | Dispara tasks específicos |

### Como funciona

- **`design-system-plan.json`** define 33 tasks em 6 fases com dependências explícitas.
- **`CHECKLIST_DESIGN_SYSTEM.md`** é o checklist rastreável via sidebar.
- **Orchestrator lê o JSON**, monta ondas, e delega pra `architect`/`general`/`review`.
- **Rollback:** `git checkout checkpoint-design-system-v0`

### Estrutura de diretórios (alvo)

```
vitrine_frontend/src/
├── themes/
│   ├── tokens.css              # ~80 CSS vars (framework)
│   ├── theme-flagship.css      # Tema escuro indigo (Stitch)
│   ├── theme-vitrine.css       # Tema claro verde (original)
│   ├── ThemeProvider.tsx        # Context + localStorage
│   └── useTheme.ts             # Hook (theme, setTheme, isDark)
├── components/
│   ├── ui/                     # Componentes atômicos (Card, KpiCard, Badge, Modal, etc)
│   └── layout/                 # Sidebar, MobileNav, AppHeader, AppLayout
└── pages/
    └── bi/DashboardConsolidado.tsx  # Novo dashboard consolidado
```

---

## Open Questions (Not in Repo)

- **Branch/PR convention:** not defined. Check remote before pushing.
- **Release workflow:** not defined.
- **Test coverage target:** not defined.
