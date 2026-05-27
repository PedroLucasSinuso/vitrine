# Current Context

> Audit stage: **Completa. 31 issues da Revisão Adversarial corrigidas. 227 testes passando.**
> Data da auditoria: **2026-05-27**
> Status: **Sprints 1-8 + 6 refinamentos concluídos. 31/31 issues do correction-plan corrigidos.**

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

### Lote 5 — Tabela de Preços (2026-05-25)

82. **Feature: Tabela de Preços** — Nova página standalone `/produtos` com listagem completa de produtos, markup e margem.
83. **Modelo `HistoricoPreco`** — Snapshot de preços por sync para preservar histórico de precificação.
84. **ETL Sync atualizado** — Grava `HistoricoPreco` para cada produto durante a sincronização.
85. **Rota `GET /bi/tabela-produtos`** — Lista paginada/filtrável com markup e margem calculados (percentuais × 100).
86. **Filtro por `ativo`** — Coluna `ativo` adicionada ao modelo `Produto`. Sync mapeia `Product.is_active`. Repository filtra apenas produtos ativos. Adapter lê `detalhe.stdetalheativo` do ERP (corrigido — antes hardcodava `True`). Sync seguinte popula valores reais.
87. **Hook `useTabelaProdutos`** — Busca com debounce, filtros, ordenação, paginação.
88. **Página standalone (não-BI)** — Rota `/produtos` com layout próprio (sem `BiPageLayout`/`BiSubNav`). Nav mobile: "Produtos" substitui "Inventário". Sidebar desktop ganha item "Produtos".
89. **Teste `test_tabela_produtos_shape`** — 169/169 testes passando.
90. **Relatório completo:** commit `10df8e9` (1ª versão BI) + `28462df` (refatoração standalone + filtro ativo).

### Auditoria Debug (2026-05-25) — 23 Novas Issues Identificadas

76. **Auditoria exaustiva por agente `debug-investigator`** — leitura de ~40 arquivos, busca de bugs não documentados.
77. **23 issues identificadas:** 5 🔴 críticos, 6 🟡 high, 7 🟡 medium, 5 🟢 low.
78. **2 regressões confirmadas:** M1+M2 (`job_id: string`) e Bônus (`logar_erro_interno`) constam como corrigidos mas **código atual ainda tem os bugs**.
79. **Documentos criados:** `docs/debug-audit-2026-05-25.md` (relatório completo) + `docs/action-plan-2026-05-25.md` (plano de ação).
80. **Todas as 23 issues corrigidas** em 6 sprints (Sprints 6-11) no commit `cdb135c` — 16 arquivos alterados, 0 regressões.
81. **Testes:** 168/168 passando. **TypeScript:** 0 erros. **Lint:** 0 erros, 0 warnings.

### Hotfix: Resumo do Dia — Comparação Parcial (2026-05-26)

98. **Problema:** `ResumoDia` comparava último dia do período com ano anterior sem verificar se era parcial (hoje em andamento). Gerava variação artificial (parcial vs full-day).
99. **Correção (frontend-only 🅰️):** `ultimoEParcial` calculado antes das variáveis `ant*Daily`; quando verdadeiro, as comparações YoY são puladas e o fallback `variacaoPeriodo` (kpisComp com `_filtrar_hora`) assume.
100. **Arquivo:** `vitrine_frontend/src/pages/bi/Dashboard.tsx` — ±20 linhas alteradas.
101. **Checkpoint:** `db8dd7b` (commit anterior ao hotfix).
102. **Documentação:** `docs/hotfix-resumo-dia-parcial.md`.
103. **Endpoint `/api/bi/diario/comparativo`:** Implementado (YoY com hora truncada para dias parciais). 15 testes.
104. **Testes:** Nenhum teste alterado. 0 regressões.

### UX Refactor + UI Fixes (2026-05-25) — 6 Commits

91. **Padronização de layout "Busca"** — `items-center px-4 py-4 overflow-x-auto` aplicado a **Etiquetas**, **Inventário**, **Produtos**, **Configurações**, **Usuarios**, **Admin**. Todas as páginas standalone agora são centralizadas horizontalmente e rolam corretamente em telas estreitas.

92. **Prepend (novo item ao topo) + Highlight animado** — Etiquetas e Inventário:
    - Item recém-adicionado vai para o **topo** da lista (`[{...item}, ...prev].slice(0, 100)`).
    - Item re-escanado em Inventário: **move ao topo + incrementa quantidade** + destaca com `highlightedCode` state + `animate-highlight-pulse` (1.5s, fade via CSS keyframe).
    - `@keyframes highlight-pulse` adicionado em `index.css`.

93. **Configurações/Geral — revisão completa de layout:**
    - Espaçamento entre blocos: `gap-12`+`divide-y` substituído por **`mb-10`** (40px) + **`border-t border-border/20 pt-6`** nos wrappers Endereço e Metas — separação visual clara com linha horizontal.
    - Inputs constritos: containers `ml-9` ganharam `max-w-md` (Endereço) ou removeram `max-w-md` com constrição específica (Metas: `max-w-[160px]` via `className`).
    - `CompactInput` corrigido: `className` passado é **mesclado** com o base em vez de sobrescrever (`...inputProps` spread vinha depois do `className` explícito).
    - Branding content: `items-start` adicionado para upload de logo não ficar deslocado à direita.
    - Whitespace removido acima da tab bar: `py-4` → `pb-4 pt-0`.

94. **Configurações — gap values aumentados:**
    - Geral: `gap-6` → `gap-10`.
    - ERP, WhatsApp, E-mail: `gap-5` → `gap-8`.
    - Grid Complemento+Bairro: `1fr_1fr` → `1fr_auto` (consistência visual).

95. **Usuarios + Admin centralizados** — Adicionados `items-center overflow-x-auto`. Input de senha em Usuarios mudou de `sm:flex-1` (esticava) para `sm:w-auto sm:min-w-[200px]` (tamanho natural).

96. **Produtos — tabela mais larga** — `max-w-4xl` → `max-w-6xl` para mostrar todas as 9 colunas (Código, Produto, Grupo, Família, Custo, Venda, Markup, Margem, Estoque) no desktop sem scroll horizontal.

97. **Commits:**
    - `84b4a97` — UX refactor: prepend, highlight, layout padrão Busca
    - `3680d23` — UI fixes: centralização, inputs, espaçamento
    - `89b36a5` — Espaçamento visível + Meta input constrito
    - `ef41cb3` — Meta input: 160px
    - `4c3894b` — Separadores explícitos entre blocos no Geral
    - `89b36a5..4c3894b` — 5 ajustes iterativos baseados em feedback

### Refinamentos Dashboard Performance + Backup (2026-05-27)

105. **F1: Dashboard loading feedback** — `loadingDiario`/`loadingHora` inicializados como `true` (skeleton visível desde o primeiro render). Single-day period early return seta ambos pra `false` (evita skeleton eterno).
106. **F2: Log de fallback de aggregates** — Warning logs em `/diario`, `/receita`, `/quantidade`, `/kpis` quando aggregate SQL retorna `None` (diagnóstico rápido se as queries do Alterdata estão funcionando).
107. **F3: Fast path SQL para `/temporal/hora`** — Antes chamava `criar_dominio()` carregando todos os itens do período. Agora usa `get_hora_aggregates()` com `GROUP BY EXTRACT(HOUR)` direto no PostgreSQL. Principal gargalo do Dashboard eliminado. Interface `TransactionSource` + implementação `AlterdataTransactionSource` + rota com fallback. (~30 min)
108. **React.memo no Dashboard** — 4 componentes (DashboardHero, DashboardSecondaryKpis, DashboardCharts, CurvaAbcPreview) envoltos em `memo()`. Props são estado (`useState`) com referências estáveis entre renders — reduz trabalho do reconciler. (~20 min)
109. **Backup automático SQLite** — Script `app/tasks/backup_db.py` que copia `price_checker.db` com timestamp, poda backups antigos (keep=7). Uso: `uv run python -m app.tasks.backup_db`. Recomendado agendar 03:00 no Windows Task Scheduler. (~30 min)
110. **Tipos SchedulerJobsResponse** — `SchedulerJob` interface exportada (`id`, `trigger`, `next_run`). `jobs: unknown[]` → `jobs: SchedulerJob[]`. (~5 min)
111. **F4: Fast path SQL para `/diario/comparativo`** — `obter_comparativo_diario()` agora tenta `get_comparativo_aggregate()` via SQL direto antes de cair no full load. Query busca apenas 2 dias (último + offset YoY) em vez de varrer o período inteiro. Suporte a 4 métricas (receita, quantidade, qtd_tickets, ticket_medio) + filtro de hora para dias parciais. Interface `TransactionSource` + implementação `AlterdataTransactionSource`. Fallback preservado. Dashboard agora faz **zero full loads** durante carregamento inicial. (~1h)
112. **Correção de dados: gráficos de tendência** — `get_diario_aggregates()` só tratava `receita` e `quantidade`. `ticket_medio` e `qtd_tickets` usavam `SUM(doc.qtitem)` — valor errado. Rota `/bi/diario` mapeava tudo exceto RECEITA para `"quantidade"`. Corrigido com mapeamento explícito das 4 métricas no adapter e na rota. (~15 min)
113. **Layout DashboardCharts sequencial** — Antes: grid 3-colunas (Tendências 2/3, Hora 1/3) com 388px de espaço morto. Agora: Tendências lado a lado, Hora full-width abaixo. Altura do hora chart: 420px → 280px. Mobile inalterado (tudo empilhado). (~20 min)
114. **CurvaAbcPreview: "Ver mais" → link** — Botão antes era toggle local (quebrado). Agora navega para `/bi/curva-abc`. (~5 min)

## Descobertas Principais

### O que está saudável ✅

- Separação API → Application → Domain → Infrastructure (direção de dependência correta).
- Adapters de ERP com interfaces (`ProductSource`, `TransactionSource`) — desacoplados do core.
- BI domain objects em Pure Python, independentes de ORM.
- Error handling sanitizado (`error_handler.py`) sem vazamento de detalhes internos.
- Rate limiting com toggle (`RATE_LIMIT_ENABLED`).
- Contratos API verificados e documentados em `api-contracts.md`.
- BI cache agora com TTL de 5 minutos + FIFO 50 entradas + invalidação pós-sync.
- Inventário com proteções anti-loop (debounce 2s global, stopper frame de câmera, pausa escaneio).
- Exportação Excel gerada no backend (elimina dependência `xlsx` no frontend).
- **227 testes passando** (pytest), 18 testes frontend.
- **54+ issues corrigidos** em múltiplos sprints.
- Cadeia JWT completa: emissão → revogação (blacklist + token_version) → refresh token com rotação → role change invalidation.
- AdapterRegistry funcional (`register_adapter()` + `_ADAPTER_REGISTRY`).
- ConfigService extraído: `config_cache.py`, `config_crypto.py`, `config_validator.py` (529→303 linhas).
- Domain pure `ProdutoPuro` + RepositoryDomain existentes (pendente migração das rotas HTTP).
- Sync extraído: `run_sync_common()` compartilhado entre scheduler e trigger manual.
- Console: 0 erros TS, 0 lint warnings.

### O que requer atenção 🔴🟡

| Prioridade | Hotspot | Arquivo | Status |
|---|---|---|---|---|
| 🔴 P1 | Domain models acoplados ao SQLAlchemy ORM | `domain/models/*.py` | **ProdutoPuro criado**, rotas HTTP pendentes de migração |
| 🔴 P1 | Caches globais em memória do processo | `deps.py`, `config_service.py`, `transaction_source.py` | Pendente (multi-worker) — mitigado por single-worker |
| 🔴 P3 | BI carrega tudo em RAM | `factory.py`, `fluxo.py` | Mitigado (180d limit + aggregates SQL) — root cause permanece |
| 🔴 N1 | ~~Console logs não aparecem no uvicorn~~ | ✅ Corrigido | ✅ |
| 🟡 P2 | Config management com 4+ fontes de verdade | `config_service.py`, `configStore.ts` | Parcial — configStore sync melhorou |
| 🟢 m3 | ~~React.memo no Dashboard~~ | ✅ Corrigido | ✅ |
| 🟢 N2 | ~~SchedulerJobsResponse unknown[]~~ | ✅ Corrigido | ✅ |

### Notas Pós-Revisão (Sprint 1 — Resíduos)

| ID | Nota | Gravidade |
|---|---|---|
| C1 | `listar_itens` (GET) não deveria ser bloqueado — apenas rotas de mutação (POST/PATCH/DELETE). Export Excel funciona em sessão encerrada, mas GET não. Inconsistência. | 🟡 Médio |
| C3 | Segundo async gap em `handleCodigo`: `await adicionarItemInventario()` nas linhas 283 e 303 não têm guard de stale closure. Apenas o `await buscarProduto()` (linha 290 → guard 292) está protegido. | 🟡 Médio |

### Cross-Layer Issues Corrigidos ✅

| Issue | Arquivos | Tipo | Lote |
|---|---|---|---|
| ~~M1+M2: `job_id` number → string~~ | **REGRESSÃO (B16) corrigida** em `cdb135c` | `admin.ts` | 🔴 Bug | 1 |
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
| ~~Bônus: `logar_erro_interno` sem import~~ | **REGRESSÃO (B24) corrigida** em `cdb135c` | `admin.py` | 🐛 Bug latente | 2 |
| observacao em ItemInventario | 4 files | 🟡 Feature | 3 |
| Cooldown + pausa escaneio | 2 files | 🟡 Bug | 3 |
| StoppedRef no LeitorCodigo | `LeitorCodigo.tsx` | 🟡 Bug | 3 |
| **C1: Validação de sessão ativa** | `inventario.py` (mas B5 reclassifica como 🔴 — GET bloqueado em sessão encerrada) | 🔴 Bug | Sprint 1 |
| **C3: Stale closure sessaoAtiva** | `Inventario.tsx` | 🔴 Bug | Sprint 1 |
| **C2: Documentação rotação Fernet** | `bootstrap.py`, `README.md` | 🟡 Documentação | Sprint 1 |

### Métricas do Projeto

- **Backend:** ~15 módulos de primeira linha, ~70 arquivos (estimado).
- **Frontend:** ~11 módulos de primeira linha, ~40+ componentes/páginas.
- **Testes:** 227 testes passando (pytest) — 31 issues do correction-plan + 23 debug-audit + hotfixes.
- **Issues resolvidos:** 54+ em múltiplos sprints (27 adversarial + 23 debug-audit + 4 hotfix/correção).
- **Lint:** 0 erros, 0 warnings.
- **TypeScript:** 0 erros de compilação.
- **UX audit:** 6 páginas ajustadas (Etiquetas, Inventário, Produtos, Configurações, Usuarios, Admin).
- **Issues abertos (2026-05-21 — Revisão Adversarial):** 27 issues — **26 corrigidos** em 6 sprints (2026-05-26). Apenas P3 (BI RAM) permanece como resíduo real.
- **Issues abertos (2026-05-25 — Auditoria Debug):** Nenhum — todos os 23 corrigidos em 6 sprints.
- **Issues abertos (2026-05-27 — Sessão Atual):** P3 (BI RAM — mitigado), P2 (Config 4 fontes), ProdutoPuro não plugado. N1, m3, N2, backup SQLite — todos **corrigidos na sessão**.
- **Regressões corrigidas:** 2 fixes (M1+M2 `job_id: string` e Bônus `logar_erro_interno`) aplicados novamente em `cdb135c`.
- **Resíduos pós-revisão Sprint 1:** 1 médio (segundo async gap em handleCodigo, linhas 283 e 303) — não bloqueante.
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
| **Frontend UX** | ✅ **Refatorado (2026-05-25)** | Layout padronizado Busca em 6 páginas, prepend, highlight, inputs constritos, espaçamento entre blocos, tabela larga |
| **Testes** | 🟡 Parcial | 168 testes, algumas lacunas de cobertura |
| **Deploy** | 🟡 Não auditado | Pipeline CI/CD, estratégia de rollback, health checks |

---

## Próximos Passos

### ✅ All Sprints (1-11 + Hotfix + UX Refactor) — Concluídos

**Sprint 1 (Bugs Críticos):** C1, C2, C3 — require_sessao_ativa, Fernet doc, stale closure.  
**Sprint 2 (Segurança):** S1-S5 + G1-G6 — JWT revogação, rate limits, frontend logout, role invalidation.  
**Sprint 3 (Performance):** P1-P3 — Dashboard, lazy loading BI, limite 180 dias, ErrorBoundary.  
**Sprint 4 (Médios):** M1-M12 + #1 #2 #5 #7 — migrations, thread-safe, dead code, Excel, configStore, 9 novos testes.  
**Sprint 5 (BI Dashboard + Temas):** MetaCard, ProjecaoCard, trend charts, mini ranking, chartTheme, CSS variables, AppHeader refatorado, tema Flagship.  
**Hotfix Scheduler/Email:** 2 bugs (session out of `with` + criar_dominio signature) + 1 MIME fix (email vazio).  
**Sprint 6 (Hotfix — Auditoria Debug):** B1, B16, B24 — regressões + crash.  
**Sprint 7 (Dados):** B3, B4, B8 — stale closure, engine leak, atomicidade ETL.  
**Sprint 8 (Consistência):** B5, B6, B15 — GET bloqueado, EAN stock, pausaEscaneio.  
**Sprint 9 (Frontend):** B13, B18, B19, B9 — 401 reload, polling leak, erros engolidos, dead code.  
**Sprint 10 (Segurança):** B10, B12, B17 — ProtectedRoute, logout fail, type fix.  
**Sprint 11 (Housekeeping):** B2, B20, B21, B23, B25 — email, modelo Claude, log, gaps de teste.  
**UX Refactor (2026-05-25):** Layout Busca em 6 páginas, prepend+highlight, Config espaçamento+inputs, Usuarios/Admin centralizados, Produtos max-w-6xl.

### Resíduos

1. `_debug_items()` em `factory.py` — ainda chamado em 2 lugares mesmo com guard DEBUG (linhas 188, 190). O guard existe, mas se logger estiver em DEBUG, faz 3 scans desnecessários. ✅ Mitigado por `logger.isEnabledFor(DEBUG)`.
2. Segundo async gap em `handleCodigo` (`await adicionarItemInventario()` linhas 283 e 303) — ainda presente, não bloqueante.

### Backlog (Médio/Longo Prazo)

21. ✅ JWT 8h + refresh token — **concluído** (Sprint 2 + Sprint 8: ACCESS_TOKEN_EXPIRE_MINUTES=30).
22. ✅ `_ADAPTER_CACHE` thread-safe — **concluído** (Sprint 4 M2).
23. Stream real no Excel export (openpyxl gera em RAM, pico ~250 MB para 50k produtos).
24. Desacoplar domain models do ORM — **ProdutoPuro já existe** (`domain/pure/`), mas rotas HTTP ainda usam service antigo. Pendente: migrar rotas.
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
