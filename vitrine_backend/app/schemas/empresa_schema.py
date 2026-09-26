from pydantic import BaseModel

from app.domain.enums import ModoOperacao, Segmento


class PerfilEmpresaResponse(BaseModel):
    nome: str
    segmento: Segmento
    modo: ModoOperacao
    modulos: list[str]
    rotulos: dict[str, str]
