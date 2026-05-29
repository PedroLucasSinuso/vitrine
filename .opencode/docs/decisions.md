# Architecture Decision Records

> Este documento captura decisões arquiteturais explícitas e implícitas, com seus tradeoffs e contexto.
> Formato: ADR (Architecture Decision Record) leve.
> Auditado em: 2026-05-21

---

## ADR-001: Monolith Backend

**Status:** Aceito

**Contexto:** Sistema interno para loja única. Equipe pequena. Necessidade de deploy simples.

**Decisão:** Backend monolítico em FastAPI, sem separação em microsserviços.

**Tradeoffs:**
- ✅ Deploy simples (único processo uvicorn)
- ✅ Desenvolvimento rápido (sem overhead de comunicação entre serviços)
- ✅ Debugging direto (tudo no mesmo processo)
- ❌ Escalabilidade limitada (tudo escala junto)
- ❌ APScheduler in-process roda em todos os workers
- ❌ Caches em memória não compartilhados entre workers

---

## ADR-002: Frontend/Backend Separation

**Status:** Aceito

**Contexto:** Necessidade de UI rica com React, independência de evolução do frontend.

**Decisão:** Frontend React (Vite + TypeScript) separado do backend FastAPI. Comunicação via REST.

**Tradeoffs:**
- ✅ Times podem evoluir frontend e backend independentemente
- ✅ Stack especializada para cada camada
- ❌ Duplicação de tipos (TypeScript types vs Pydantic schemas)
- ❌ Overhead de manutenção de contratos de API
- ❌ BI cache no frontend sem invalidação server-side (dados podem ficar obsoletos)

---

## ADR-003: JWT Stateless Authentication

**Status:** Aceito

**Contexto:** Simplicidade, evitar estado de sessão no servidor.

**Decisão:** Autenticação stateless via JWT (HS256), sem refresh token, sem blacklist, sem allowlist.

**Tradeoffs:**
- ✅ Sem estado no servidor (fácil de escalar horizontalmente... exceto pelos caches em memória)
- ✅ Implementação simples (PyJWT + bcrypt)
- ❌ **Token com 7 dias de expiração:** janela de exposição longa se houver vazamento
- ❌ **Sem revogação:** impossível invalidar token de usuário desligado antes da expiração
- ❌ **Sem refresh token:** rotação de chaves ou mudança de permissões só valem após novo login
- ❌ Role armazenado em paralelo no localStorage do frontend (fonte alternativa que pode dessincronizar)

**Nota:** Para um sistema interno de loja com poucos usuários, 7 dias é aceitável. Se houver requisitos de compliance (LGPD, PCI), reduzir para 8h + implementar refresh token.

---

## ADR-004: Domain Models Coupled to SQLAlchemy ORM

**Status:** Aceito (consciente do risco)

**Contexto:** Produtividade inicial vs pureza arquitetural. SQLAlchemy é o ORM padrão do ecossistema Python.

**Decisão:** Models de domínio (`domain/models/`) herdam diretamente de `SQLAlchemy declarative_base`.

**Tradeoffs:**
- ✅ Desenvolvimento rápido (models = tabelas = schemas)
- ✅ Menos arquivos/indireção
- ❌ **Domínio não é puro:** regras de negócio (`markup`, `margem`) ficam no model ORM
- ❌ **Testes unitários exigem sessão SQLAlchemy** (mais lentos, mais setup)
- ❌ **Trocar de ORM exige reescrever o domínio inteiro**
- ❌ Interface `IProdutoRepository` retorna `Produto` (ORM model), não um objeto de domínio puro

**Mitigação futura:** Se o domínio crescer, extrair regras de negócio para objetos de domínio puros (dataclasses/value objects) e usar os models ORM apenas para persistência (padrão Repository com mapper).

---

## ADR-005: SQLite para Configurações e Cache (Temporário)

**Status:** Aceito (temporário, documentado como tal)

**Contexto:** Projeto começou com PostgreSQL legado do cliente como única fonte. Necessidade de armazenar settings de forma flexível sem exigir PostgreSQL.

**Decisão:** SQLite como banco auxiliar para settings, usuários, cache de produtos, jobs de sync.

**Tradeoffs:**
- ✅ Zero configuração de infra (arquivo .db local)
- ✅ Fácil de fazer backup/restore
- ❌ **Sem suporte a concorrência:** `check_same_thread=False` é workaround, não solução
- ❌ **Múltiplos workers uvicorn corrompem o SQLite** (deadlock ou `database is locked`)
- ❌ Sem point-in-time recovery, sem replicação
- ❌ PostgreSQL do cliente continua sendo necessário para ETL e BI

**Trigger para migrar:** Quando o sistema precisar de >1 worker uvicorn, ou quando houver requisitos de HA.

---

## ADR-006: In-Process Cache (Não Compartilhado)

**Status:** Aceito (consciente do risco)

**Contexto:** Evitar dependência externa (Redis, Memcached) para um sistema de loja única.

**Decisão:** Cache em dicionários globais no módulo Python (`_ADAPTER_CACHE`, `_cache` no `config_service`, `TTLCache` no `transaction_source`).

**Tradeoffs:**
- ✅ Zero dependência externa
- ✅ Simples de implementar e debugar
- ❌ **Cada worker uvicorn tem seu próprio cache** — dados inconsistentes entre workers
- ❌ TTL de 30s no config_service reduz o problema, mas não elimina
- ❌ TTLCache de transações com 1h de TTL pode servir dados obsoletos se sync rodar

**Migração futura:** Substituir por Redis quando houver múltiplos workers ou necessidade de cache compartilhado.

---

## ADR-007: APScheduler In-Process (Sem Liderança)

**Status:** Aceito (consciente do risco)

**Contexto:** Necessidade de sync agendado ETL e envio de notificações periódicas.

**Decisão:** APScheduler rodando dentro do processo uvicorn, sem mecanismo de liderança (leader election).

**Tradeoffs:**
- ✅ Simples: scheduler.start() no lifespan
- ✅ Sem dependência externa (Redis, Celery, etc.)
- ❌ **Com múltiplos workers, o scheduler roda em TODOS eles**
- ❌ Sync e notificações disparam N vezes (N = número de workers)
- ❌ ThreadPoolExecutor single-thread (`max_workers=1`) para sync serializa execução

**Mitigação atual:** O sync usa `SyncJob` no SQLite para tracking, mas não previne execução concorrente. Se dois workers iniciarem sync simultaneamente, o segundo sobrescreverá os dados do primeiro durante o DELETE+INSERT.

**Solução futura:** Usar lock no banco (`SELECT ... FOR UPDATE` ou tabela de locks) ou migrar para Celery/scheduler externo.

---

## ADR-008: ETL Full-Reload (Sem Incremental)

**Status:** Aceito (consciente do risco)

**Contexto:** PostgreSQL do cliente (Alterdata) não tem coluna de atualização confiável para incremental.

**Decisão:** SyncService faz `DELETE + INSERT` completo a cada execução.

**Tradeoffs:**
- ✅ Simples de implementar e debugar
- ✅ Garante consistência (não precisa detectar mudanças)
- ❌ **DELETE + INSERT não é atômico** — dados inconsistentes durante o sync
- ❌ Operação lenta para 50k+ produtos
- ❌ Sem isolation: queries de busca durante o sync podem retornar vazio ou parcial

**Mitigação:** Usar transação SQLite no SyncService `db.commit()` após o insert. O problema é que o SQLite não suporta concorrência de leitura durante transação de escrita.

---

## ADR-009: Config Management com Múltiplas Fontes de Verdade

**Status:** Aceito (migração em andamento)

**Contexto:** Migração gradual de configurações do `.env` para o SQLite (editável via UI).

**Decisão:** `ConfigService` lê na ordem: (1) cache TTL → (2) SQLite → (3) `.env` → (4) default. Com seed automático do `.env` para SQLite.

**Tradeoffs:**
- ✅ UI pode editar configurações sem reiniciar o servidor
- ✅ Migração transparente (configs existentes no .env são copiadas para SQLite)
- ✅ Retrocompatibilidade: se voltar o deploy, .env ainda funciona
- ❌ **Múltiplas fontes de verdade** (`.env`, SQLite, cache, localStorage do frontend)
- ❌ Race condition: seed automático com `IntegrityError` catch (+ rollback + refetch)
- ❌ Cache de 30s no backend + localStorage no frontend → delay entre salvar e ver o valor atualizado

---

## ADR-010: BI Domain Isolado do ORM Principal

**Status:** Aceito (bom design)

**Contexto:** BI precisa de visão agregada de transações do ERP, não do cache SQLite local.

**Decisão:** BI domain objects (`Vendas`, `Trocas`, `Perdas`, `Consumo`) são Pure Python, alimentados por `TransactionSource` (adapter). ORM não entra no pipeline de BI.

**Tradeoffs:**
- ✅ BI testável sem banco de dados
- ✅ Troca de ERP não impacta lógica de BI
- ✅ Separação clara entre dados operacionais (SQLite) e dados analíticos (PostgreSQL do ERP)
- ❌ Cada requisição BI faz query no PostgreSQL do cliente (sem cache server-side compartilhado)
- ❌ `criar_dominio()` carrega TODOS os itens do período em memória — para ERPs com milhões de registros, pode ser problematico

---

## ADR-011: Frontend sem Reactive State Library

**Status:** Aceito (consciente do risco)

**Contexto:** Projeto começou simples, sem necessidade de estado global complexo.

**Decisão:** Gerenciamento de estado via `localStorage` + React Context + singletons em módulo.

**Tradeoffs:**
- ✅ Zero dependências (sem Redux, Zustand, Jotai)
- ✅ Curva de aprendizado baixa
- ❌ `configStore.ts` é singleton mutável — componentes não re-renderizam quando o cache muda
- ❌ `biCache.tsx` usa `Map` em `useRef` — mutação não reativa
- ❌ Estado duplicado: role no localStorage + role no JWT decode
- ❌ Dark mode manipula DOM diretamente (`document.documentElement.classList`)

---

## ADR-012: Operador com Página Própria (/inventario)

**Status:** Aceito

**Contexto:** Operadores precisam acessar o inventário para contar estoque, mas o módulo ficava dentro de `/admin/` (rota de administradores). Operadores com acesso a `/admin/` poderiam se sentir confusos ou tentar acessar funcionalidades que não lhes pertencem.

**Decisão:** Criar uma rota `/inventario` fora do prefixo `/admin` exclusiva para operadores. Administradores e supervisores continuam usando `/admin/inventario`. A homepage do operador (`/home/operador`) mostra cards grandes (Busca + Inventário) sem links administrativos.

**Tradeoffs:**
- ✅ Separação clara de responsabilidades (operador ≠ admin)
- ✅ Operador não vê funcionalidades admin que não pode usar
- ✅ Admin/supervisor mantêm acesso total via `/admin/inventario`
- ✅ Preparado para futura separação de roles (admin ≠ supervisor)
- ❌ Duplicação de rota (dois entry points para o mesmo módulo)
- ❌ Header precisa detectar role para montar link correto (`linkPara()`)
- ❌ Se um admin quiser entrar como operador, precisa de outra conta

---

## ADR-013: Escaneio Único (Sem Contínuo) + Flash na Câmera

**Status:** Aceito

**Contexto:** A câmera do `LeitorCodigo` operava em modo contínuo (`continuo`), lendo códigos repetidamente sem parar. Isso causava:
- Múltiplas chamadas de API para o mesmo código em segundos
- Dificuldade de parar a leitura quando um modal (ex: produto não cadastrado) era aberto
- Consumo excessivo de bateria em dispositivos móveis

**Decisão:** Remover o modo `continuo`. A câmera lê um código, fecha automaticamente, e o operador reabre com um toque. Adicionar:
- Botão flash/torch toggle via `MediaStreamTrack.applyConstraints({ advanced: [{ torch }] })`
- Cooldown global de 2s (`ultimaQualquerLeitura`) para evitar bombardeio de API caso o usuário escaneie o mesmo código muito rápido
- Per-code cooldown de 1.5s (`ultimaLeitura`) para evitar duplicatas acidentais
- `stoppedRef` para impedir callbacks de frame após parada
- `pausaEscaneio` ref para bloquear leitura durante modal aberto
- 500ms grace window ao fechar modal para evitar re-leitura imediata

**Tradeoffs:**
- ✅ Muito mais confiável que contínuo (sem duplicatas, sem chamadas fantasmas)
- ✅ Operador controla quando escanear (mais previsível)
- ✅ Flash funciona em Android Chrome e iOS Safari 13+
- ✅ Sem dependências adicionais
- ❌ Menos produtivo para grandes contagens (operador precisa tocar para cada scan)
- ❌ Flash/torch não funciona em alguns dispositivos iOS mais antigos
- ❌ Cooldown de 2s pode frustrar operador experiente

**Mitigação para produtividade:** Operador pode ajustar quantidade com +/- após escanear, evitando escanear o mesmo SKU 10x.

---

## ADR-014: Observacao em Item de Inventário

**Status:** Aceito

**Contexto:** Durante a contagem de inventário, operadores e supervisores precisam registrar observações sobre itens (ex: "produto danificado", "embalagem amassada", "faltando 2 unidades"). Anteriormente, o sistema só permitia quantidade. Observações só existiam no endpoint `POST /produtos/nao-encontrado` para produtos não cadastrados.

**Decisão:** Adicionar campo opcional `observacao` (string) ao `ItemInventario`:
- Coluna `observacao TEXT NULL` no SQLite
- Campo `observacao?: str = ""` nos schemas Pydantic
- Campo `observacao?: string` nos types TypeScript
- Merge de observação se o item já existir (concatena com newline)
- Terceira aba "Observações" no Excel gerado
- Backward compatible: schemas com default `""`, `nullable=True` no model, frontend trata como vazio se ausente

**Tradeoffs:**
- ✅ Operador pode registrar anomalias durante a contagem
- ✅ Supervisor vê observações no consolidado e no Excel
- ✅ Terceira aba no Excel facilita auditoria
- ✅ Merge evita perda de observações de múltiplos operadores
- ❌ Observação só aparece no modal de "não cadastrado" (não na lista principal por simplicidade)
- ❌ Merge simples (concat) pode ficar confuso se muitos operadores comentarem
- ❌ Sem edição de observação depois de criada (só merge)

---

## ADR-015: Geração de Excel no Backend

**Status:** Aceito

**Contexto:** Anteriormente, a exportação de Excel do inventário dependia de biblioteca JavaScript no frontend (`xlsx`). Isso significava:
- Todo o processamento de dados precisava ser baixado e transformado no navegador
- O delta (diferença entre contagem e sistema) precisava ser calculado no frontend
- A dependência `xlsx` aumentava o bundle size
- Operadores em dispositivos lentos sofriam com processamento pesado

**Decisão:** Gerar o arquivo `.xlsx` no backend (openpyxl) com 3 abas:
1. **Contagem** — itens registrados com código, nome, grupo, família, quantidade, observação
2. **Delta** — diferença entre contagem e estoque do sistema (com colunas: contagem, sistema, diferença, status OK/sobra/falta)
3. **Observações** — apenas itens com observação preenchida (só aparece se houver ao menos 1)

Dois endpoints novos:
- `GET /admin/inventario/sessoes/{id}/exportar-excel` — por sessão
- `GET /admin/inventario/consolidado-geral/exportar-excel` — consolidadas

**Tradeoffs:**
- ✅ Removida dependência `xlsx` do frontend
- ✅ Processamento no servidor (mais rápido que JS no mobile)
- ✅ Delta calculado no backend (correto, com dados do sistema)
- ✅ Terceira aba de observações invisível se vazia
- ✅ Download direto com `Content-Disposition`
- ❌ Backend precisa de `openpyxl` (já instalado para BI)
- ❌ Requer streaming de arquivo grande para muitas sessões
- ❌ Backend precisa buscar dados do sistema para calcular delta (mais queries)

---

## ADR-016: Macro-Economic Indicators — Live Fetch + Transparency

**Status:** Aceito (2026-05-28)

**Contexto:** O módulo Intelligence precisa de indicadores macroeconômicos (Selic, IPCA, IGP-M, INPC) para contextualizar o desempenho da loja. Anteriormente, 3 valores estavam hardcoded em `Settings` (`ipca_alimentacao_12m=7.8`, `ipca_geral_12m=4.5`, `selic=14.75`) e injetados via `macro_collector.py` sem uso real pelo TemplateProvider.

**Decisão:**

1. **Zero hardcoded** — todos os indicadores são buscados ao vivo do Banco Central (SGS API). Nenhum valor em `.env` ou `Settings`.
2. **Cache apenas para dados mensais**, e apenas no mês vigente:
   - IPCA, IGP-M, INPC: se já foram buscados e armazenados neste mês calendário, usa cache. Mês seguinte → re-busca.
   - Selic (série 432, meta COPOM): **sempre ao vivo**, sem cache.
3. **Transparência total de frescor**:
   - Todo indicador exibe `consultado_em` (timestamp da última consulta).
   - Indicadores mensais mostram `periodo_ref` (mês a que o dado se refere, ex: "Mai/2026").
4. **"API indisponível" é estado explícito**:
   - Se a API do BC falhar, o indicador retorna `disponivel=False` com `mensagem` descritiva.
   - Frontend renderiza card vermelho com tooltip de erro. Não esconde nem fallback silencioso.
5. **Fetch paralelo** — `asyncio.gather` para todas as séries simultaneamente.
6. **Detector condicional** — `MacroContextoDetector` só gera insights para indicadores com `disponivel=True`.
7. **Remover** `ipca_alimentacao_12m`, `ipca_geral_12m`, `selic` de `app/core/config.py`.

**Tradeoffs:**
- ✅ Dados sempre frescos e reais — sem ilusão de acurácia
- ✅ Transparência com o usuário (vê timestamp, vê falhas)
- ✅ Código mais simples (sem cascata de fallbacks)
- ❌ Selic (sempre ao vivo) adiciona ~300-500ms de latência à Intelligence page
- ❌ API do BC pode ficar fora do ar — indicadores ficam "indisponíveis" até恢复正常
- ❌ Cache mensal expira no fim do mês: se API falhar nos primeiros dias do mês novo, indicador fica "indisponível" mesmo com dado do mês anterior disponível

**Séries BC SGS:**
| Indicador | Série | Frequência |
|---|---|---|
| Selic (meta) | 432 | Reunião COPOM |
| IPCA geral (12m) | 433 | Mensal |
| IPCA Alimentação (12m) | 1635 | Mensal |
| IGP-M (12m) | 189 | Mensal |
| INPC (12m) | 188 | Mensal |
| Taxa desemprego | 24369 | Mensal |

---

## ADR-017: SQLite como Cache Transparente via ProductSource

**Status:** Proposto

**Contexto:**
- O ERP (Alterdata/PostgreSQL) não tem `updated_at`, triggers ou CDC para detectar mudanças incrementais em produtos/preços.
- A única maneira de sincronizar é DELETE+INSERT completo em intervalo curto (TTL).
- O SQLite (`price_checker.db`) serve como cache local para consultas de catálogo (produtos, preços, estoque, EAN).
- O PostgreSQL do ERP não é controlado pelo app — pode cair, estar lento ou em outra cidade via VPN.
- Hoje o SQLite é acessado diretamente pelas rotas HTTP (`produto_service.py`), enquanto o BI/Intelligence já usa `TransactionSource` (adapter PostgreSQL).

**Decisão:**
Criar uma **camada de cache transparente** atrás do `ProductSource` (adapter PostgreSQL):

```
Rota HTTP → ProductSource (interface) → ProdutoCacheSource (decorator/impl)
                                         ├── SQLite (cache local, TTL configurável)
                                         └── AlterdataProductSource (PostgreSQL, fallback)
```

Fluxo:
1. `ProductSource.buscar_por_codigo(codigo)` → `ProdutoCacheSource` verifica SQLite
2. Se cache **quente** (idade < TTL): retorna direto (~1ms)
3. Se cache **frio** (idade ≥ TTL): delega ao `AlterdataProductSource`, popula SQLite, retorna
4. Se cache **vazio** (nunca sincronizado): delega ao PostgreSQL, popula SQLite, retorna

**Sync (ETL) simplificado:**
- Não precisa mais fazer DELETE+INSERT de todos os produtos
- O sync vira um **warm-up assíncrono**: percorre todos os produtos e popula o cache
- Rotas HTTP não sabem que SQLite existe — chamam `ProductSource` como se fosse o banco real

**Mudanças necessárias:**

| Arquivo | O que muda |
|---|---|
| `ProductSource` (interface) | Métodos existentes (`buscar_por_codigo`, `listar_todos`, etc) |
| `AlterdataProductSource` | Implementação atual (já lê PostgreSQL via queries SQL) |
| `ProdutoCacheSource` | **Novo** — wrapper que gerencia cache SQLite + delega para Alterdata |
| `produto_service.py` / `produto_service_domain.py` | Remover ou simplificar (lógica migra para o cache source) |
| `sync_service.py` / `run_etl.py` | Simplificar: não precisa mais mapear para ORM, só popular cache |
| `app/infrastructure/db/session.py` | Pode remover engine SQLite ou manter só para auth/config/notificações |
| `deps.py` | `get_product_source()` retorna `ProdutoCacheSource` (que internamente chama `AlterdataProductSource`) |

**Riscos mapeados:**

| Risco | Mitigação |
|---|---|
| 🔴 Cache frio na primeira consulta após TTL expirar → latência alta | `warm-up` assíncrono pós-sync; indicador de staleness no header da resposta |
| 🔴 DELETE+INSERT atual é atômico? | Atual usa transação, mas tabela temporária + swap é mais seguro |
| 🟡 Staleness: usuário vê preço de 5 min atrás | TTL configurável (default 2 min); header `X-Cache-Age` |
| 🟡 Duas fontes de cache concorrentes (sync vs consulta direta) | `ProdutoCacheSource` é a ÚNICA porta de entrada para dados de produto |
| 🟢 Mais complexidade (mais uma camada) | Compensado pela remoção de `sync_service.py` + `run_etl.py` + modelos ORM de catálogo |

**Relação com `TransactionSource`:**
- `TransactionSource` (BI/Intelligence) continua consultando PostgreSQL direto — são dados analíticos (vendas, trocas), não de catálogo. Cache não faz sentido para agregações.
- `ProductSource` (catálogo) ganha cache porque é consulta pontual (busca por código, listagem) com alta frequência e dados relativamente estáveis.

**Tradeoffs:**
- ✅ Rotas HTTP desacopladas do SQLite — cache vira detalhe de implementação
- ✅ Sync não precisa mais mapear para ORM — só popular cache
- ✅ Se PostgreSQL cair, cache quente ainda serve dados (degradação graciosa)
- ✅ Staleness é explícito e mensurável (header, timestamp)
- ❌ Complexidade adicional (camada de cache)
- ❌ Primeira consulta após TTL expirar paga latência do PostgreSQL
- ❌ DELETE+INSERT continua sendo a única opção (sem delta do ERP) — mas vira responsabilidade do cache, não do sync
