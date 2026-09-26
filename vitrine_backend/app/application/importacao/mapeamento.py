from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from vitrine_core.datasets.tipos import TipoDataset

TipoCampo = Literal["texto", "numero", "inteiro", "data", "hora", "operacao"]


@dataclass(frozen=True)
class Campo:
    rotulo: str
    tipo: TipoCampo
    obrigatorio: bool = False
    somavel: bool = False


CAMPOS: dict[TipoDataset, dict[str, Campo]] = {
    TipoDataset.VENDAS_VENDEDOR_PERIODO: {
        "vendedor": Campo("Vendedor", "texto", obrigatorio=True),
        "faturamento_bruto": Campo("Faturamento bruto", "numero", obrigatorio=True, somavel=True),
        "atendimentos": Campo("Atendimentos / tickets", "inteiro", obrigatorio=True, somavel=True),
        "pecas": Campo("Peças", "numero", somavel=True),
        "trocas": Campo("Trocas", "numero", somavel=True),
        "faturamento_liquido": Campo("Faturamento líquido", "numero", somavel=True),
    },
    TipoDataset.VENDAS_DIARIAS: {
        "data": Campo("Data", "data", obrigatorio=True),
        "faturamento_bruto": Campo("Faturamento bruto", "numero", obrigatorio=True, somavel=True),
        "atendimentos": Campo("Atendimentos / tickets", "inteiro", somavel=True),
        "pecas": Campo("Peças", "numero", somavel=True),
        "trocas": Campo("Trocas", "numero", somavel=True),
        "vendedor": Campo("Vendedor", "texto"),
    },
    TipoDataset.VENDAS_PRODUTO_PERIODO: {
        "produto": Campo("Produto", "texto", obrigatorio=True),
        "quantidade": Campo("Quantidade", "numero", obrigatorio=True, somavel=True),
        "receita": Campo("Receita", "numero", obrigatorio=True, somavel=True),
        "codigo_produto": Campo("Código do produto", "texto"),
        "grupo": Campo("Grupo / departamento", "texto"),
        "familia": Campo("Família / categoria", "texto"),
        "custo": Campo("Custo", "numero", somavel=True),
    },
    TipoDataset.CONTATOS_VENDEDOR: {
        "vendedor": Campo("Vendedor", "texto", obrigatorio=True),
        "contatos": Campo("Contatos", "inteiro", obrigatorio=True, somavel=True),
        "respostas": Campo("Respostas", "inteiro", somavel=True),
        "conversoes": Campo("Conversões", "inteiro", somavel=True),
    },
    TipoDataset.ITENS_VENDA: {
        "documento": Campo("Documento / ticket", "texto", obrigatorio=True),
        "data": Campo("Data", "data", obrigatorio=True),
        "quantidade": Campo("Quantidade", "numero", obrigatorio=True, somavel=True),
        "valor": Campo("Valor", "numero", obrigatorio=True, somavel=True),
        "hora": Campo("Hora", "hora"),
        "operacao": Campo("Operação (venda/troca)", "operacao"),
        "produto": Campo("Produto", "texto"),
        "codigo_produto": Campo("Código do produto", "texto"),
        "grupo": Campo("Grupo / departamento", "texto"),
        "familia": Campo("Família / categoria", "texto"),
        "vendedor": Campo("Vendedor", "texto"),
        "tamanho": Campo("Tamanho", "texto"),
        "cor": Campo("Cor", "texto"),
        "colecao": Campo("Coleção", "texto"),
    },
}

MARCADORES_DE_LINHA_IGNORADA = ["total", "totais", "subtotal", "soma", "geral"]

TIPOS_POR_PERIODO = {
    TipoDataset.VENDAS_VENDEDOR_PERIODO,
    TipoDataset.VENDAS_PRODUTO_PERIODO,
    TipoDataset.CONTATOS_VENDEDOR,
}


class ColunaMapeada(BaseModel):
    indice: int = Field(ge=0)
    campo: str


class PeriodoInformado(BaseModel):
    inicio: date
    fim: date

    @model_validator(mode="after")
    def _ordem(self):
        if self.fim < self.inicio:
            raise ValueError("O fim do período não pode ser antes do início.")
        return self


class Mapeamento(BaseModel):
    tipo: TipoDataset
    linha_cabecalho: int = Field(ge=0)
    colunas: list[ColunaMapeada]
    ignorar_linhas_com: list[str] = Field(default_factory=lambda: list(MARCADORES_DE_LINHA_IGNORADA))
    formato_data: Literal["dd/mm/aaaa", "aaaa-mm-dd", "mm/dd/aaaa"] = "dd/mm/aaaa"
    separador_decimal: Literal[",", "."] = ","
    periodo: PeriodoInformado | None = None

    @model_validator(mode="after")
    def _campos(self):
        campos = CAMPOS[self.tipo]
        usados = [c.campo for c in self.colunas]
        invalidos = sorted(set(usados) - set(campos))
        if invalidos:
            raise ValueError(f"Campos que não existem em {self.tipo.value}: {', '.join(invalidos)}")
        repetidos = sorted({c for c in usados if usados.count(c) > 1})
        if repetidos:
            raise ValueError(f"Campo mapeado em mais de uma coluna: {', '.join(repetidos)}")
        faltando = [nome for nome, campo in campos.items() if campo.obrigatorio and nome not in usados]
        if faltando:
            raise ValueError(f"Faltam campos obrigatórios: {', '.join(faltando)}")
        return self

    def sem_posicao(self) -> dict:
        return self.model_dump(mode="json", exclude={"linha_cabecalho", "periodo"})
