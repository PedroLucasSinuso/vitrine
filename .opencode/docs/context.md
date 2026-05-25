# Current Context

> Audit stage: **Completa. 5 sprints finalizados + hotfix scheduler. 168 testes passando.**
> Data da auditoria: **2026-05-22**
> Status: **Sprints 1-4 concluídos. Sprint 5 (BI Dashboard + Temas) concluído. Hotfix scheduler/email aplicado.**

---

## O que Foi Feito

### Lote 1 — Análise Inicial (2026-05-20)

1. **Análise estrutural completa** do frontend (React/TypeScript/Vite) e backend (Python/FastAPI/SQLAlchemy).
2. **Mapeamento de módulos e boundaries** — camadas, dependências, acoplamentos.
3. **Registro de 12 hotspots arquiteturais** (P1 a P3) em `architecture.md`.
4. **Documentação de 11 decisões arquiteturais (ADRs)** em `decisions.md`, com tradeoffs explícitos.
5. **Cross-layer audit (2026-05-20):** Verificação contrato a contrato entre 10 routes, 11 schemas, 8 API clients e 6 type files. Contrato formal em `api-contracts.md`.
6. **Correção de 11 mismatches no frontend** (14 files alterados, 0 backend).

### Lote 2 — Refatoração do Inventário (2026-05-21)

7. **Adapter Pattern no ETL** — ETL acoplado deu lugar ao `ProductSource`/`TransactionSource` com adapter Alterdata (`adapters/alterdata/`). Core models (`Product`, `Transaction`) como dataclasses Pure Python. Redução de -1472/+766 linhas.

8. **Módulo de Inventário — melhorias**:
   - **OperadorHome** — página própria com 2 cards (Busca + Inventário), sem acesso a admin.
   - **URL `/inventario`** — operador acessa fora do `/admin`. Admin/supervisor mantêm `/admin/inventario`.
   - **Exportação Excel + Delta** — backend gera `.xlsx` com 3 abas: Contagem, Delta (vs. Sistema), Observações.
   - **Terceira aba "Observações"** — itens com observação registrados manualmente.
   - **Botão flash na câmera** — toggle torch via `MediaStreamTrack.applyConstraints()`.
   - **Escaneio único** — removido `continuo` (câmera lê 1 código e fecha). Operador ajusta quantidade com +/−.
   - **Cooldown de 2s global** entre leituras para evitar bombardeio de API.
   - **Campos `observacao`** — modelo + schema + rota + frontend.

9. **Migration automática** — `bootstrap._run_migrations()` com `ALTER TABLE` para colunas novas (SQLite).

### Lote 3 — Documentação (2026-05-21)

10. **`context.md`, `decisions.md`, `known-issues.md`, `api-contracts.md`** atualizados para refletir Lote 2.
11. **ADR-012 a ADR-015** adicionados.
12. **`AGENTS.md`** atualizado (comando sync, contagem ADRs, layout).

### Lote 4 — Revisão Adversarial Completa (2026-05-21)

13. **Revisão adversarial multi-angulo** usando skills: `adversarial-review`, `security-review`, `performance-review`, `cross-layer-review`, `anti-overengineering`.
14. **Análise de 4 áreas críticas:**
    - **Auth/Security:** JWT, CSRF, rate limiting, role hierarchy, Fernet crypto, token storage
    - **Câmera/Inventário:** stream cleanup, debounce, flash, sessão encerrada, observacao, Excel export
    - **Config/Cache/Sync:** race conditions, TTLs, thread-safety, engine lifecycle, scheduler DST
    - **BI/Frontend:** re-renders, bundle size, memory usage, stale closures, N+1 groupbys
15. **27 issues documentadas** em `known-issues.md`.
16. **10 lacunas de teste identificadas** (T1-T10).
17. **Agente `orchestrator` criado** em `.opencode/agents/orchestrator.md`.

### Sprint 1 — Correção de Bugs Críticos (2026-05-21)

18. **C1: Sessão encerrada agora bloqueia operações** — `require_sessao_ativa()` adicionado em `listar_itens`, `adicionar_item`, `atualizar_item`, `limpar_itens` no backend. Itens não podem mais ser adicionados/editados/removidos em sessões encerradas. (~30 min)
19. **C3: Stale closure de `sessaoAtiva` protegido** — `useRef(sessaoAtivaRef)` adicionado para rastrear o ID da sessão atual. Guard `if (!sessaoAtivaRef.current || sessaoAtivaRef.current !== sessaoAtiva?.id) return` após `await buscarProduto()` no `handleCodigo`. (~20 min)
20. **C2: Risco de rotação de chave Fernet documentado** — Warning em `bootstrap.py` no startup, seção dedicada no `README.md` com boas práticas. O código não foi alterado (requer redesign). (~15 min)
21. **Revisão adversarial do Sprint 1 concluída** — 2 resíduos identificados (ver "Notas Pós-Revisão" abaixo).

### Sprint 2 — Segurança (2026-05-21)

22. **S1: Revogação de token JWT implementada** — Tabela `token_blacklist` com `jti` (UUID4) + coluna `token_version` em `usuarios`. Endpoints `POST /auth/logout` (revoga jti) e `POST /auth/logout-all` (incrementa token_version). `get_current_user()` verifica ambos. (~2h)
23. **S2: Prefixo `/admin/` documentado como intencional** — Comentário inline no router `inventario.py` referenciando ADR-012. (~5 min)
24. **S3: JWT_SECRET agora é somente `.env`** — `_CHAVES_SOMENTE_ENV = {"jwt_secret"}` em `config_service.py`. `get()` ignora DB para essas chaves. `set_many()` bloqueia escrita. (~15 min)
25. **S4: `/status/` com rate limit (10/min)** — `@limiter.limit("10/minute")` adicionado em `cache_status.py`. (~5 min)
26. **S5: `/auth/register` com rate limit (5/min)** — `@limiter.limit("5/minute")` adicionado em `auth.py`. (~5 min)

### Correções Pós-Revisão Sprint 2 (2026-05-21)

27. **G1: Frontend chama `/auth/logout`** — `useAuth().logout()` e `auth.logout()` agora fazem fire-and-forget POST para revogar token no servidor. (~10 min)
28. **G2: Mudança de role invalida tokens** — `auth_service.atualizar()` incrementa `token_version` se role mudar. (~5 min)
29. **G3: Migration limpa `jwt_secret` do DB** — `DELETE FROM configuracoes WHERE chave = 'jwt_secret'` em `bootstrap.py`. (~2 min)
30. **G4: `set_many()` retorna chaves ignoradas** — `ConfiguracaoResponse.ignoradas` agora informa quais chaves não foram salvas. (~10 min)
31. **G5: Blacklist filtra tokens expirados** — Query adiciona `expires_at > now()`. (~2 min)
32. **G6: Tokens < 5 min pulam blacklist** — `iat` no payload; skip query para tokens recentes. (~8 min)
33. **T11-T15: 4 novos testes de integração** — Cobertura de logout, logout-all, role change, status endpoint. (~20 min)
34. **159 testes passando** (155 + 4 novos, 0 regressões).

### Sprint 3 — Performance (2026-05-21)

35. **P1: Dashboard sem duplicação** — 2 useEffects fundidos em 1 com `useRef(isFirstRender)`. De 4 chamadas de API no mount para 1. (~30 min)
36. **P2: Lazy loading BI** — 8 páginas BI convertidas para `React.lazy(() => import(...))` + `<Suspense>` com fallback. Chunks carregados sob demanda. (~20 min)
37. **P3: BI com limite de 180 dias** — 3 camadas de proteção: validação visual no form, clamp no API client, HTTP 400 no backend. (~10 min)
38. **P2a: ErrorBoundary criado** — `ErrorBoundary.tsx` com fallback + botão "Tentar novamente". Envolve `<Suspense>` em `App.tsx`. (~15 min)
39. **P3c: Validação data_fim < data_inicio** — Mensagem de erro específica + botão desabilitado. (~5 min)

### Sprint 4 — Médios e Manutenção (2026-05-21)

40. **M1: Migration no lifespan** — `init_db()` movido para o startup, guard `_migration_feita` com `threading.Lock`. Removidas 12 chamadas em rotas. (~20 min)
41. **M2: _ADAPTER_CACHE thread-safe** — `threading.Lock` + `with _ADAPTER_LOCK` em `get_product_source` e `get_transaction_source`. (~10 min)
42. **M3: sync_com_erro() chamado** — Bloco try/except em `sync()` com rollback antes de gravar erro. (~10 min)
43. **M4: Observacao com limite 500 chars** — `max_length=500` no schema + truncamento na concatenação. (~5 min)
44. **M5: useCountUp sem reset visual** — `lastValueRef` mantém valor durante mudança de target. (~10 min)
45. **M6: BI cache FIFO 50 entradas** — `insertionOrderRef` com `MAX_ENTRIES = 50`. Removeção FIFO. (~10 min)
46. **M7: Content-Length no Excel** — Adicionado em ambos endpoints de exportação. (~5 min)
47. **M8: localStorage role removido** — `getRole()` decodifica JWT. Escritas residuais removidas. (~5 min)
48. **M9: get_hierarchy() removido** — Dead code confirmado. (~2 min)
49. **M10: isTokenAboutToExpire removido** — Dead code confirmado. (~2 min)
50. **M11: configStore com TTL 30s** — Cache expira após 30s. `refreshConfig()` exportado. Debounce com `pendingPromise`. (~15 min)
51. **M12: Busca com mountedRef** — Guard contra `setState` em componente desmontado (busca por nome + EAN). (~10 min)
52. **#1: sync_com_erro com rollback** — `self.db.rollback()` antes de commit do erro. Impede perda de dados. (~5 min)
53. **#2: Content-Disposition unificado** — Aspas adicionadas no filename do bi.py. (~2 min)
54. **#5: getConfigsCache sem duplicação** — `pendingPromise` compartilhada evita requests paralelas. (~5 min)
55. **#7: handleBuscar com mountedRef** — Guard na busca por código EAN. (~5 min)
56. **9 novos testes (T1-T9)** — Cobertura de IntegrityError retry, set_many rejeita jwt_secret, sync_com_erro, Excel export, BI Excel, logout role change, CHAVES_SOMENTE_ENV, init_db idempotente. (~30 min)
57. **M1(auth): getRole() decodifica JWT** — Supervisor/admin voltam a ver preco_custo na busca. (~5 min)
58. **Feature: Link Análise de Vendas na Busca** — Botão "Análise de Vendas" para supervisor/admin, navega para `/bi/sku?codigo={codigo}`. (~10 min)
59. **168 testes passando** (159 + 9 novos, 0 regressões).

### Sprint 5 — BI Dashboard + Meta/Projeção + Temas (2026-05-22)

60. **MetaCard + ProjecaoCard no Dashboard** — Dois novos cards condicionais: MetaCard (barra de progresso + "% da meta atingido") e ProjecaoCard (projeção `(receita/dias corridos) * total dias` + pill vs meta). Só renderizam quando `meta_faturamento_mensal > 0` configurado. (~30 min)
61. **Gráficos de tendência** — Ticket Médio + Tickets (qtd) em AreaCharts lado a lado sob "Tendências no Período". Só aparecem quando período > 1 dia. Dados via `fetchDiario(periodo, 'ticket_medio'/'qtd_tickets')`. (~20 min)
62. **Mini ranking compacto** — Versão simplificada do ranking (rank + nome + valor) no Dashboard, clicável para `/bi/sku?codigo=`. (~15 min)
63. **chartTheme.ts** — Novo arquivo `src/config/chartTheme.ts` com `CHART_THEME` (margin, xAxis, yAxis, tooltip, area, line) + helpers `formatChartCurrency`, `formatChartNumber`. Aplicado ao Dashboard. (~10 min)
64. **CSS variables em gráficos BI** — Todas as páginas BI (Receita, Temporal, Sku, CurvaAbc, etc) usam `var(--color-text-muted)` e `var(--color-border)` nos ticks de eixo, eliminando cores hardcoded. (~15 min)
65. **Backend: QTD_TICKETS + TICKET_MEDIO** — `Metrica` enum ganha `qtd_tickets` e `ticket_medio`. `relatorio_diario.serie_temporal()` trata ambos (nunique para tickets, sum/nunique para ticket médio). (~10 min)
66. **Backend: meta_faturamento_mensal** — `config_service.py` whitelist adiciona `meta_faturamento_mensal` (Aba Metas). (~2 min)
67. **AppHeader refatorado** — Layout 3-blocos com pipes `|`: `[logo mercado][nome] | [search] | [bell][theme][user papel][logout]`. Altura `h-14 → h-16`. Logo `h-6 → h-7`. Search `py-1.5 → py-2`. Sidebar simplificada (Dashboard+Consolidado → "BI"). Botão tema removido da sidebar. (~25 min)
68. **Configuracoes page** — Seção "Metas" com campo `meta_faturamento_mensal` no tab Geral. Seção de Endereço mantida (endereço completo). (~10 min)
69. **Bug fix: configStore ignora meta_faturamento_mensal** — `getConfigsCache()` descartava `meta_faturamento_mensal` no cache builder (só extraía `marketName`/`marketLogoUrl`). Dashboard nunca via o valor. Corrigido extraindo o campo no cache. (~5 min)
70. **Build/Tests** — 0 erros TS, 17/17 testes frontend, 168/168 backend.

### Hotfix — Scheduler/Email (2026-05-22)

71. **Bug 1: Session usada fora do `with SqliteSession()`** — `_enviar_relatorio_email()` e `_enviar_relatorio_whatsapp()` usavam `session` já fechada pelo context manager nas chamadas a `construir_relatorio_email/semanal`. Erro engolido pelo `except` genérico. Correção: movidas chamadas p/ dentro do `with`. (~10 min)
72. **Bug 2: `criar_dominio` chamado com assinatura antiga** — `report_builder.py` e `report_builder_email.py` passavam `(date, date, Session)` para `criar_dominio`, mas a assinatura atual é `(source: TransactionSource, date, date)`. Nunca funcionou desde a refatoração do adapter. Correção: report builders agora aceitam `TransactionSource`; adicionada `_obter_transaction_source()` no scheduler. (~15 min)
73. **Bug 3: E-mail chegava vazio (MIME order)** — `multipart/related` exige HTML como primeira parte (root, RFC 2387), mas as imagens eram anexadas antes. Correção: estrutura `related → alternative(text/html) → imagens`. (~10 min)
74. **Teste real** — Enviado para `gloriamarket21@gmail.com` + `pedrolucassinuso@gmail.com`. Ambos chegaram com conteúdo completo. ✅
75. **3 commits** — `6231b3e` (scheduler bugs) + `be6f80e` (MIME fix). 168/168 testes, 0 regressões.

### Auditoria Debug (2026-05-25) — 23 Novas Issues Identificadas

76. **Auditoria exaustiva por agente `debug-investigator`** — leitura de ~40 arquivos, busca de bugs não documentados.
77. **23 issues identificadas:** 5 🔴 críticos, 6 🟡 high, 7 🟡 medium, 5 🟢 low.
78. **2 regressões confirmadas:** M1+M2 (`job_id: string`) e Bônus (`logar_erro_interno`) constam como corrigidos mas **código atual ainda tem os bugs**.
79. **Documentos criados:** `docs/debug-audit-2026-05-25.md` (relatório completo) + `docs/action-plan-2026-05-25.md` (plano de ação).
80. **`known-issues.md` e `context.md` atualizados** — issues adicionados na seção de abertos.
81. **Próximos passos:** 6 sprints (Sprints 6-11) para resolver as 23 issues (~11h de trabalho).

## Descobertas Principais

### O que está saudável ✅

- Separação API → Application → Domain → Infrastructure (direção de dependência correta).
- Adapters de ERP com interfaces (`ProductSource`, `TransactionSource`) — desacoplados do core.
- BI domain objects em Pure Python, independentes de ORM.
- Error handling sanitizado (`error_handler.py`) sem vazamento de detalhes internos.
- Rate limiting com toggle (`RATE_LIMIT_ENABLED`).
- Contratos API verificados e documentados em `api-contracts.md`.
- BI cache agora com TTL de 5 minutos e invalidação pós-sync.
- Inventário com proteções anti-loop (debounce 2s global, stopper frame de câmera, pausa escaneio).
- Exportação Excel gerada no backend (elimina dependência `xlsx` no frontend).
- 168 testes passando.
- 27+ issues corrigidos em 4 sprints.
- Cadeia JWT completa: emissão → revogação → role change invalidation.
- Todos os 4 sprints concluídos e revisados com adversarial-review.

### O que requer atenção 🔴🟡

| Prioridade | Hotspot | Arquivo | Status |
|---|---|---|---|---|
| 🔴 P1 | Domain models acoplados ao SQLAlchemy ORM | `domain/models/*.py` | Pendente (longo prazo) |
| 🔴 P1 | Caches globais em memória do processo | `deps.py`, `config_service.py`, `transaction_source.py` | Pendente (multi-worker) |
| 🟡 P2 | Config management com 4+ fontes de verdade | `config_service.py`, `configStore.ts` | Parcial |
| 🟡 P2 | ETL full-reload sem transação atômica | `sync_service.py` | Mitigado (rollback + fetch-before-delete) |
| 🔴 **NOVO** | **Regressão: M1+M2 e Bônus não foram aplicados** | `admin.ts`, `admin.py` | **Sprint 6 (Hotfix)** |
| 🔴 **NOVO** | **Stale closure em ajustarQuantidade** | `Inventario.tsx:330-341` | **Sprint 7** |
| 🔴 **NOVO** | **Vazamento engine PostgreSQL no ETL** | `sync_service.py:103-124` | **Sprint 7** |
| 🔴 **NOVO** | **Sessão encerrada: GET bloqueado mas Excel não** | `inventario.py:341,488` | **Sprint 8** |
| 🟢 P3 | config_service.py ~430 linhas (SRP) | `config_service.py` | Pendente |

### Notas Pós-Revisão (Sprint 1 — Resíduos)

| ID | Nota | Gravidade |
|---|---|---|
| C1 | `listar_itens` (GET) não deveria ser bloqueado — apenas rotas de mutação (POST/PATCH/DELETE). Export Excel funciona em sessão encerrada, mas GET não. Inconsistência. | 🟡 Médio |
| C3 | Segundo async gap em `handleCodigo`: `await adicionarItemInventario()` nas linhas 283 e 303 não têm guard de stale closure. Apenas o `await buscarProduto()` (linha 290 → guard 292) está protegido. | 🟡 Médio |

### Cross-Layer Issues Corrigidos ✅

| Issue | Arquivos | Tipo | Lote |
|---|---|---|---|
| ~~M1+M2: `job_id` number → string~~ | **⚠️ REGRESSÃO (B16)** — código atual ainda tem `number` | `admin.ts` | 🔴 Bug | 1 |
| M3: `CacheStatus` sem tipo | `types/admin.ts`, `admin.ts` | 🟡 Tipagem | 1 |
| N1+A1: `getRole()` localStorage → JWT | `auth.ts`, `produtos.ts` | 🟡 UX/Security | 1 |
| A4: Botão encerrar sem restrição | `Inventario.tsx` | 🟡 UX | 1 |
| N2: `codigo` optional → required | `types/bi.ts` | 🟡 Contrato | 1 |
| N3+N10: BI Cache sem TTL | `biCache.tsx`, `Admin.tsx` | 🟡 Cache | 1 |
| N5: `relatorio` sem tipo | `types/bi.ts`, `bi.ts` | 🟡 Tipagem | 1 |
| N7+N8: Sem validação client-side | `utils/validation.ts`, `bi.ts`, `usuarios.ts` | 🟡 Validação | 1 |
| N4: configStore não reativo | `configStore.ts`, `AdminHeader.tsx` | 🟡 State | 1 |
| N9: `cacheInfo` tipo inseguro | `Configuracoes.tsx` | 🟢 Typing | 1 |
| A2: Sync sem lock | `admin.py` | 🟡 Concorrência | 2 |
| N6: Paginação sem metadata | `produto.py` (6 files) | 🟡 API | 2 |
| ~~Bônus: `logar_erro_interno` sem import~~ | **⚠️ REGRESSÃO (B24)** — código atual ainda chama sem import | `admin.py` | 🐛 Bug latente | 2 |
| observacao em ItemInventario | 4 files | 🟡 Feature | 3 |
| Cooldown + pausa escaneio | 2 files | 🟡 Bug | 3 |
| StoppedRef no LeitorCodigo | `LeitorCodigo.tsx` | 🟡 Bug | 3 |
| **C1: Validação de sessão ativa** | `inventario.py` (mas B5 reclassifica como 🔴 — GET bloqueado em sessão encerrada) | 🔴 Bug | Sprint 1 |
| **C3: Stale closure sessaoAtiva** | `Inventario.tsx` | 🔴 Bug | Sprint 1 |
| **C2: Documentação rotação Fernet** | `bootstrap.py`, `README.md` | 🟡 Documentação | Sprint 1 |

### Métricas do Projeto

- **Backend:** ~15 módulos de primeira linha, ~70 arquivos (estimado).
- **Frontend:** ~11 módulos de primeira linha, ~40+ componentes/páginas.
- **Testes:** 168 testes passando (pytest) — 5 sprints + hotfix validados.
- **Issues resolvidos:** 30+ em 5 sprints + hotfix.
- **Issues abertos (2026-05-21):** 0 críticos, 0 segurança, 0 performance.
- **Issues abertos (2026-05-25):** 5 🔴 críticos, 6 🟡 high, 7 🟡 medium, 5 🟢 low — 23 no total (ver `docs/debug-audit-2026-05-25.md`).
- **Regressões confirmadas:** 2 fixes documentados como corrigidos (M1+M2 `job_id: string` e Bônus `logar_erro_interno`) **não foram aplicados no código atual** — ver B16/B24.
- **Resíduos pós-revisão Sprint 1:** 2 médios (GET bloqueado indevidamente + segundo async gap) — não bloqueantes.
- **Tipo de app:** Sistema interno de vitrine/PDV para loja física com BI, inventário, sincronização ERP (Alterdata).

---

## Riscos Auditados

| Risco | Status | Detalhes |
|---|---|---|
| **Segurança** | ✅ Resolvido (Sprint 2) | S1-S5 corrigidos em `known-issues.md` |
| **Performance** | ✅ Resolvido (Sprint 3) | P1-P3 corrigidos: Dashboard, lazy loading BI, limite 180 dias |
| **Auth/Token** | ✅ Resolvido (Sprint 2) | JWT com revogação, blacklist + token_version, secret exclusivo .env |
| **Bugs Críticos** | ✅ **Resolvido** | C1, C2, C3 corrigidos no Sprint 1 (com 2 resíduos médios não bloqueantes) |
| **Manutenção** | ✅ Resolvido (Sprint 4) | M1-M12: migrations, thread-safe, dead code, Observacao, Excel, configStore |
| **Frontend UX** | 🟡 Não auditado | Loading/error/empty states, acessibilidade, responsividade |
| **Testes** | 🟡 Parcial | 168 testes, algumas lacunas de cobertura |
| **Deploy** | 🟡 Não auditado | Pipeline CI/CD, estratégia de rollback, health checks |

---

## Próximos Passos

### ✅ All Sprints (1-5 + Hotfix) — Concluídos

**Sprint 1 (Bugs Críticos):** C1, C2, C3 — require_sessao_ativa, Fernet doc, stale closure.  
**Sprint 2 (Segurança):** S1-S5 + G1-G6 — JWT revogação, rate limits, frontend logout, role invalidation.  
**Sprint 3 (Performance):** P1-P3 — Dashboard, lazy loading BI, limite 180 dias, ErrorBoundary.  
**Sprint 4 (Médios):** M1-M12 + #1 #2 #5 #7 — migrations, thread-safe, dead code, Excel, configStore, 9 novos testes.  
**Sprint 5 (BI Dashboard + Temas):** MetaCard, ProjecaoCard, trend charts, mini ranking, chartTheme, CSS variables, AppHeader refatorado, tema Flagship.  
**Hotfix Scheduler/Email:** 2 bugs (session out of `with` + criar_dominio signature) + 1 MIME fix (email vazio).

### Auditoria Debug 2026-05-25 — 23 Novas Issues

> **Relatório completo:** `docs/debug-audit-2026-05-25.md`
> **Plano de ação:** `docs/action-plan-2026-05-25.md`
> **6 sprints planejados** (~11h de trabalho)

**5 🔴 Críticos:** WhatsApp test crash (B1), stale closure em ajustarQuantidade (B3), vazamento engine PostgreSQL (B4), sessão encerrada inconsistente (B5), **2 regressões de fixes documentados** (B16/B24).
**6 🟡 High:** EAN não consultado no estoque (B6), atomicidade ETL (B8), polling leak (B18), erros engolidos (B19), ProtectedRoute frágil (B10), logout sem revogação real (B12).
**7 🟡 Medium:** 401 reload total (B13), pausaEscaneio não resetado (B15), job_id number/string mismatch (B17), gaps de teste (B25), email sem logo (B2).
**5 🟢 Low:** continuo prop morto (B9), modelo Claude 2024 (B20), log INFO em debug (B21), PK redundante (B23).

### Plano de Ação (Sprints 6-11)

| Sprint | Foco | Issues | Esforço |
|---|---|---|---|
| **Sprint 6 — Hotfix** | Regressões + Crash | B1, B16, B24 | ~30 min |
| **Sprint 7 — Dados** | Data Loss / Corrupção | B3, B4, B8 | ~3h |
| **Sprint 8 — Consistência** | Lógica de Negócio | B5, B6, B15 | ~3h |
| **Sprint 9 — Frontend** | UX / State / Leaks | B13, B18, B19, B9 | ~2h |
| **Sprint 10 — Segurança** | Defense-in-depth | B10, B12, B17 | ~1h |
| **Sprint 11 — Housekeeping** | Tech Debt + Testes | B2, B20, B21, B23, B25 | ~2h |

### Resíduos (Opcional) — Agora Incorporados nos Sprints

1. ~~Remover `require_sessao_ativa()` do GET → **B5 (Sprint 8)**~~
2. ~~Adicionar guard de stale closure → **B3 (Sprint 7, separado do C3)**~~
3. Limpar `localStorage.removeItem('role')` em `client.ts` (dead code desde Sprint 4) — ainda pendente

### Backlog (Médio/Longo Prazo)

21. Reduzir JWT expiry para 8h + refresh token.
22. Tornar `_ADAPTER_CACHE` thread-safe com `threading.Lock` (já corrigido M2, mas verificar abrangência).
23. Stream real no Excel export.
24. Desacoplar domain models do ORM.
25. Cache compartilhado (Redis) se houver multi-worker.

---

## Documentos Relacionados

| Documento | Conteúdo |
|---|---|---|
| `architecture.md` | Análise completa: layers, coupling, state, scalability, hotspots |
| `decisions.md` | ADRs com tradeoffs documentados (ADR-001 a 015) |
| `context.md` (este) | Status atual, riscos, próximos passos |
| `known-issues.md` | Histórico de correções + issues abertos |
| `debug-audit-2026-05-25.md` | **NOVO** — Relatório completo da auditoria debug (23 issues) |
| `action-plan-2026-05-25.md` | **NOVO** — Plano de ação para resolução em 6 sprints |
| `api-contracts.md` | Contratos formais da API |
| `TUTORIAL_INVENTARIO.md` | Guia de uso do módulo de inventário (usuários finais) |
