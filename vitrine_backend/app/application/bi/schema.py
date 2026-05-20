from dataclasses import dataclass
from enum import Enum

class Dimensao(Enum):
    PRODUTO = "produto"
    GRUPO = "grupo"
    FAMILIA = "familia"

    def colunas(self) -> list[str]:
        if self == Dimensao.PRODUTO:
            return ["grupo", "familia", "produto"]
        return [self.value]

class Metrica(Enum):
    RECEITA = "receita_produto"
    QUANTIDADE = "qtd_item"

@dataclass(frozen=True)
class Colunas:
    id_item: str = "id_item"
    id_documento: str = "iddocumento"
    id_nfe: str = "id_nfe"
    emissao: str = "emissao"
    hora: str = "hora"
    operacao: str = "operacao"
    id_operacao: str = "id_operacao"
    devolucao: str = "tipo_devolucao"
    cancelado: str = "cancelado"
    total_documento: str = "total_documento"
    grupo: str = "grupo"
    familia: str = "familia"
    codigo: str = "codigo"
    produto: str = "produto"
    custo: str = "custo"
    venda: str = "venda"
    qtd_item: str = "qtd_item"
    receita: str = "receita_produto"
    valor_unitario: str = "valor_unitario"

COLUNAS = Colunas()

