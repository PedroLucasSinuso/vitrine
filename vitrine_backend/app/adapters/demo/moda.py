import random
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal

from app.adapters.demo.rng import semente
from vitrine_core.datasets.tipos import Operacao

CENTAVOS = Decimal("0.01")
ATENDIMENTOS_DIA_BASE = 30
TAXA_DOIS_VENDEDORES = 0.08
TAXA_SEM_VENDEDOR = 0.03

PESO_DIA_SEMANA = (0.75, 0.8, 0.85, 0.95, 1.15, 1.6, 1.05)
PESO_MES = {1: 0.9, 2: 0.75, 3: 0.85, 4: 0.95, 5: 1.25, 6: 1.15, 7: 0.95, 8: 0.9, 9: 0.95, 10: 1.0, 11: 1.2, 12: 1.6}
HORAS = list(range(10, 22))
PESO_HORA = [0.4, 0.6, 0.8, 0.8, 0.7, 0.8, 1.0, 1.3, 1.5, 1.5, 1.2, 0.7]


@dataclass(frozen=True)
class PerfilVendedor:
    nome: str
    peso: float
    fator_ticket: float
    pecas_por_atendimento: float
    taxa_troca: float
    contratado_ha_dias: int | None = None
    ferias_no_mes_passado: bool = False


VENDEDORES = (
    PerfilVendedor("Mariana Souza", 1.35, 1.30, 2.3, 0.03),
    PerfilVendedor("Rafael Mendes", 1.05, 0.80, 3.4, 0.04),
    PerfilVendedor("Beatriz Lima", 0.90, 1.00, 2.2, 0.04, contratado_ha_dias=60),
    PerfilVendedor("Diego Alves", 1.00, 1.00, 2.4, 0.04, ferias_no_mes_passado=True),
    PerfilVendedor("Camila Rocha", 1.00, 1.05, 2.3, 0.13),
    PerfilVendedor("Lucas Ferreira", 0.95, 0.95, 2.2, 0.05),
    PerfilVendedor("Patrícia Nunes", 0.95, 1.00, 2.1, 0.05),
)

CATALOGO: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("FEMININO", "VESTIDOS"): [("Vestido Midi Linho", "259.90"), ("Vestido Curto Estampado", "189.90"), ("Vestido Longo Malha", "229.90")],
    ("FEMININO", "BLUSAS"): [("Blusa Viscose", "119.90"), ("Camisa Seda Toque", "159.90"), ("Regata Canelada", "69.90")],
    ("FEMININO", "CALCAS"): [("Calça Wide Leg", "199.90"), ("Calça Jeans Reta", "219.90"), ("Saia Midi Plissada", "169.90")],
    ("MASCULINO", "CAMISAS"): [("Camisa Oxford", "179.90"), ("Camisa Linho", "199.90")],
    ("MASCULINO", "CAMISETAS"): [("Camiseta Algodão Pima", "89.90"), ("Polo Piquet", "129.90")],
    ("MASCULINO", "BERMUDAS"): [("Bermuda Sarja", "139.90"), ("Calça Chino", "189.90")],
    ("CALCADOS", "TENIS"): [("Tênis Couro Branco", "329.90"), ("Tênis Casual Lona", "219.90")],
    ("CALCADOS", "SANDALIAS"): [("Sandália Rasteira", "149.90"), ("Sandália Salto Bloco", "239.90")],
    ("ACESSORIOS", "BOLSAS"): [("Bolsa Tiracolo", "249.90"), ("Bolsa Shopper", "279.90")],
    ("ACESSORIOS", "CINTOS"): [("Cinto Couro", "99.90"), ("Lenço Estampado", "79.90")],
}
PESO_DEPARTAMENTO = {"FEMININO": 0.5, "MASCULINO": 0.25, "CALCADOS": 0.15, "ACESSORIOS": 0.10}
TAMANHOS = {
    "FEMININO": ["PP", "P", "M", "G", "GG"],
    "MASCULINO": ["P", "M", "G", "GG"],
    "CALCADOS": [str(n) for n in range(34, 44)],
    "ACESSORIOS": ["U"],
}
CORES = ["Preto", "Branco", "Azul Marinho", "Bege", "Verde Oliva", "Terracota", "Rosa"]

_MODELOS = [
    (departamento, categoria, nome, Decimal(preco))
    for (departamento, categoria), modelos in CATALOGO.items()
    for nome, preco in modelos
]
_PESO_MODELOS = [PESO_DEPARTAMENTO[d] / sum(1 for m in _MODELOS if m[0] == d) for d, *_ in _MODELOS]


def _rng(*partes) -> random.Random:
    return random.Random(semente("moda", *partes))


def _mes_passado(hoje: date) -> tuple[date, date]:
    fim = hoje.replace(day=1) - timedelta(days=1)
    return fim.replace(day=1), fim


def _ativos(dia: date, hoje: date) -> list[tuple[PerfilVendedor, float]]:
    inicio_ferias, fim_ferias = _mes_passado(hoje)
    inicio_ferias = inicio_ferias + timedelta(days=7)
    ativos = []
    for perfil in VENDEDORES:
        peso = perfil.peso
        if perfil.contratado_ha_dias is not None:
            dias_de_casa = (dia - (hoje - timedelta(days=perfil.contratado_ha_dias))).days
            if dias_de_casa < 0:
                continue
            peso *= min(1.0, 0.35 + dias_de_casa / 50)
        if perfil.ferias_no_mes_passado and inicio_ferias <= dia < inicio_ferias + timedelta(days=15):
            continue
        ativos.append((perfil, peso))
    return ativos


def _item(rng: random.Random, documento: str, dia: date, hora: time, vendedor: str | None, operacao=Operacao.VENDA) -> dict:
    departamento, categoria, nome, preco = rng.choices(_MODELOS, weights=_PESO_MODELOS, k=1)[0]
    quantidade = rng.choices([1, 2], weights=[0.9, 0.1], k=1)[0]
    desconto = Decimal(str(rng.choice([1, 1, 1, 0.9, 0.95])))
    return {
        "documento": documento,
        "data": dia,
        "hora": hora,
        "operacao": operacao,
        "quantidade": Decimal(quantidade),
        "valor": (preco * quantidade * desconto).quantize(CENTAVOS),
        "produto": nome,
        "codigo_produto": f"{abs(hash_estavel(nome)) % 100000:05d}",
        "grupo": departamento,
        "familia": categoria,
        "vendedor": vendedor,
        "tamanho": rng.choice(TAMANHOS[departamento]),
        "cor": rng.choice(CORES),
        "colecao": "Verão 26" if dia.month in (9, 10, 11, 12, 1, 2) else "Inverno 26",
    }


def hash_estavel(texto: str) -> int:
    return semente("produto", texto)


def itens_do_dia(dia: date, hoje: date | None = None) -> list[dict]:
    hoje = hoje or date.today()
    rng = _rng("dia", dia.isoformat())
    ativos = _ativos(dia, hoje)
    if not ativos:
        return []
    fator = PESO_DIA_SEMANA[dia.weekday()] * PESO_MES[dia.month]
    atendimentos = max(0, round(ATENDIMENTOS_DIA_BASE * fator * rng.gauss(1.0, 0.1)))
    perfis = [p for p, _ in ativos]
    pesos = [w for _, w in ativos]
    itens: list[dict] = []
    for n in range(atendimentos):
        documento = f"M{dia:%Y%m%d}{n:04d}"
        hora = time(rng.choices(HORAS, weights=PESO_HORA, k=1)[0], rng.randrange(60))
        perfil = rng.choices(perfis, weights=pesos, k=1)[0]
        vendedores = [perfil]
        if rng.random() < TAXA_DOIS_VENDEDORES and len(perfis) > 1:
            outro = rng.choices(perfis, weights=pesos, k=1)[0]
            if outro != perfil:
                vendedores.append(outro)
        pecas = max(1, round(rng.gauss(perfil.pecas_por_atendimento, 0.8)))
        for i in range(pecas):
            vendedor = vendedores[i % len(vendedores)]
            nome = None if rng.random() < TAXA_SEM_VENDEDOR else vendedor.nome
            item = _item(rng, documento, dia, hora, nome)
            item["valor"] = (item["valor"] * Decimal(str(vendedor.fator_ticket))).quantize(CENTAVOS)
            itens.append(item)
    trocas = []
    for n, perfil in enumerate(perfis):
        vendas_do_vendedor = sum(1 for i in itens if i["vendedor"] == perfil.nome)
        for m in range(sum(1 for _ in range(vendas_do_vendedor) if rng.random() < perfil.taxa_troca)):
            troca = _item(rng, f"T{dia:%Y%m%d}{n:02d}{m:02d}", dia, time(rng.choice(HORAS), 0), perfil.nome, Operacao.TROCA)
            trocas.append(troca)
    return itens + trocas


def meses_da_demo(hoje: date, meses: int = 6) -> list[tuple[date, date]]:
    periodos = []
    inicio = hoje.replace(day=1)
    for _ in range(meses):
        fim = min(hoje, (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1))
        periodos.append((inicio, fim))
        inicio = (inicio - timedelta(days=1)).replace(day=1)
    return list(reversed(periodos))


def itens_do_periodo(inicio: date, fim: date, hoje: date | None = None) -> list[dict]:
    itens = []
    dia = inicio
    while dia <= fim:
        itens.extend(itens_do_dia(dia, hoje))
        dia += timedelta(days=1)
    return itens
