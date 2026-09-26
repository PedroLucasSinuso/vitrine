import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.adapters.demo.rng import semente

CENTAVOS = Decimal("0.01")
DIAS_UTEIS_DO_MES = 26
PESO_MES = {1: 0.9, 2: 0.75, 3: 0.85, 4: 0.95, 5: 1.25, 6: 1.15, 7: 0.95, 8: 0.9, 9: 0.95, 10: 1.0, 11: 1.25, 12: 1.6}
RAMPA_DIAS = 50


@dataclass(frozen=True)
class Vendedor:
    nome: str
    atendimentos_por_dia: float
    pecas_por_atendimento: float
    preco_por_peca: float
    taxa_troca: float
    contratado_ha_dias: int | None = None
    saiu_ha_dias: int | None = None
    ferias_no_mes_passado: int = 0
    tem_contatos: bool = True
    contatos_por_atendimento: float = 2.4


VENDEDORES = (
    Vendedor("Mariana Souza", 3.4, 2.4, 152.0, 0.03, contatos_por_atendimento=2.1),
    Vendedor("Rafael Mendes", 2.6, 3.5, 112.0, 0.04, contatos_por_atendimento=2.8),
    Vendedor("Camila Rocha", 2.8, 2.5, 148.0, 0.13, contatos_por_atendimento=3.0),
    Vendedor("Diego Alves", 2.7, 2.3, 141.0, 0.04, ferias_no_mes_passado=15, contatos_por_atendimento=2.5),
    Vendedor("Beatriz Lima", 2.6, 2.2, 138.0, 0.05, contratado_ha_dias=70, contatos_por_atendimento=3.4),
    Vendedor("Lucas Ferreira", 2.5, 2.2, 135.0, 0.05, saiu_ha_dias=38, contatos_por_atendimento=2.6),
    Vendedor("Patrícia Nunes", 2.4, 2.1, 140.0, 0.05, tem_contatos=False),
    Vendedor("Thiago Barros", 2.5, 2.3, 136.0, 0.06, contratado_ha_dias=24, tem_contatos=False),
)


@dataclass(frozen=True)
class LinhaMensal:
    vendedor: str
    atendimentos: int
    pecas: Decimal
    bruto: Decimal
    trocas: Decimal
    contatos: int | None


def _dias_ativos(v: Vendedor, inicio: date, fim: date, hoje: date) -> float:
    dias = 0.0
    dia = inicio
    ferias_ini = (hoje.replace(day=1) - timedelta(days=1)).replace(day=8)
    while dia <= fim:
        if dia.weekday() != 6:
            ativo = True
            if v.contratado_ha_dias is not None and dia < hoje - timedelta(days=v.contratado_ha_dias):
                ativo = False
            if v.saiu_ha_dias is not None and dia > hoje - timedelta(days=v.saiu_ha_dias):
                ativo = False
            if v.ferias_no_mes_passado and ferias_ini <= dia < ferias_ini + timedelta(days=v.ferias_no_mes_passado):
                ativo = False
            if ativo:
                dias += _fator_de_rampa(v, dia, hoje)
        dia += timedelta(days=1)
    return dias


def _fator_de_rampa(v: Vendedor, dia: date, hoje: date) -> float:
    if v.contratado_ha_dias is None:
        return 1.0
    dias_de_casa = (dia - (hoje - timedelta(days=v.contratado_ha_dias))).days
    return min(1.0, 0.4 + dias_de_casa / RAMPA_DIAS)


def linhas_do_periodo(inicio: date, fim: date, hoje: date) -> list[LinhaMensal]:
    rng = random.Random(semente("equipe", inicio.isoformat(), fim.isoformat()))
    fator_mes = PESO_MES[inicio.month]
    linhas = []
    for v in VENDEDORES:
        dias = _dias_ativos(v, inicio, fim, hoje)
        if dias <= 0:
            continue
        atendimentos = max(1, round(v.atendimentos_por_dia * dias * fator_mes * rng.gauss(1.0, 0.06)))
        pecas = Decimal(max(atendimentos, round(atendimentos * v.pecas_por_atendimento * rng.gauss(1.0, 0.04))))
        bruto = (pecas * Decimal(str(v.preco_por_peca * rng.gauss(1.0, 0.03)))).quantize(CENTAVOS)
        trocas = (bruto * Decimal(str(v.taxa_troca * rng.gauss(1.0, 0.15)))).quantize(CENTAVOS)
        contatos = round(atendimentos * v.contatos_por_atendimento * rng.gauss(1.0, 0.05)) if v.tem_contatos else None
        linhas.append(LinhaMensal(v.nome, atendimentos, pecas, bruto, trocas, contatos))
    return linhas
