from datetime import datetime
from pydantic import BaseModel


class CriarSessaoInput(BaseModel):
    nome: str


class EntrarSessaoInput(BaseModel):
    codigo_convite: str


class SessaoResponse(BaseModel):
    id: int
    nome: str
    status: str
    codigo_convite: str
    criado_por: str
    criado_em: datetime
    total_operadores: int
    total_itens: int


class ItemInventarioSubmit(BaseModel):
    codigo: str
    nome: str
    grupo: str
    familia: str
    quantidade: int = 1
    observacao: str = ""


class ItemInventarioResponse(BaseModel):
    codigo: str
    nome: str
    grupo: str
    familia: str
    quantidade: int
    observacao: str = ""


class AtualizarItemInput(BaseModel):
    quantidade: int
    observacao: str | None = None
