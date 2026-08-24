"""Constantes calibráveis do adapter de demonstração.

Todo número que define "quanto" ou "quão realista" mora aqui, para caber
num ajuste só. Ver ``generator.py`` para como cada um é usado.
"""

# Semente base. Trocar este número gera um "mercado" inteiramente diferente
# (outras vendas, outros picos) sem mudar uma linha de lógica.
SEED_BASE = 20260824

# Quantos dias para trás existem dados. Precisa cobrir o maior período das
# rotas de BI (180 dias) MAIS o deslocamento ano-a-ano (365) com folga para
# o ajuste de dia da semana e para o relatório do mesmo mês do ano anterior.
JANELA_DIAS = 800

# Tickets (documentos de venda) num dia mediano, antes dos pesos de dia da
# semana, mês, feriado e tendência. Calibrado para caber no orçamento de
# tempo do maior período das rotas (180 dias) somado ao comparativo
# ano-a-ano, que dobra o volume carregado num único request.
TICKETS_DIA_BASE = 36

# Itens por ticket: distribuição geométrica truncada neste intervalo.
ITENS_TICKET_MIN = 1
ITENS_TICKET_MAX = 12
ITENS_TICKET_MODA = 4

# Fração do faturamento do dia que volta como troca/devolução.
TAXA_TROCA = 0.015

# Fração dos tickets que sai cancelada (exercita o filtro dos domínios).
TAXA_CANCELAMENTO = 0.008

# Documentos de perda e de consumo interno por dia.
PERDAS_DOCS_DIA = (1, 3)
CONSUMO_DOCS_DIA = (1, 2)

# Fração das perdas/consumos SEM documento comprobatório. Os domínios de
# Perdas e Consumo filtram esses fora — existe para provar que o filtro
# funciona, não para sumir com a tela.
TAXA_SEM_DOCUMENTO = 0.10

# Dias mantidos no cache do TransactionSource. Cada dia custa ~300 itens;
# 200 dias ficam na casa de dezenas de MB por processo.
MAXSIZE_CACHE_DIAS = 200
