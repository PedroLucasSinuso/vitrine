"""Curvas de sazonalidade — funções puras, sem aleatoriedade.

São elas que dão forma aos gráficos: sem isso a demo vira ruído branco
uniforme, que é visualmente pior (e menos crível) que dados de verdade.
"""

from datetime import date

# Segunda a domingo. Supermercado concentra no fim de semana, com pico no
# sábado; segunda e terça são os dias fracos.
PESO_WEEKDAY = (0.88, 0.85, 0.90, 1.00, 1.25, 1.45, 0.78)

# Janela de funcionamento da loja.
HORA_ABERTURA = 7
HORA_FECHAMENTO = 21

# Movimento por hora: dois picos (almoço e fim de tarde) com vale no meio.
_PESO_HORA = {
    7: 0.35, 8: 0.60, 9: 0.85, 10: 1.05, 11: 1.35, 12: 1.30, 13: 1.00,
    14: 0.75, 15: 0.70, 16: 0.85, 17: 1.20, 18: 1.45, 19: 1.30, 20: 0.85,
    21: 0.40,
}

# Dezembro puxa o ano; começo do ano é fraco.
PESO_MES = (0.85, 0.82, 0.95, 0.98, 1.00, 0.97, 1.02, 1.00, 0.98, 1.03, 1.08, 1.35)

# Feriados fixos: multiplicador do movimento. 0.0 = loja fechada.
# Véspera enche, o próprio feriado fecha.
FERIADOS = {
    (1, 1): 0.0,    # Ano-novo
    (4, 21): 0.55,  # Tiradentes
    (5, 1): 0.60,   # Dia do Trabalho
    (9, 7): 0.65,   # Independência
    (10, 12): 0.70, # Nossa Senhora Aparecida
    (11, 2): 0.60,  # Finados
    (11, 15): 0.70, # Proclamação da República
    (12, 24): 1.90, # Véspera de Natal
    (12, 25): 0.0,  # Natal
    (12, 31): 1.55, # Véspera de Ano-novo
}

# Crescimento anual do faturamento — faz a comparação ano-a-ano mostrar
# evolução em vez de ruído.
CRESCIMENTO_ANUAL = 0.09


def peso_weekday(dia: date) -> float:
    return PESO_WEEKDAY[dia.weekday()]


def peso_mes(dia: date) -> float:
    return PESO_MES[dia.month - 1]


def peso_feriado(dia: date) -> float:
    return FERIADOS.get((dia.month, dia.day), 1.0)


def horas_e_pesos() -> tuple[list[int], list[float]]:
    """Horas de funcionamento e o peso de movimento de cada uma."""
    horas = list(range(HORA_ABERTURA, HORA_FECHAMENTO + 1))
    return horas, [_PESO_HORA[h] for h in horas]


# Âncora do crescimento. Precisa ser uma data FIXA, nunca relativa a hoje:
# com referência móvel, o faturamento de um dia passado mudaria a cada
# virada de data, e o mesmo dia consultado duas vezes daria números
# diferentes.
ANCORA = date(2020, 1, 1)


def tendencia(dia: date) -> float:
    """Crescimento acumulado do movimento até ``dia``.

    Dias recentes valem mais que dias antigos — é o que produz variação
    positiva na comparação ano-a-ano.
    """
    anos = (dia - ANCORA).days / 365.0
    return (1 + CRESCIMENTO_ANUAL) ** anos


def fator_do_dia(dia: date) -> float:
    """Multiplicador total de movimento do dia (0.0 = loja fechada)."""
    return peso_weekday(dia) * peso_mes(dia) * peso_feriado(dia) * tendencia(dia)
