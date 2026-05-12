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


class ItemInventarioResponse(BaseModel):
    codigo: str
    nome: str
    grupo: str
    familia: str
    quantidade: int


class AtualizarItemInput(BaseModel):
    quantidade: int
