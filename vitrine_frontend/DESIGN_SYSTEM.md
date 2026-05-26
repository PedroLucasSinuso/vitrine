# Vitrine Design System

> Sistema de design global para o SaaS Vitrine.
> Aparência enterprise premium consistente — inspirado em Stripe, Linear e Retool.

---

## Índice

1. [Filosofia](#1-filosofia)
2. [Tokens Visuais](#2-tokens-visuais)
3. [Spacing Scale](#3-spacing-scale)
4. [Radius Scale](#4-radius-scale)
5. [Tipografia](#5-tipografia)
6. [Sombras](#6-sombras)
7. [Cores](#7-cores)
8. [Padrões de Cards](#8-padrões-de-cards)
9. [Padrões de Tabelas](#9-padrões-de-tabelas)
10. [Padrões de Formulários](#10-padrões-de-formulários)
11. [Padrões de Layout](#11-padrões-de-layout)
12. [Animações](#12-animações)
13. [Componentes](#13-componentes)
14. [Temas](#14-temas)
15. [Guia de Uso](#15-guia-de-uso)

---

## 1. Filosofia

```
Token-first    → Todo valor visual passa por uma variável CSS, nunca hardcoded
Composição     → Wrappers que compõem, não props infinitas
Consistência   → Um único design token para cada conceito visual
Escuro nativo  → Dark mode único via useTheme(), sem sistemas concorrentes
Anti-fragil    → Fallbacks explícitos em todos os tokens
```

### Hierarquia de decisão

```
1. Existe um token?   → USE-O
2. Existe um wrapper? → USE-O
3. Existe um componente? → USE-O
4. Se não existe → crie seguindo os padrões deste documento
```

---

## 2. Tokens Visuais

Todos os tokens são definidos em:
- **`src/themes/tokens.css`** — defaults com `:root` (executável)
- **`src/index.css`** — `@theme` que referência `var(--token)` para o Tailwind v4
- **`src/themes/theme-vitrine.css`** — tema claro (override via `[data-theme="vitrine"]`)
- **`src/themes/theme-flagship.css`** — tema escuro (override via `[data-theme="flagship"]`)

### Arquitetura de cascata

```
tokens.css (:root defaults)
    ↓
index.css (@theme → var(--token))
    ↓
theme-*.css ([data-theme="..."] → override)
    ↓
Tailwind v4 utilities (bg-primary, text-text-muted, etc.)
```

### Convenção de nomenclatura

```
--color-{categoria}-{especificacao}
--font-{tipo}
--radius-{tamanho}
--shadow-{elemento}
--space-{valor}
--duration-{velocidade}
--ease-{tipo}
```

---

## 3. Spacing Scale

Todas as distâncias no sistema usam uma escala de 4px.

| Token   | Rem   | Pixels | Uso                          |
|---------|-------|--------|------------------------------|
| `--space-1` | 0.25rem | 4px  | Micro espaçamentos          |
| `--space-2` | 0.5rem  | 8px  | Gaps internos pequenos      |
| `--space-3` | 0.75rem | 12px | Gaps médios, padding sm     |
| `--space-4` | 1rem    | 16px | Padding base                |
| `--space-5` | 1.25rem | 20px | Padding largo               |
| `--space-6` | 1.5rem  | 24px | **Card padding** padrão     |
| `--space-8` | 2rem    | 32px | Section gap                 |
| `--space-10`| 2.5rem  | 40px | Page padding                |
| `--space-12`| 3rem    | 48px | Large section gap           |
| `--space-16`| 4rem    | 64px | Header height               |

### Utility classes disponíveis

```css
gap-space-{1..16}   /* gap */
p-space-{1..16}     /* padding */
```

---

## 4. Radius Scale

| Token        | Rem    | Pixels | Uso                              |
|--------------|--------|--------|----------------------------------|
| `--radius-sm`   | 0.25rem | 4px  | Inputs, badges                  |
| `--radius-md`   | 0.375rem| 6px  | Badges pequenos                 |
| `--radius-lg`   | 0.5rem  | 8px  | Botões, cards secundários       |
| `--radius-xl`   | 0.75rem | 12px | **Cards principais**, modal     |
| `--radius-2xl`  | 1rem    | 16px | Hero cards                      |
| `--radius-full` | 9999px  | —    | Pills, status dots              |

**Regra:** O radius padrão de cards e containers é `--radius-xl` (12px). Componentes interativos (botões) usam `--radius-lg` (8px) no tamanho `md`.

---

## 5. Tipografia

### Fontes

| Token | Fonte | Uso |
|-------|-------|-----|
| `--font-body` | Inter | Corpo de texto, labels, tabelas |
| `--font-display` | Hanken Grotesk | **Títulos**, KPIs, hero sections, valores destacados |
| `--font-mono` | JetBrains Mono | Códigos, valores monetários, dados tabulares |

### Type Scale

| Token    | Tamanho | Uso principal                      |
|----------|---------|------------------------------------|
| `--text-2xs` | 10px | Metadados, timestamps            |
| `--text-xs`  | 11px | Labels de formulário, badges     |
| `--text-sm`  | 12px | **Tabelas**, texto auxiliar      |
| `--text-base`| 13px | Parágrafos compactos             |
| `--text-md`  | 14px | **Corpo de texto padrão**        |
| `--text-lg`  | 16px | Parágrafos principais            |
| `--text-xl`  | 18px | Subtítulos, headlines pequenos   |
| `--text-2xl` | 20px | Headlines de seção               |
| `--text-3xl` | 24px | Headlines grandes                |
| `--text-4xl` | 30px | Hero headlines                   |

### Utility classes

```css
.font-display { font-family: var(--font-display); }
.text-2xs { font-size: var(--text-2xs); }
/* ... até text-4xl */
.tracking-tight  { letter-spacing: var(--tracking-tight); }
.tracking-wider  { letter-spacing: var(--tracking-wider); }
.tracking-widest { letter-spacing: var(--tracking-widest); }
```

### Hierarquia visual

```
Página:     font-display + text-xl (h1)
Seção:      font-display + text-lg (h2)  
Card:       font-body + text-md (h3, conteúdo)
KPI:        font-display + text-2xl (valor)
Label:      font-body + text-xs + tracking-wider
Table:      font-body + text-sm
Mono:       font-mono + text-sm (códigos, valores)
```

---

## 6. Sombras

| Token | Uso | Vitrine (claro) | Flagship (escuro) |
|-------|-----|-----------------|-------------------|
| `--shadow-sm` | Geral | `0 1px 2px rgb(0 0 0 / 0.05)` | — |
| `--shadow-card` | **Cards padrão** | `0 1px 3px rgb(0 0 0 / 0.10)` | `0 4px 12px rgba(0,0,0,0.25)` |
| `--shadow-card-hover` | Card hover | `0 4px 6px rgb(0 0 0 / 0.10)` | `0 8px 24px rgba(0,0,0,0.35)` |
| `--shadow-modal` | Modal | `0 10px 25px rgb(0 0 0 / 0.15)` | `0 25px 50px rgba(0,0,0,0.60)` |
| `--shadow-kpi` | KPI cards | `0 1px 3px rgba(5,150,105,0.10)` | `0 4px 12px rgba(129,140,248,0.15)` |
| `--shadow-toast` | Toast | `0 4px 6px rgb(0 0 0 / 0.10)` | `0 10px 20px rgba(0,0,0,0.40)` |

### Regras de shadow

- **Cards padrão** usam `shadow-card` (sutil, elevado)
- **Cards interativos** sobem para `shadow-card-hover` no hover
- **Modais** usam `shadow-modal` (mais profundo, distância do fundo)
- **KPIs** usam `shadow-kpi` com glow na cor primária
- **Botões primary** usam `shadow-sm`

---

## 7. Cores

### Paleta Semântica

| Token | Vitrine | Flagship | Uso |
|-------|---------|----------|-----|
| `--color-primary` | `#059669` | `#818cf8` | Ação principal, links, indicadores |
| `--color-accent` | `#f59e0b` | `#fbbf24` | Destaque secundário |
| `--color-info` | `#3b82f6` | `#60a5fa` | Informação |
| `--color-success` | `#10b981` | `#34d399` | Sucesso, online |
| `--color-warning` | `#f59e0b` | `#fbbf24` | Atenção, idle |
| `--color-danger` | `#ef4444` | `#fb7185` | Erro, offline, perigo |

### Superfícies

| Token | Vitrine | Flagship |
|-------|---------|----------|
| `--color-bg-page` | `#f8fafc` (slate-50) | `#0b1120` (deep navy) |
| `--color-bg-card` | `#ffffff` | `rgba(30,41,59,0.45)` (glass) |
| `--color-bg-sidebar` | `#ffffff` | `#060d1a` |
| `--color-bg-input` | `#ffffff` | `#060d1a` |

### Texto

| Token | Vitrine | Flagship |
|-------|---------|----------|
| `--color-text-primary` | `#0f172a` | `#f8fafc` |
| `--color-text-secondary` | `#475569` | `#e2e8f0` |
| `--color-text-muted` | `#94a3b8` | `#94a3b8` |

### Borders

| Token | Vitrine | Flagship |
|-------|---------|----------|
| `--color-border` | `#e2e8f0` | `rgba(51,65,85,0.60)` |
| `--color-border-input` | `#cbd5e1` | `#1e293b` |
| `--color-border-focus` | `#059669` | `#818cf8` |

### Chart (data viz)

| Token | Vitrine | Flagship |
|-------|---------|----------|
| `--color-chart-1` | `#059669` | `#818cf8` |
| `--color-chart-2` | `#f59e0b` | `#34d399` |
| `--color-chart-3` | `#6366f1` | `#fbbf24` |
| `--color-chart-4` | `#06b6d4` | `#fb7185` |
| `--color-chart-5` | `#64748b` | `#60a5fa` |

---

## 8. Padrões de Cards

### Card (`components/ui/Card.tsx`)

```tsx
<Card variant="bordered" padding="lg">
  conteúdo
</Card>
```

**Variantes:**

| Variant | Visual | Quando usar |
|---------|--------|-------------|
| `default` | Fundo branco + shadow sutil | Container genérico |
| `bordered` | Borda + shadow | Seções dentro de página |
| `interactive` | Borda + hover com primary | Cards clicáveis |
| `elevated` | Shadow mais forte | Cards de destaque |
| `danger` | Fundo danger-light | Alertas/erros em card |
| `compact` | Padding reduzido | Cards densos, tabelas |

**Paddings:**

| Valor | Rem | Quando usar |
|-------|-----|-------------|
| `sm` | 1rem (16px) | Cards densos |
| `md` | 1.25rem (20px) | **Padrão** |
| `lg` | 1.5rem (24px) | Cards de destaque |
| `none` | 0 | Quando o conteúdo controla padding |

### Card presets (CSS utilities)

```css
.card-base       /* bg + radius-xl + shadow-card */
.card-bordered   /* .card-base + border */
.card-elevated   /* .card-base + shadow-card-hover */
.card-interactive /* .card-base + border + hover effects */
.card-hover:hover /* translateY(-1px) + shadow-card-hover */
```

---

## 9. Padrões de Tabelas

### DataTable (`components/ui/DataTable.tsx`)

```tsx
import DataTable, { type Column } from '../components/ui/DataTable'

const columns: Column<MeuTipo>[] = [
  { key: 'nome', label: 'Nome', sortable: true },
  { key: 'valor', label: 'Valor', align: 'right', render: (item) => formatCurrency(item.valor) },
]

<DataTable
  data={itens}
  columns={columns}
  rowKey={(item) => item.id}
  loading={loading}
  sortBy={sortBy}
  sortOrder={sortOrder}
  onSort={handleSort}
  page={page}
  pageSize={pageSize}
  total={total}
  onPageChange={setPage}
  onPageSizeChange={setPageSize}
  empty={<EmptyState title="Nenhum item" />}
/>
```

**Interface `Column<T>`:**

| Prop | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| `key` | `string` | Sim | Chave única da coluna |
| `label` | `string` | Sim | Texto do header |
| `sortable` | `boolean` | Não | Habilita ordenação |
| `align` | `'left' \| 'right' \| 'center'` | Não | Alinhamento |
| `hide` | `'sm' \| 'md' \| 'lg'` | Não | Oculta em breakpoints |
| `width` | `string` | Não | Largura CSS |
| `render` | `(item: T) => ReactNode` | Não | Render customizado |
| `cellClass` | `string` | Não | Classes adicionais |

**Regras de tabela:**

- Header usa `text-sm` (12px), não `text-[10px]`
- Células usam `text-sm` (12px)
- Sort exibe ícone ChevronUp/Down na cor primary quando ativo
- Linha tem hover com `bg-bg-hover`
- Última linha não tem border-bottom
- Paginação completa com navegação, elipses, seletor de page size

---

## 10. Padrões de Formulários

### Input (`components/ui/Input.tsx`)

```tsx
<Input
  label="E-mail"
  placeholder="seu@email.com"
  icon={<Mail size={14} />}
  error={errors.email}
  helper="Nunca compartilharemos seus dados"
  loading={isChecking}
/>
```

### Button (`components/ui/Button.tsx`)

```tsx
<Button variant="primary" size="md" loading={saving} onClick={handleSave}>
  Salvar
</Button>
```

**Variantes:** `primary | secondary | ghost | danger | outline`
**Tamanhos:** `sm | md | lg`

### FormField (`components/ui/FormField.tsx`)

```tsx
<FormField label="Endereço" error={errors.endereco} required>
  <Input {...register('endereco')} />
</FormField>
```

### Regras de formulário

- Inputs usam `--radius-lg` (8px)
- Labels usam `text-xs` (11px) + `font-medium` + `text-text-muted`
- Focus ring usa `--color-border-focus` com `box-shadow: 0 0 0 2px`
- Erros aparecem abaixo com `text-xs` + `text-danger`
- Helper text aparece com `text-xs` + `text-text-muted`
- Disabled tem `opacity-50` + `cursor-not-allowed`

---

## 11. Padrões de Layout

### PageContainer (`components/layout/PageContainer.tsx`)

Wrapper principal de página. Substitui o padrão manual `flex flex-col items-center px-4`.

```tsx
<PageContainer maxWidth="xl">
  <PageSection title="Relatório">...</PageSection>
</PageContainer>
```

**maxWidth:** `sm` (max-w-lg) | `md` (max-w-3xl) | `lg` (max-w-5xl) | `xl` (max-w-6xl) | `full`

### PageSection (`components/layout/PageSection.tsx`)

Seção dentro de uma página, com título padrão.

```tsx
<PageSection
  title="Produtos"
  subtitle="Lista completa com preços e margens"
  actions={<Button size="sm">Exportar</Button>}
>
  ...
</PageSection>
```

### Grid (`components/layout/Grid.tsx`)

Grid responsivo com gap consistente.

```tsx
<Grid cols={3} gap="md">
  <KpiCard ... />
  <KpiCard ... />
</Grid>
```

**cols:** 1-6 | **gap:** `sm` (3) | `md` (4) | `lg` (5)

### Layout global

```
┌────────────────────────────────────────────────┐
│          AppHeader (sticky, z-30)               │
├──────────┬─────────────────────────────────────┤
│          │                                     │
│ Sidebar  │  Main (Outlet)                      │
│ (fixed)  │  padding: px-4 sm:px-6 py-4 sm:py-6 │
│ w-240px  │  margin-left: 240px (lg+)           │
│          │  padding-top: 64px (header height)  │
│          │                                     │
├──────────┴─────────────────────────────────────┤
│          MobileNav (fixed bottom, < lg)          │
└────────────────────────────────────────────────┘
```

---

## 12. Animações

### Tokens de duração

| Token | Valor | Uso |
|-------|-------|-----|
| `--duration-fast` | 150ms | Hover, micro-interações |
| `--duration-normal` | 200ms | Transições padrão |
| `--duration-slow` | 300ms | Animações de entrada |

### Easing

| Token | Curva | Uso |
|-------|-------|-----|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Saídas suaves padrão |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Efeito mola (entrada) |

### Utility classes

```css
.animate-fade-in-up     /* entrada: opacidade + translateY */
.animate-pulse-glow     /* glow pulsante (KPIs) */
.animate-slide-up       /* slide up (modal mobile) */
.animate-scale-in       /* scale in (modal desktop) */
.animate-page-in        /* fade + translateY sutil (troca de página) */
.animate-highlight-pulse /* destaque temporário (inventário) */
```

### Micro-interações

- `active:scale-[0.97]` em botões (feedback tátil)
- `.card-hover:hover` com translateY(-1px) em cards interativos
- `transition-all duration-fast` em todos os elementos interativos
- Entrada de página com `.animate-page-in`

---

## 13. Componentes

### Átomos (components/ui/)

| Componente | Status | Descrição |
|-----------|--------|-----------|
| `Badge` | ✅ Padronizado | Pill com variante, dot, pulse |
| `Button` | ✅ Padronizado | 5 variantes, 3 tamanhos, loading |
| `Card` | ✅ Padronizado | 6 variantes, 4 opções de padding |
| `DataTable` | ✅ Padronizado | Sort, paginação, loading/empty/error |
| `EmptyState` | ✅ Padronizado | Icon + title + description + action |
| `ErrorBanner` | ✅ Padronizado | Alert role, dismiss |
| `FormField` | ✅ Novo | Label + input + error wrapper |
| `Input` | ✅ Padronizado | forwardRef, icon, loading, error |
| `Modal` | ✅ Padronizado | 3 sizes, variant, actions, focus trap |
| `ProgressBar` | ✅ Existente | — |
| `SectionHeader` | ✅ Padronizado | Icon + title + description + action |
| `Skeleton` | ✅ Padronizado | 6 variants, pulse animation |
| `StatusPill` | ✅ Existente | — |

### Layout (components/layout/)

| Componente | Status | Descrição |
|-----------|--------|-----------|
| `AppLayout` | ✅ Tokens | Sidebar + Header + Outlet + MobileNav |
| `AppHeader` | ✅ Tokens | Sticky, useTheme, busca |
| `Grid` | ✅ Novo | Grid responsivo com gap unificado |
| `MobileNav` | ✅ Tokens | Bottom nav mobile |
| `PageContainer` | ✅ Novo | Wrapper de página com maxWidth |
| `PageSection` | ✅ Novo | Seção com título + actions |
| `Sidebar` | ✅ Tokens | Navegação, role-based, active states |

### BI (components/bi/)

| Componente | Status | Descrição |
|-----------|--------|-----------|
| `BiPageLayout` | ✅ Padronizado | Layout de páginas BI |
| `BiSubNav` | ✅ tokens | Sub-navegação horizontal com scroll |
| `BiTooltip` | ✅ tokens | Tooltip customizado para Recharts |
| `ExportButtons` | ✅ tokens | Excel/CSV export |
| `HeroKpiCard` | ✅ tokens | KPI hero com glow |
| `KpiCard` | ✅ tokens | KPI compacto com variação |
| `PeriodoForm` | ✅ tokens | Seletor de período |

---

## 14. Temas

### Estrutura

```
src/themes/
├── tokens.css              ← Defaults (executável, :root)
├── ThemeProvider.tsx        ← Context + localStorage
├── useTheme.ts              ← Hook público
├── theme-vitrine.css        ← Tema claro (verde esmeralda)
└── theme-flagship.css       ← Tema escuro (indigo slate)
```

### ThemeProvider API

```tsx
import { useTheme } from '../themes/useTheme'

function Component() {
  const { theme, setTheme, isDark, toggleTheme } = useTheme()
  // theme: 'vitrine' | 'flagship'
  // isDark: boolean (true quando flagship)
  // toggleTheme(): alterna entre claro/escuro
}
```

### Ativação

O tema é aplicado via `data-theme` no `<html>`:

```html
<html data-theme="vitrine">   <!-- Claro -->
<html data-theme="flagship">  <!-- Escuro -->
```

Tema persistido em `localStorage` via chave `vitrine_theme`.

### Diferenças entre temas

| Aspecto | Vitrine (claro) | Flagship (escuro) |
|---------|----------------|-------------------|
| Primary | `#059669` (emerald) | `#818cf8` (indigo) |
| Page bg | `#f8fafc` | `#0b1120` (deep navy) |
| Card bg | `#ffffff` | `rgba(30,41,59,0.45)` (glass) |
| Shadows | Sutis, luz do topo | Profundos, luz de baixo |
| Display font | Hanken Grotesk | Hanken Grotesk |
| Chart | Emerald/Amber | Indigo/Emerald |

---

## 15. Guia de Uso

### Para criar uma nova página

```tsx
import PageContainer from '../components/layout/PageContainer'
import PageSection from '../components/layout/PageSection'
import Card from '../components/ui/Card'

export default function MinhaPagina() {
  return (
    <PageContainer maxWidth="xl">
      <PageSection
        title="Minha Página"
        subtitle="Descrição da página"
        actions={<Button size="sm">Ação</Button>}
      >
        <Card variant="bordered" padding="md">
          Conteúdo aqui
        </Card>
      </PageSection>
    </PageContainer>
  )
}
```

### Para criar uma tabela

```tsx
import DataTable, { type Column } from '../components/ui/DataTable'
import type { MeuTipo } from '../types'

const columns: Column<MeuTipo>[] = [
  { key: 'id', label: 'ID', sortable: true, width: '80px' },
  { key: 'nome', label: 'Produto', sortable: true },
  { key: 'valor', label: 'Valor', align: 'right', render: (item) => formatCurrency(item.valor) },
]

<DataTable
  columns={columns}
  data={items}
  rowKey={(i) => i.id}
  loading={loading}
  page={page} pageSize={25} total={total}
  onPageChange={setPage}
/>
```

### Para criar um formulário

```tsx
import FormField from '../components/ui/FormField'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

<FormField label="Nome" error={errors.nome} required>
  <Input {...register('nome')} placeholder="Seu nome" />
</FormField>

<Button type="submit" loading={saving}>Salvar</Button>
```

### Checklist de consistência

- [ ] Todo valor visual usa um token CSS (nunca hardcoded)
- [ ] Toda página usa `PageContainer` + `PageSection`
- [ ] Toda tabela usa `DataTable`
- [ ] Todo formulário usa `Input` + `FormField`
- [ ] Dark mode usa `useTheme()` (nunca `localStorage` direto)
- [ ] Cores semânticas usam `text-danger`, `bg-success-light`, etc.
- [ ] Espaçamentos usam `gap-3`, `gap-4`, `gap-5` (nunca `gap-[13px]`)
- [ ] Cards usam `Card` component (nunca `div` com classes soltas)
- [ ] Botões usam `Button` component (nunca `<button>` solto)

---

> **Documentação gerada em:** 2026-05-25
> **Versão do Design System:** 1.0.0
> **Última revisão:** enterprise-ui-architect
