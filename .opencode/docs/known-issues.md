# Known Issues

Hoje monólito, mas no futuro o projeto será:
- SaaS python backend deployed on AWS;
- Specific adapter per ERP/Data Source installed on the client's PC, communicating with AWS by cloudflare tunnel;
- Frontend deployed on Vercel or AWS

---

## Cross-Layer Mismatches (API Contracts)

Verificados contra o código-fonte em 2026-05-20. Contrato completo em `docs/api-contracts.md`.

### ✅ Corrigidos (2026-05-20)

#### 🔴 M1+M2: `POST /admin/sync` e `GET /admin/sync/{job_id}` — `job_id` agora é `string`  
**⚠️ REGRESSÃO IDENTIFICADA EM 2026-05-25 — RE-CORRIGIDO (B16)**

**Correção original:** `vitrine_frontend/src/api/admin.ts` — `triggerSync()` retorna `{ job_id: string }`, `getSyncStatus()` recebe `jobId: string`.  
**Re-correção (2026-05-25):** O código ainda estava como `number`. Aplicado novamente no commit `cdb135c`.

#### 🔴 M3: `GET /admin/cache/status` — `CacheStatusResponse` interface adicionada

**Correção:** `vitrine_frontend/src/types/admin.ts` — nova interface `CacheStatusResponse` com `produtos_cached`, `last_refresh`, `ttl_seconds`. `getCacheStatus()` agora retorna `Promise<CacheStatusResponse>`.

#### 🟡 N1+A1: `buscarProduto()` agora decodifica JWT e tem fallback 403

**Correção:**
- `vitrine_frontend/src/api/auth.ts` — `getRole()` decodifica JWT via `jwtDecode` antes de cair no localStorage.
- `vitrine_frontend/src/api/produtos.ts` — `buscarProduto()` tenta `/completo` primeiro; se 403, faz fallback silencioso para `/`.

#### 🟡 A4: Botão "Encerrar" só aparece para o criador da sessão

**Correção:** `vitrine_frontend/src/pages/Inventario.tsx` — botão "Encerrar" agora checa `sessaoAtiva.criado_por === currentUsername`.

#### 🟡 N2: `ItemDimensaoDTO.codigo` agora é `string` (não optional)

**Correção:** `vitrine_frontend/src/types/bi.ts` — `codigo?: string` → `codigo: string`.

#### 🟡 N3+N10: BI Cache com TTL de 5 min + invalida após sync

**Correção:**
- `vitrine_frontend/src/stores/biCache.tsx` — cache expira após 5 minutos; exporta `clearBiCache()`.
- `vitrine_frontend/src/pages/Admin.tsx` — `clearBiCache()` é chamado quando sync termina.

#### 🟡 N5: `exportarExcelBI()` agora valida `relatorio` com tipo `RelatorioBi`

**Correção:** `vitrine_frontend/src/types/bi.ts` — novo tipo `RelatorioBi` (union de 10 literais). `exportarExcelBI()` valida antes de chamar API.

#### 🟡 N7+N8: Validações client-side adicionadas

**Correção:** `vitrine_frontend/src/utils/validation.ts` — funções `validarCodigo()`, `validarTop()`, `validarPeriodoBi()`, `validarSenha()`. Aplicadas em `bi.ts`, `usuarios.ts`.

#### 🟡 N4: `configStore` agora reativa com hook `useConfigCache()`

**Correção:** `vitrine_frontend/src/stores/configStore.ts` — novo hook `useConfigCache()` com subscription pattern. `AdminHeader` usa o hook em vez de `localStorage.getItem()`.

#### 🟢 N9: `cacheInfo` em Configuracoes tipado como `CacheStatusResponse`

**Correção:** `vitrine_frontend/src/pages/Configuracoes.tsx` — estado `cacheInfo` agora usa `CacheStatusResponse | null` em vez de tipo inline com campos opcionais.

---

### ✅ Corrigidos (2026-05-20, 2º lote — backend)

#### 🟡 A2: Sync com proteção contra execução duplicada

**Correção:** `vitrine_backend/app/api/routes/admin.py` — `trigger_sync()` agora verifica se existe `SyncJob` com `status == "em_progresso"` antes de criar novo job. Retorna 409 se já houver sincronização em andamento.

#### 🟡 N6: Paginação com metadata (`GET /produtos/busca` e `GET /produtos/`)

**Correção:**
- Backend: novos schemas `ProdutoListResponse { items, total }` + métodos `count_paginado()` e `count_por_nome()` no repositório/serviço.
- Frontend: `buscarProdutosPorNome()` retorna `ProdutoListResponse`, callers extraem `.items`.

#### 🐛 Bônus: `logar_erro_interno` sem import (bug latente)  
**⚠️ REGRESSÃO IDENTIFICADA EM 2026-05-25 — RE-CORRIGIDO (B24)**

**Correção original:** `vitrine_backend/app/api/routes/admin.py` — adicionado import de `logar_erro_interno`.  
**Re-correção (2026-05-25):** A importação ainda estava ausente no código. Aplicado novamente no commit `cdb135c`.

---

### ✅ Corrigidos (2026-05-21 — Lote 3: Inventário + Câmera + Operador)

#### 🟡 Feature: `observacao` adicionada ao ItemInventario

**Correção:**
- `vitrine_backend/app/domain/models/inventario.py` — coluna `observacao: Mapped[Optional[str]]`
- `vitrine_backend/app/schemas/inventario_schema.py` — campo `observacao: str = ""` em `ItemInventarioResponse`, `ItemInventarioSubmit`, `AtualizarItemInput`
- `vitrine_backend/app/infrastructure/db/bootstrap.py` — `_run_migrations()` executa `ALTER TABLE` idempotente
- `vitrine_backend/app/api/routes/inventario.py` — merge de observação ao incrementar item
- `vitrine_frontend/src/types/inventario.ts` — campo `observacao?: string`
- `vitrine_frontend/src/pages/Inventario.tsx` — modal de não-cadastrado com campo observacao, badge indicador na lista

#### 🟡 Bug: Escaneio contínuo causava duplicatas e chamadas fantasmas

**Correção:**
- `vitrine_frontend/src/components/LeitorCodigo.tsx` — removido `continuo` prop; adicionado `stoppedRef` para impedir callbacks de frame após parada; reset `stoppedRef.current = false` para React Strict Mode
- `vitrine_frontend/src/pages/Inventario.tsx` — cooldown global de 2s (`ultimaQualquerLeitura`), per-code 1.5s (`ultimaLeitura`), `pausaEscaneio` ref, auto `setCamera(false)` ao abrir modal 404, 500ms grace window ao fechar modal

#### 🟡 Feature: Botão flash/torch na câmera

**Correção:** `vitrine_frontend/src/components/LeitorCodigo.tsx` — `toggleFlash()` usa `MediaStreamTrack.applyConstraints({ advanced: [{ torch }] })`; botão UI com ícone `Sun` no topo direito.

#### 🟡 Feature: Operador com página própria

**Correção:**
- `vitrine_frontend/src/pages/OperadorHome.tsx` — NOVA página com 2 cards grandes (Busca + Inventário), role badge, dark mode
- `vitrine_frontend/src/App.tsx` — rota `/inventario` para operador; `/home/operador` redireciona para OperadorHome
- `vitrine_frontend/src/components/AdminHeader.tsx` — `linkPara()` retorna `/inventario` para operador, `/admin/inventario` para admin/supervisor

#### 🟡 Feature: Exportação Excel com 3 abas (backend)

**Correção:**
- `vitrine_backend/app/api/routes/inventario.py` — `exportar_excel_sessao()` e `exportar_excel_consolidado()` geram .xlsx com openpyxl (3 abas: Contagem, Delta, Observações)
- `vitrine_frontend/src/api/admin.ts` — `exportarInventarioSessaoExcel()` e `exportarInventarioConsolidadoExcel()` com `_filenameFromHeaders()`
- `vitrine_frontend/package.json` — removida dependência `xlsx`

#### 🟡 Melhoria: `ProdutoService.get_all_products()` + DI

**Correção:**
- `vitrine_backend/app/application/services/produto_service.py` — método `get_all_products()` adicionado
- `vitrine_backend/app/api/deps.py` — DI `get_produto_service()` registrado
- `vitrine_backend/app/sync_service.py` — `_get_estoque_db()` otimizado com `WHERE codigo_chamada IN (...)`

---

---

### ✅ Corrigidos (2026-05-21 — Sprint 1: Bugs Críticos)

#### 🔴 C1 — Itens em sessões encerradas

**Correção:** `vitrine_backend/app/api/routes/inventario.py` — novo helper `require_sessao_ativa()` adicionado nas rotas `listar_itens`, `adicionar_item`, `atualizar_item`, `limpar_itens`. Agora todas as operações em sessão encerrada retornam 400.

#### 🔴 C2 — Rotação de chave Fernet documentada

**Correção:** `vitrine_backend/app/infrastructure/db/bootstrap.py` — warning no startup. `README.md` — seção dedicada com boas práticas. O bug de design permanece (requer redesign), mas o risco está documentado.

#### 🔴 C3 — Stale closure de `sessaoAtiva` protegido

**Correção:** `vitrine_frontend/src/pages/Inventario.tsx` — `useRef(sessaoAtivaRef)` adicionado para rastrear o ID da sessão atual. Guard `if (!sessaoAtivaRef.current || sessaoAtivaRef.current !== sessaoAtiva?.id) return` após `await buscarProduto()` em `handleCodigo`.

---

### ✅ Corrigidos (2026-05-21 — Sprint 2: Segurança)

Correções de segurança implementadas via agente orquestrador. 5 issues fechados.

#### 🔴 S1 — JWT com revogação (blacklist + token_version)

**Correção:**
- `vitrine_backend/app/domain/models/token_blacklist.py` — NOVO modelo `TokenBlacklist` com `jti` (PK), `user_id`, `expires_at`, `revoked_at`
- `vitrine_backend/app/domain/models/usuario.py` — coluna `token_version` (Integer)
- `vitrine_backend/app/application/utils/jwt_handler.py` — `create_access_token()` agora aceita `user_id` + `token_version`; adiciona `jti` (UUID4) ao payload
- `vitrine_backend/app/application/services/auth_service.py` — `autenticar()` passa `usuario.id` e `usuario.token_version` para `create_access_token`
- `vitrine_backend/app/api/deps.py` — `get_current_user()` verifica blacklist por `jti` + `token_version`
- `vitrine_backend/app/api/routes/auth.py` — novos endpoints `POST /auth/logout` (revoga jti) e `POST /auth/logout-all` (incrementa token_version)
- `vitrine_backend/app/schemas/auth_schema.py` — schema `MessageResponse` adicionado
- `vitrine_backend/app/infrastructure/db/bootstrap.py` — migration para coluna `token_version`
- Testes: fixtures atualizadas com `token_version=0`

#### 🟡 S2 — Prefixo `/admin/` documentado como intencional

**Correção:** `vitrine_backend/app/api/routes/inventario.py` — comentário inline (linhas 48-66) no topo do router esclarecendo que o prefixo `/admin/inventario` é deliberado (ADR-012), operadores precisam dos endpoints, e não adicionar role checks desnecessários.

#### 🔴 S3 — `JWT_SECRET` agora é somente `.env` (não mais sobrescritível via DB)

**Correção:**
- `vitrine_backend/app/application/config_service.py` — nova constante `_CHAVES_SOMENTE_ENV = {"jwt_secret"}`; `get()` faz bypass do cache/DB para essas chaves; `set_many()` bloqueia escrita com warning
- `vitrine_backend/tests/services/test_config_service.py` — ajuste de asserção `test_mistura_chaves_validas_e_invalidas` para refletir o novo comportamento

#### 🟡 S4 — `GET /status/` com rate limit (10/min)

**Correção:** `vitrine_backend/app/api/routes/cache_status.py` — adicionado `@limiter.limit("10/minute")` + parâmetro `request: Request`.

#### 🟡 S5 — `POST /auth/register` com rate limit (5/min)

**Correção:** `vitrine_backend/app/api/routes/auth.py` — adicionado `@limiter.limit("5/minute")` + parâmetros `request: Request, response: Response`.

---

### ✅ Corrigidos (2026-05-21 — Pós-Revisão Sprint 2)

Correções dos gaps identificados na revisão adversarial pós-Sprint 2.

#### 🟡 G1 — Frontend chama `/auth/logout` no logout

**Correção:**
- `vitrine_frontend/src/api/auth.ts` — `logout()` agora é `async`, chama `POST /auth/logout` antes de limpar localStorage
- `vitrine_frontend/src/hooks/useAuth.ts` — `logout` do hook faz fire-and-forget `api.post('/auth/logout').catch(() => {})`

#### 🟡 G2 — Mudança de role invalida tokens

**Correção:** `vitrine_backend/app/application/services/auth_service.py:atualizar()` — se `dados.role != usuario.role`, incrementa `usuario.token_version += 1`.

#### 🟡 G3 — Migration limpa `jwt_secret` do banco

**Correção:** `vitrine_backend/app/infrastructure/db/bootstrap.py:_run_migrations()` — `DELETE FROM configuracoes WHERE chave = 'jwt_secret'`.

#### 🟡 G4 — `set_many()` retorna chaves ignoradas

**Correção:**
- `config_service.py` — `set_many()` agora retorna `list[str]` (chaves ignoradas)
- `configuracao_schema.py` — `ConfiguracaoResponse.ignoradas: list[str] = []`
- `configuracoes.py` — PATCH captura retorno e inclui no response

#### 🟡 G5 — Blacklist filtra tokens expirados

**Correção:** `vitrine_backend/app/api/deps.py:get_current_user()` — query de blacklist agora filtra `expires_at > datetime.now(timezone.utc)`.

#### 🟡 G6 — Otimização: pula blacklist para tokens < 5 min

**Correção:**
- `jwt_handler.py` — `iat` adicionado ao payload JWT
- `deps.py` — tokens com `iat` < 5 min pulam query de blacklist

#### 🧪 Novos testes (T11-T15)

**Correção:** `vitrine_backend/tests/api/test_api.py` — 4 novos testes:
- `test_logout_revoga_token` (T11) — logout individual insere na blacklist
- `test_logout_all_invalida_tokens_anteriores` (T12) — logout-all invalida tokens
- `test_mudanca_role_invalida_token` (T13) — mudança de role invalida tokens
- `test_status_endpoint_funciona` (T15) — GET /status/ retorna 200

---

### 🔴 Abertos (2026-05-21 — Revisão Adversarial)

Issues identificados por auditoria adversarial de código. Não corrigidos — requerem ação.

---

#### 🟡 F3-Qtde — Ranking Top 5 sem campo `quantidade`

**Severidade:** Baixa  
**Arquivo:** `vitrine_frontend/src/types/bi.ts` (ItemRankingDTO), `vitrine_backend/.../ranking`  
**Adicionado:** 2026-05-22  
**Descrição:** `ItemRankingDTO` (`codigo`, `produto`, `valor`) não inclui `quantidade`. O card Top 5 no Dashboard Consolidado não pode exibir o volume de vendas (unidades) junto da receita — informação útil pra diferenciar produtos de alto valor com poucas vendas vs. produtos populares.  
**Recomendação:** Adicionar campo `quantidade: number` ao `ItemRankingDTO` e preenchê-lo no backend (BI ranking query).

---

#### 🔴 P1 — Performance: Dashboard duplica chamadas de API no mount

**Severidade:** Alta  
**Arquivo:** `Dashboard.tsx` (L117 e L120-123)  
**Descrição:** Dois `useEffect` disparam no mount: o primeiro chama `buscar()` (KPIs + ranking), o segundo (com dependência `[comparar]`) roda imediatamente porque `comparar` muda de `undefined` para `true` no estado inicial — e chama `buscar(undefined, true)` novamente com `force=true`. Total: **4 chamadas de API para carregar a mesma coisa**.  
**Testes faltando:** Nenhum teste verifica número de chamadas no mount.

---

#### 🔴 P2 — Performance: Sem lazy loading — bundle inclui todas as 8 páginas BI

**Severidade:** Média  
**Arquivo:** `App.tsx`  
**Descrição:** Todos os componentes BI são importados estaticamente. O bundle inicial inclui Recharts, date-fns, e todo código BI mesmo para usuários operadores que nunca acessam BI. Bundle estimado ~2 MB (500 KB gzipped).  
**Recomendação:** `React.lazy(() => import(...))` + `Suspense`.

---

#### 🔴 P3 — Performance: BI carrega potencialmente GBs de dados na RAM

**Severidade:** Alta  
**Arquivos:** `factory.py`, `fluxo.py`, `transaction_source.py`, `relatorio.py`  
**Descrição:** Para 2 anos com ~5M itens: `get_items()` retorna `list[TransactionItem]` (~2 GB), `Fluxo.df` cria DataFrame (~1 GB), `TTLCache` retém por 1h com `maxsize=32`. `RelatorioTemporal` faz `vendas.df.copy()` dobrando consumo. KPI faz dois groupbys separados em vez de `.agg()` único. Risco de OOM.  
**Recomendação:** Limitar período máximo no frontend, ou implementar paginação/amostragem no backend.

---

#### 🟡 M1 — `_run_migrations()` chamado em toda requisição

**Arquivo:** `bootstrap.py`, `inventario.py`  
`init_db()` → `_run_migrations()` executa `ALTER TABLE` em toda requisição de inventário. Após a primeira, falha silenciosamente com `except Exception: pass`. Round-trip SQLite desnecessário em cada request. Deveria rodar apenas no lifespan.

---

#### 🟡 M2 — `_ADAPTER_CACHE` não é thread-safe e nunca é invalidado

**Arquivo:** `deps.py`, `alterdata/db.py`  
Race condition no primeiro acesso: duas requisições concorrentes podem criar dois `AlterdataProductSource`, cada um com pool PostgreSQL próprio (até 10 conexões). Se a config de ERP mudar, o cache nunca é limpo — precisa reiniciar o servidor.

---

#### 🟡 M3 — `sync_com_erro()` é código morto

**Arquivo:** `sync_service.py` (L65-74)  
Método que registra falha no `CacheStatus` nunca é chamado. Se `sync()` falhar em `source.get_all_products()`, a exceção propaga sem registro no banco. `CacheStatus` só é escrito em caso de sucesso.

---

#### 🟡 M4 — Observação sem limite de tamanho, concatenação infinita

**Arquivo:** `inventario.py`, `inventario_schema.py`, `domain/models/inventario.py`  
Cada re-scan com observação diferente concatena com `" | "`. String cresce sem limites. SQLite `TEXT` sem limite prático. Excel pode ter células muito longas.

---

#### 🟡 M5 — `useCountUp` reseta para 0 se target muda durante animação

**Arquivo:** `useCountUp.ts`  
Se o target muda enquanto animação roda (ex.: dados chegam em dois batches), o valor "pisca" voltando a 0 antes de subir. Efeito visual de bug mesmo sendo comportamentalmente correto.

---

#### 🟡 M6 — Cache do BI no frontend sem limite de tamanho

**Arquivo:** `biCache.tsx`  
`Map` em `useRef` com `set()` sem LRU, sem TTL, sem `maxEntries`. Na prática o usuário explora ~10-20 períodos, mas em teoria pode crescer indefinidamente.

---

#### 🟡 M7 — Excel export constroi tudo em RAM sem streaming verdadeiro

**Arquivo:** `exportador.py`, `routes/bi.py`  
`StreamingResponse(io.BytesIO(excel_bytes))` — o nome engana. Todo o Excel é construído em RAM (openpyxl), serializado em bytes, e só então servido. Para 50k+ produtos, pico de ~250 MB por exportação.

---

#### 🟡 M8 — Role redundante em localStorage sem validação

**Arquivo:** `useAuth.ts` (L59-65)  
`getRole()` faz fallback para `localStorage.getItem('role')` se o JWT falhar ao decodificar. O usuário pode modificar manualmente. Só afeta renderização condicional (backend sempre valida), mas é vetor de confusão.

---

#### 🟡 M9 — `RolesEnum.get_hierarchy()` nunca usado

**Arquivo:** `domain/enums.py`  
100% código morto. As verificações usam lista simples `usuario.role not in [...]`. Pode levar a inconsistências se alguém tentar usar a hierarquia no futuro.

---

#### 🟡 M10 — `isTokenAboutToExire` nunca chamado

**Arquivo:** `useAuth.ts` (L112-116)  
Função existe com lógica completa (threshold 5 min), mas nenhum componente a chama. Dead code.

---

#### 🟡 M11 — Config cache frontend nunca atualiza automaticamente

**Arquivo:** `configStore.ts`  
Cache singleton carregado uma vez (API ou localStorage). Se admin muda nome da loja, headers mostram valor antigo até F5.

---

#### 🟡 M12 — `setState` em componente desmontado na Busca

**Arquivo:** `Busca.tsx` (L42-53)  
Se o timeout de 300ms já disparou e o componente desmonta antes da Promise resolver, `setSearchResults` é chamado em componente desmontado. React 19 não crasha, mas loga warning.

---

#### 🟢 m1 — `_filenameFromHeaders` com regex frágil

**Arquivo:** `admin.ts`  
`content-disposition` com UTF-8 pode quebrar o regex. Nunca testado.

---

#### 🟢 m2 — `baixarCSVdeArray` não revoga URL.createObjectURL

**Arquivo:** `csv.ts`  
Cria blob URL mas nunca chama `URL.revokeObjectURL`.

---

#### 🟢 m3 — Nenhum `React.memo` no projeto

Toda prop inline (arrow functions, objetos literais) causa re-render em cascata. Especialmente crítico no Dashboard com 6 cards.

---

#### 🟢 m4 — Erro de token usa mesma mensagem para expirado e malformado

**Arquivo:** `jwt_handler.py`  
"Token inválido ou expirado" — impossível diagnosticar remote sem logs do servidor.

---

### ✅ Corrigidos (2026-05-25 — Auditoria Debug)

> **23 issues corrigidas em 6 sprints** (~2h de trabalho total)
> Relatório completo: `docs/debug-audit-2026-05-25.md`
> Plano de ação: `docs/action-plan-2026-05-25.md`
> Commit: `cdb135c`

#### 🔴 B1 — Rota `/admin/whatsapp/teste` chama função inexistente

**Correção:** `whatsapp.py:79-80` — Import corrigido para `_enviar_relatorio_whatsapp()`.

#### 🔴 B3 — `ajustarQuantidade()` lê estado stale

**Correção:** `Inventario.tsx:330-341` — Extraído `novaQtd` de dentro do callback do `setItens`.

#### 🔴 B4 — Engine PostgreSQL nunca disposto (vazamento de conexões)

**Correção:** `sync_service.py:116-124` — Engine capturado em variável e `engine.dispose()` no `finally`.

#### 🔴 B5 — GET /itens bloqueado em sessão encerrada mas export-excel funciona

**Correção:** `inventario.py:341` — `require_sessao_ativa` removido do GET. Operador recebe 403, supervisor/admin 200.

#### 🔴 B16/B24 — REGRESSÃO: Fixes documentados não aplicados

**Correção:** `admin.ts:12,17` — `job_id` alterado de `number` para `string`. `admin.py:19` — import de `logar_erro_interno` adicionado.

#### 🟡 B6 — `_get_estoque_db()` não consulta EAN

**Correção:** `inventario.py:173-193` — Segundo passo adicionado: busca por `ProdutoCodigo.codigo` para códigos não encontrados por `codigo_chamada`.

#### 🟡 B8 — ETL sem atomicidade (janela de banco vazio)

**Correção:** `sync_service.py:52-60` — DELETE + INSERT envoltos em `with self.db.begin():` (transação explícita).

#### 🟡 B18 — Polling de sync continua após desmontar Admin

**Correção:** `Admin.tsx:33,65,70-74,96` — `mountedRef` adicionado; guard contra criação de intervalo após cleanup.

#### 🟡 B19 — Erros do consolidado engolidos silenciosamente

**Correção:** `Inventario.tsx:83` — `catch (err) { console.error(...) }` adicionado.

#### 🟡 B10 — `ProtectedRoute` permite acesso se `allowedRoles` for undefined

**Correção:** `ProtectedRoute.tsx:7,10,17-22` — `allowedRoles` obrigatório (removido `?`). Busca route recebeu `allowedRoles` faltante.

#### 🟡 B12 — Logout com falha de rede mantém token válido

**Correção:** `useAuth.ts:84-91` — Timeout 5s adicionado; warning explícito sobre token ainda válido.

#### 🟡 B13 — Interceptor 401 faz full page reload

**Correção:** `client.ts:20-21` + `App.tsx` — Substituído `window.location.href` por `CustomEvent('auth:unauthorized')` + `AuthListener` com `useNavigate()`.

#### 🟡 B15 — `pausaEscaneio` nunca resetado se componente remontar

**Correção:** `Inventario.tsx:95` — `pausaEscaneio.current = false` adicionado no `useEffect` de montagem.

#### 🟡 B17 — `job_id` tipado como `number` (regressão, coberto por B16)

**Correção:** Incluso no B16.

#### 🟡 B2 — Email sem logos se `STATIC_DIR` não existir

**Correção:** `report_builder_email.py:64` — `STATIC_DIR.mkdir(parents=True, exist_ok=True)` adicionado.

#### 🟢 B9 — Prop `continuo` ainda existe no `LeitorCodigo.tsx`

**Correção:** `LeitorCodigo.tsx:6-9,53-61,107` — Prop `continuo` removido; lógica simplificada (leitura única).

#### 🟢 B20 — Modelo Claude hardcoded com versão 2024

**Correção:** `configuracoes.py:234` — `claude-3-haiku-20240307` → `claude-3-5-haiku-latest`.

#### 🟢 B21 — `_debug_items()` loga em INFO em produção

**Correção:** `factory.py:77,93,102` — `logger.info` → `logger.debug` (3 ocorrências).

#### 🟢 B23 — PK autoincrement redundante em `SyncJob`

**Decisão:** Tech debt consciente — não justifica migration. Mantido como está.

---

### ~~🟡 Dívida Técnica — Filtro `ativo` Desconectado do ERP~~ ✅ Corrigido

#### `Produto.ativo` agora lê `detalhe.stdetalheativo` do ERP

**O problema:** O adapter hardcodava `is_active=True` (linha 46 do `product_source.py`). Nenhum produto chegava como inativo.

**Correção (2026-05-25):**
1. `produto.sql` — Adicionado `COALESCE(d.stdetalheativo, true) as ativo` ao SELECT + GROUP BY
2. `product_source.py` — Hardcode `is_active=True` → `is_active=bool(row.get("ativo", True))`
3. Sync seguite vai popular `Produto.ativo` com o valor real do ERP

---

### ✅ UX Refactor + UI Fixes (2026-05-25)

#### 🟢 Layout centralizado (Busca pattern) — 6 páginas
- **Antes:** `flex flex-col px-4 py-4` — sem centralização, sem overflow-x-auto.
- **Depois:** `items-center overflow-x-auto` adicionado a Etiquetas, Inventário, Produtos, Configurações, Usuarios, Admin.
- **Commits:** `84b4a97`, `3680d23`

#### 🟢 Prepend: novo item ao topo da lista
- **Onde:** Etiquetas (`handleCodigo`) + Inventário (handleCodigo + handleLeituraNovoItem).
- **Como:** `[{...item}, ...prev].slice(0, 100)`.
- **Re-scan (Inventário):** Move ao topo + incrementa + destaca com `highlightedCode` + `animate-highlight-pulse` (1.5s).

#### 🟢 Configurações/Geral — espaçamento entre blocos
- **Problema:** `gap-12`+`divide-y` não era visível devido ao aninhamento de divs no JSX.
- **Solução:** `mb-10` (40px) em cada wrapper + `border-t border-border/20 pt-6` em Endereço e Metas.
- **Resultado:** Linha horizontal sutil + 40px de espaço entre Identidade, Endereço e Metas.
- **Commit:** `4c3894b`

#### 🟢 Configurações/Geral — inputs constritos
- **Endereço:** Container `ml-9` com `max-w-md` (448px).
- **Metas:** `max-w-[160px]` no próprio CompactInput — suficiente para `R$ 1.000.000.000`.
- **CompactInput:** `className` agora é mesclado com a classe base (não sobrescreve).
- **Logo:** `items-start` no branding content para upload não ficar deslocado.
- **Whitespace acima tab bar:** `py-4` → `pb-4 pt-0`.

#### 🟢 Usuarios — input senha não estica mais
- **Antes:** `sm:flex-1` — ocupava todo espaço restante, bem maior que username.
- **Depois:** `sm:w-auto sm:min-w-[200px]` — tamanho natural.

#### 🟢 Produtos — tabela mais larga
- `max-w-4xl` (896px) → `max-w-6xl` (1152px). Todas as 9 colunas visíveis sem scroll no desktop.

---

### 🟡 BI-01: Resumo do Dia comparava dados parciais com full-day do ano anterior

**Status:** ✅ **Corrigido (2026-05-26) — Hotfix frontend-only**

**Problema:** O `ResumoDia` no Dashboard comparava o último dia do período com o mesmo weekday do ano anterior (`findValorAnterior`), sem verificar se o último dia era parcial (hoje em andamento). Isso gerava variação artificial (ex: parcial vs full-day → -55% enganoso).

**Correção:** `ultimoEParcial` é calculado primeiro; quando verdadeiro, as variáveis `ant*Daily` (`antReceitaDaily`, `antTicketsDaily`, `antTicketMedioDaily`) são forçadas a `null`, fazendo o badge de variação cair no fallback `variacaoPeriodo` (kpisComp, já com `_filtrar_hora` do backend).

**Arquivo:** `vitrine_frontend/src/pages/bi/Dashboard.tsx` — ±20 linhas alteradas.

**Documentação completa:** `docs/hotfix-resumo-dia-parcial.md`

**Próximo passo:** Endpoint `/api/bi/diario/comparativo` delegado ao `architect` para comparação YoY com hora truncada.

---

### 🔴 Pré-existentes (Não Requerem Ação Imedita)

#### 🟡 A3: Export SKU exige `codigo` no query param

Backend retorna 400 se `codigo` não for passado com relatório `"sku"`. Frontend agora tem validação client-side, e o caller `Sku.tsx` já envia `codigo`.
