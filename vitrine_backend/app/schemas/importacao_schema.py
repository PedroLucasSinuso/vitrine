from datetime import date, datetime

from pydantic import BaseModel

from app.application.importacao.mapeamento import Mapeamento

Celula = str | float | int | None


class DiferencaDTO(BaseModel):
    campo: str
    calculado: float
    informado: float


class ValidacaoDTO(BaseModel):
    status: str
    campos_conferidos: list[str]
    diferencas: list[DiferencaDTO]


class DescartadaDTO(BaseModel):
    indice: int
    motivo: str


class PeriodoDTO(BaseModel):
    inicio: date
    fim: date


class PreviaDTO(BaseModel):
    registros: list[dict]
    total_registros: int
    descartadas: list[DescartadaDTO]
    total_descartadas: int
    periodo: PeriodoDTO | None
    erros: list[str]
    validacao: ValidacaoDTO
    confirmavel: bool


class SugestaoIaDTO(BaseModel):
    confianca: str | None = None
    duvidas: list[str] = []
    erro: str | None = None


class ImportacaoDTO(BaseModel):
    id: int
    nome: str
    formato: str
    status: str
    criado_em: datetime
    template_aplicado: bool
    duplicado_de: int | None
    grade: list[list[Celula]]
    total_linhas: int
    mapeamento: Mapeamento | None
    previa: PreviaDTO | None
    sugestao_ia: SugestaoIaDTO | None = None


class ImportacaoResumoDTO(BaseModel):
    id: int
    nome: str
    formato: str
    status: str
    criado_em: datetime


class CampoDTO(BaseModel):
    campo: str
    rotulo: str
    tipo: str
    obrigatorio: bool


class DatasetDTO(BaseModel):
    id: int
    tipo: str
    inicio: date
    fim: date
    linhas: int
    nome_origem: str
    criado_em: datetime
