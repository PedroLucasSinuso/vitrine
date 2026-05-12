# Vitrine — Frontend

Frontend web do sistema **Vitrine** (antigo Price Checker), construído com React 19 + TypeScript + Vite 8 + Tailwind v4.

Interface para consulta de produtos, BI com gráficos, etiquetas, inventário multi-usuário e gestão de usuários.

---

## Stack

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

---

## Estrutura

```
src/
├── api/              # Cliente HTTP + funções por módulo
│   ├── client.ts     # Axios instance + interceptors (auth, 401 redirect)
│   ├── admin.ts      # Sync, configurações, inventário (sessões + itens)
│   ├── auth.ts       # Login
│   ├── bi.ts         # KPIs, receita, ranking, SKU, trocas, etc.
│   ├── produtos.ts   # Consulta de produtos por código/nome
│   └── usuarios.ts   # CRUD de usuários
├── components/       # Componentes reutilizáveis
│   ├── AdminHeader.tsx   # Header com nav grid, dropdown, logo, dark mode
│   ├── LeitorCodigo.tsx  # Leitor de código de barras via câmera
│   ├── ProtectedRoute.tsx # Guard de rota por role
│   ├── ToastContainer.tsx
│   ├── bi/               # Componentes de BI
│   │   ├── BiSubNav.tsx
│   │   ├── KpiCard.tsx
│   │   └── PeriodoForm.tsx
│   └── ui/
│       ├── ScrollToTop.tsx
│       └── Skeleton.tsx
├── hooks/            # Hooks customizados
│   ├── useAuth.ts        # Auth context (JWT decode, role, expiração)
│   ├── useCountUp.ts     # Animação de contagem
│   ├── useLocalStorage.ts
│   └── useToast.tsx      # Sistema de toast (feedback visual)
├── pages/            # Páginas
│   ├── Admin.tsx         # Sync ETL
│   ├── Busca.tsx         # Consulta de produtos por código/nome
│   ├── Configuracoes.tsx # Configurações do sistema (admin)
│   ├── Etiquetas.tsx     # Geração de etiquetas
│   ├── Home.tsx          # Pós-login com cards de navegação
│   ├── Inventario.tsx    # Inventário multi-usuário com sessões
│   ├── Login.tsx
│   ├── NotFound.tsx
│   ├── Usuarios.tsx      # Gestão de usuários (admin)
│   └── bi/               # BI (Dashboard, Receita, Ranking, etc.)
├── stores/
│   └── biCache.tsx    # Cache de requests BI (abort + stale-while-revalidate)
├── types/             # Tipos TypeScript
│   ├── admin.ts
│   ├── auth.ts
│   ├── bi.ts
│   ├── index.ts
│   ├── inventario.ts  # SessaoInventario, ItemInventario
│   └── produto.ts
└── utils/
    ├── csv.ts
    └── formatters.ts
```

---

## Inventário Multi-usuário

### Conceito

- **Supervisor** cria sessões de contagem, vê o consolidado de todos os operadores e gera relatório geral (TXT/Excel)
- **Operadores** têm acesso ao módulo de inventário, mas limitados a entrar em sessões existentes pelo código de convite e bipar itens
- Códigos iguais **do mesmo usuário** são somados (upsert no backend)
- Códigos iguais **entre usuários diferentes** são somados apenas na visão consolidada

### Fluxo

1. **Seleção de sessão** — lista de sessões ativas, botão "Nova Sessão" (supervisor), campo "Código da sessão" (todos)
2. **Bipagem** — scan via input ou câmera, cada item é enviado ao backend (upsert), lista local atualizada instantaneamente
3. **Consolidado** (supervisor) — toggle "Meus itens / Consolidado" mostra a soma total de todos os operadores dentro da sessão (read-only)
4. **Relatório Consolidado Geral** (supervisor) — botões "TXT Consolidado" e "Excel Consolidado" na tela de seleção de sessão baixam o relatório somando **todas as sessões ativas**

### Exportação

| Formato | Onde | Conteúdo | Uso |
|---|---|---|---|
| `.txt` | Dentro da sessão | `codigo;quantidade` | Coletor / sistema legado |
| `.xlsx` | Dentro da sessão | `código | grupo | família | produto` | Planilha Excel |
| `.txt` | **Consolidado Geral** (supervisor) | `codigo;quantidade` | ERP (ajuste de estoque apurado) |
| `.xlsx` | **Consolidado Geral** (supervisor) | `código | produto | grupo | família | quantidade` | Análise humana |

---

## Scripts

| Comando | Descrição |
|---|---|
| `npm run dev` | Dev server (Vite, proxy `/api` → `localhost:8000`, proxy `/static` → `localhost:8000`) |
| `npm run build` | TypeScript check + Vite build |
| `npm run preview` | Preview do build de produção |
| `scripts/dump_full_project.py` | Gera `dump_vitrine_completo.json` com todos os arquivos do back + front |

---

## Configuração

```env
VITE_API_URL=/api
```

- Em desenvolvimento, o Vite faz proxy de `/api` para `http://localhost:8000` e `/static` para `http://localhost:8000/static`
- Em produção, a API e os arquivos estáticos devem estar no mesmo domínio ou atrás de um reverse proxy
