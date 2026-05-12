from pydantic import BaseModel

# Schema: define o formato/contrato de dados para validacao e resposta da API.
class ProdutoPublicResponse(BaseModel):
    codigo_chamada: str
    grupo: str
    familia: str
    nome: str
    preco_venda: float
    estoque: float
    codigo_buscado: str | None = None

    model_config = {"from_attributes": True}


class ProdutoResponse(ProdutoPublicResponse):
    preco_custo: float
    markup: float
    margem: float

class ObservacaoNaoEncontrado(BaseModel):
    codigo: str
    observacao: str