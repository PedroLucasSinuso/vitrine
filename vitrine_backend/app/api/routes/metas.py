from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin, require_modulo, require_supervisor
from app.application.equipe import metas as servico
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario

router = APIRouter(tags=["Metas e vendedores"])
exige_metas = require_modulo("metas")
exige_equipe = require_modulo("equipe")


class MetaDTO(BaseModel):
    vendedor: str = Field(min_length=1)
    valor_meta: Decimal = Field(gt=0)
    percentual_comissao: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class MetasDaCompetenciaDTO(BaseModel):
    competencia: str
    metas: list[MetaDTO]
    vendedores_conhecidos: list[str]


class AliasDTO(BaseModel):
    nome_origem: str = Field(min_length=1)
    vendedor: str = Field(min_length=1)


def _competencia(competencia: str) -> str:
    try:
        return servico.validar_competencia(competencia)
    except servico.CompetenciaInvalida as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("/metas/{competencia}", response_model=MetasDaCompetenciaDTO)
def listar(
    competencia: str,
    empresa: Empresa = Depends(exige_metas),
    _usuario: Usuario = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    competencia = _competencia(competencia)
    aliases = servico.aliases_da_empresa(db, empresa.id)
    conhecidos = sorted(
        {aliases.get(n, n) for n in servico.vendedores_nos_dados(db, empresa.id)}, key=str.upper
    )
    return MetasDaCompetenciaDTO(
        competencia=competencia,
        metas=[
            MetaDTO(vendedor=m.vendedor, valor_meta=m.valor_meta, percentual_comissao=m.percentual_comissao)
            for m in servico.metas_da_competencia(db, empresa.id, competencia)
        ],
        vendedores_conhecidos=conhecidos,
    )


@router.put("/metas/{competencia}", response_model=MetasDaCompetenciaDTO)
def salvar(
    competencia: str,
    metas: list[MetaDTO],
    empresa: Empresa = Depends(exige_metas),
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    competencia = _competencia(competencia)
    servico.salvar_metas(db, empresa.id, competencia, [m.model_dump() for m in metas], usuario.id)
    return listar(competencia, empresa, usuario, db)


@router.post("/metas/{competencia}/copiar-de/{origem}", response_model=MetasDaCompetenciaDTO)
def copiar(
    competencia: str,
    origem: str,
    empresa: Empresa = Depends(exige_metas),
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    destino, origem = _competencia(competencia), _competencia(origem)
    servico.copiar_metas(db, empresa.id, destino, origem, usuario.id)
    return listar(destino, empresa, usuario, db)


@router.get("/vendedores", response_model=list[str])
def vendedores(
    empresa: Empresa = Depends(exige_equipe),
    _usuario: Usuario = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return servico.vendedores_nos_dados(db, empresa.id)


@router.get("/vendedores/alias", response_model=list[AliasDTO])
def listar_aliases(
    empresa: Empresa = Depends(exige_equipe),
    _usuario: Usuario = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return [AliasDTO(nome_origem=o, vendedor=v) for o, v in sorted(servico.aliases_da_empresa(db, empresa.id).items())]


@router.put("/vendedores/alias", response_model=list[AliasDTO])
def salvar_aliases(
    aliases: list[AliasDTO],
    empresa: Empresa = Depends(exige_equipe),
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    servico.salvar_aliases(db, empresa.id, {a.nome_origem: a.vendedor for a in aliases})
    return listar_aliases(empresa, usuario, db)
