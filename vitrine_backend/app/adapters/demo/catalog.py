"""Catálogo de produtos da demonstração.

Nomes são genéricos de propósito (nada de marcas reais): a demo é pública
e não deve parecer o catálogo de um cliente.

O ``peso_popularidade`` segue uma lei de potência — poucos produtos
concentram a maior parte da receita. É isso que faz a curva ABC ter as três
classes com massa em cada uma, em vez de uma reta.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.adapters.demo.ean import gerar_ean13
from app.adapters.demo.rng import semente

# Expoente da lei de potência da popularidade. Quanto maior, mais
# concentrada a receita nos campeões (curva ABC mais acentuada).
_EXPOENTE_POPULARIDADE = 0.85

# Margem bruta típica por grupo — o custo sai do preço por aqui.
_MARGEM_POR_GRUPO = {
    "HORTIFRUTI": 0.38,
    "ACOUGUE": 0.24,
    "PADARIA": 0.45,
    "LATICINIOS": 0.26,
    "MERCEARIA": 0.22,
    "BEBIDAS": 0.28,
    "CONGELADOS": 0.30,
    "LIMPEZA": 0.32,
    "HIGIENE": 0.35,
    "PET": 0.34,
    "BAZAR": 0.42,
}

# (grupo, familia) -> [(nome, preco_venda, vendido_por_peso), ...]
_PRODUTOS: dict[tuple[str, str], list[tuple[str, str, bool]]] = {
    ("HORTIFRUTI", "FRUTAS"): [
        ("Banana Prata kg", "6.49", True), ("Maçã Gala kg", "9.90", True),
        ("Mamão Formosa kg", "7.99", True), ("Laranja Pera kg", "4.99", True),
        ("Uva Itália kg", "14.90", True), ("Melancia kg", "3.49", True),
        ("Abacaxi unidade", "8.90", False), ("Limão Tahiti kg", "5.99", True),
    ],
    ("HORTIFRUTI", "VERDURAS"): [
        ("Alface Crespa unidade", "3.99", False), ("Tomate kg", "8.90", True),
        ("Cebola kg", "5.49", True), ("Batata kg", "6.99", True),
        ("Cenoura kg", "5.90", True), ("Couve maço", "3.49", False),
        ("Pimentão Verde kg", "9.90", True), ("Abobrinha kg", "6.49", True),
    ],
    ("ACOUGUE", "BOVINOS"): [
        ("Patinho kg", "42.90", True), ("Alcatra kg", "49.90", True),
        ("Coxão Mole kg", "44.90", True), ("Acém kg", "32.90", True),
        ("Costela Bovina kg", "28.90", True), ("Carne Moída kg", "34.90", True),
        ("Picanha kg", "79.90", True),
    ],
    ("ACOUGUE", "AVES"): [
        ("Peito de Frango kg", "18.90", True), ("Coxa e Sobrecoxa kg", "12.90", True),
        ("Frango Inteiro kg", "13.90", True), ("Filé de Frango kg", "24.90", True),
    ],
    ("ACOUGUE", "SUINOS"): [
        ("Linguiça Toscana kg", "22.90", True), ("Costelinha Suína kg", "26.90", True),
        ("Bisteca Suína kg", "24.90", True), ("Bacon em Cubos 500g", "19.90", False),
    ],
    ("PADARIA", "PAES"): [
        ("Pão Francês kg", "16.90", True), ("Pão de Forma 500g", "8.99", False),
        ("Pão de Queijo kg", "32.90", True), ("Broa de Milho unidade", "7.90", False),
        ("Pão Integral 400g", "10.90", False),
    ],
    ("PADARIA", "CONFEITARIA"): [
        ("Bolo de Cenoura fatia", "6.90", False), ("Sonho unidade", "5.50", False),
        ("Torta de Frango fatia", "12.90", False), ("Rosca Doce unidade", "8.90", False),
    ],
    ("LATICINIOS", "LEITES"): [
        ("Leite Integral 1L", "5.29", False), ("Leite Desnatado 1L", "5.49", False),
        ("Leite Condensado 395g", "7.90", False), ("Creme de Leite 200g", "3.99", False),
    ],
    ("LATICINIOS", "QUEIJOS"): [
        ("Queijo Mussarela kg", "44.90", True), ("Queijo Prato kg", "46.90", True),
        ("Requeijão 200g", "8.90", False), ("Queijo Parmesão 100g", "12.90", False),
    ],
    ("LATICINIOS", "IOGURTES"): [
        ("Iogurte Natural 170g", "3.49", False), ("Iogurte Morango 900g", "12.90", False),
        ("Bebida Láctea 1L", "8.49", False),
    ],
    ("MERCEARIA", "GRAOS"): [
        ("Arroz Branco 5kg", "27.90", False), ("Arroz Branco 1kg", "6.49", False),
        ("Feijão Carioca 1kg", "8.99", False), ("Feijão Preto 1kg", "9.49", False),
        ("Lentilha 500g", "11.90", False), ("Açúcar Refinado 1kg", "4.99", False),
    ],
    ("MERCEARIA", "MASSAS"): [
        ("Macarrão Espaguete 500g", "4.99", False), ("Macarrão Parafuso 500g", "4.99", False),
        ("Molho de Tomate 340g", "3.49", False), ("Macarrão Instantâneo 80g", "2.49", False),
    ],
    ("MERCEARIA", "OLEOS"): [
        ("Óleo de Soja 900ml", "7.49", False), ("Azeite Extra Virgem 500ml", "34.90", False),
        ("Vinagre de Álcool 750ml", "4.29", False),
    ],
    ("MERCEARIA", "MATINAIS"): [
        ("Café Torrado 500g", "18.90", False), ("Achocolatado em Pó 400g", "9.90", False),
        ("Biscoito Recheado 130g", "3.29", False), ("Cereal Matinal 300g", "14.90", False),
        ("Geleia de Morango 230g", "12.90", False),
    ],
    ("BEBIDAS", "REFRIGERANTES"): [
        ("Refrigerante Cola 2L", "9.99", False), ("Refrigerante Guaraná 2L", "8.49", False),
        ("Refrigerante Laranja 2L", "7.99", False), ("Refrigerante Cola Lata 350ml", "4.49", False),
        ("Água Tônica Lata 350ml", "4.99", False),
    ],
    ("BEBIDAS", "SUCOS E AGUAS"): [
        ("Suco de Uva 1L", "12.90", False), ("Suco de Laranja 1L", "9.90", False),
        ("Água Mineral 1,5L", "3.49", False), ("Água com Gás 500ml", "2.99", False),
        ("Néctar de Pêssego 1L", "8.49", False),
    ],
    ("BEBIDAS", "ALCOOLICAS"): [
        ("Cerveja Pilsen Lata 350ml", "4.29", False), ("Cerveja Puro Malte 600ml", "9.90", False),
        ("Vinho Tinto Seco 750ml", "39.90", False), ("Vodka 1L", "44.90", False),
    ],
    ("CONGELADOS", "PRATOS PRONTOS"): [
        ("Lasanha Congelada 600g", "24.90", False), ("Pizza Congelada 460g", "19.90", False),
        ("Nuggets 300g", "14.90", False), ("Hambúrguer Bovino 672g", "27.90", False),
    ],
    ("CONGELADOS", "SORVETES"): [
        ("Sorvete Creme 2L", "22.90", False), ("Picolé Fruta unidade", "3.99", False),
        ("Açaí Polpa 1kg", "29.90", False),
    ],
    ("LIMPEZA", "ROUPAS"): [
        ("Sabão em Pó 1kg", "16.90", False), ("Amaciante 2L", "14.90", False),
        ("Sabão em Barra 200g", "2.99", False), ("Água Sanitária 2L", "7.49", False),
    ],
    ("LIMPEZA", "CASA"): [
        ("Detergente Neutro 500ml", "2.79", False), ("Desinfetante 2L", "9.90", False),
        ("Limpador Multiuso 500ml", "6.49", False), ("Esponja Dupla Face unidade", "2.29", False),
        ("Saco de Lixo 50L 10un", "8.90", False),
    ],
    ("HIGIENE", "BANHO"): [
        ("Sabonete 90g", "2.99", False), ("Shampoo 350ml", "18.90", False),
        ("Condicionador 350ml", "19.90", False), ("Creme Dental 90g", "6.49", False),
        ("Desodorante Aerosol 150ml", "16.90", False),
    ],
    ("HIGIENE", "PAPEL"): [
        ("Papel Higiênico 12 rolos", "24.90", False), ("Papel Toalha 2 rolos", "9.90", False),
        ("Lenço de Papel 50un", "4.99", False), ("Fralda Descartável M 30un", "44.90", False),
    ],
    ("PET", "ALIMENTOS"): [
        ("Ração Cães Adultos 10kg", "89.90", False), ("Ração Gatos 3kg", "49.90", False),
        ("Petisco Cães 65g", "9.90", False), ("Areia Sanitária 4kg", "19.90", False),
    ],
    ("BAZAR", "UTILIDADES"): [
        ("Pilha AA 4un", "19.90", False), ("Lâmpada LED 9W", "12.90", False),
        ("Copo de Vidro 300ml", "6.90", False), ("Pano de Prato unidade", "8.90", False),
        ("Vela unidade", "3.49", False),
    ],
}


@dataclass(frozen=True)
class SkuDemo:
    """Um produto do catálogo de demonstração."""

    internal_code: str
    nome: str
    grupo: str
    familia: str
    preco_base: Decimal
    custo_base: Decimal
    peso_popularidade: float
    por_peso: bool
    barcodes: tuple[str, ...]


def _montar_catalogo() -> tuple[SkuDemo, ...]:
    """Constrói o catálogo uma vez, no import.

    A popularidade é atribuída embaralhando o catálogo com semente fixa e
    aplicando a lei de potência sobre a posição sorteada — assim os
    campeões de venda ficam espalhados entre grupos, em vez de todos caírem
    na primeira categoria listada.
    """
    import random

    brutos: list[tuple[str, str, str, str, bool]] = []
    for (grupo, familia), produtos in _PRODUTOS.items():
        for nome, preco, por_peso in produtos:
            brutos.append((nome, preco, grupo, familia, por_peso))

    posicoes = list(range(len(brutos)))
    random.Random(semente("popularidade")).shuffle(posicoes)

    catalogo: list[SkuDemo] = []
    for indice, (nome, preco, grupo, familia, por_peso) in enumerate(brutos):
        preco_venda = Decimal(preco)
        margem = Decimal(str(_MARGEM_POR_GRUPO[grupo]))
        custo = (preco_venda * (Decimal("1") - margem)).quantize(Decimal("0.01"))
        catalogo.append(
            SkuDemo(
                # PLU de 6 dígitos: é a forma já normalizada por
                # Codigo.normalizar(), que é o que as rotas comparam.
                internal_code=f"{indice + 1:06d}",
                nome=nome,
                grupo=grupo,
                familia=familia,
                preco_base=preco_venda,
                custo_base=custo,
                peso_popularidade=1 / (posicoes[indice] + 1) ** _EXPOENTE_POPULARIDADE,
                por_peso=por_peso,
                barcodes=(gerar_ean13(indice + 1),),
            )
        )
    return tuple(catalogo)


CATALOGO: tuple[SkuDemo, ...] = _montar_catalogo()
PESOS_POPULARIDADE: tuple[float, ...] = tuple(s.peso_popularidade for s in CATALOGO)
