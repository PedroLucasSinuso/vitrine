from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_modulo, require_supervisor
from app.application.importacao import servico
from app.application.importacao.extracao import LIMITE_BYTES, ArquivoInvalido
from app.application.importacao.mapeamento import CAMPOS, Mapeamento
from app.application.importacao.persistencia import datasets_da_empresa, excluir_dataset as apagar_dataset
from app.domain.models.empresa import Empresa
from app.domain.models.importacao import ArquivoImportado, Dataset
from app.domain.models.usuario import Usuario
from app.limiter import limiter
from app.schemas.importacao_schema import (
    CampoDTO,
    DatasetDTO,
    DescartadaDTO,
    DiferencaDTO,
    ImportacaoDTO,
    ImportacaoResumoDTO,
    PeriodoDTO,
    PreviaDTO,
    ValidacaoDTO,
)

router = APIRouter(tags=["Importação"], dependencies=[Depends(require_supervisor)])
exige_modulo = require_modulo("importacao")

LINHAS_NA_GRADE = 60
REGISTROS_NA_PREVIA = 20
DESCARTADAS_NA_PREVIA = 50


def _json(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, Enum):
        return valor.value
    return valor


def _dto(estado: servico.EstadoImportacao) -> ImportacaoDTO:
    previa = None
    resultado = estado.resultado
    if resultado is not None:
        previa = PreviaDTO(
            registros=[{k: _json(v) for k, v in r.items()} for r in resultado.registros[:REGISTROS_NA_PREVIA]],
            total_registros=len(resultado.registros),
            descartadas=[DescartadaDTO(indice=d.indice, motivo=d.motivo) for d in resultado.descartadas[:DESCARTADAS_NA_PREVIA]],
            total_descartadas=len(resultado.descartadas),
            periodo=PeriodoDTO(inicio=resultado.periodo[0], fim=resultado.periodo[1]) if resultado.periodo else None,
            erros=resultado.erros,
            validacao=ValidacaoDTO(
                status=resultado.validacao.status,
                campos_conferidos=resultado.validacao.campos_conferidos,
                diferencas=[
                    DiferencaDTO(campo=d.campo, calculado=float(d.calculado), informado=float(d.informado))
                    for d in resultado.validacao.diferencas
                ],
            ),
            confirmavel=resultado.confirmavel,
        )
    arquivo = estado.arquivo
    return ImportacaoDTO(
        id=arquivo.id,
        nome=arquivo.nome_original,
        formato=arquivo.formato,
        status=arquivo.status,
        criado_em=arquivo.criado_em,
        template_aplicado=arquivo.template_id is not None,
        duplicado_de=estado.duplicado_de,
        grade=[[_json(c) for c in linha] for linha in estado.grade.linhas[:LINHAS_NA_GRADE]],
        total_linhas=len(estado.grade.linhas),
        mapeamento=estado.mapeamento,
        previa=previa,
    )


def _arquivo_da_empresa(db: Session, arquivo_id: int, empresa: Empresa) -> ArquivoImportado:
    arquivo = db.get(ArquivoImportado, arquivo_id)
    if arquivo is None or arquivo.empresa_id != empresa.id:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    return arquivo


@router.get("/importacoes/campos", response_model=dict[str, list[CampoDTO]])
def campos(_: Empresa = Depends(exige_modulo)):
    return {
        tipo.value: [
            CampoDTO(campo=nome, rotulo=c.rotulo, tipo=c.tipo, obrigatorio=c.obrigatorio)
            for nome, c in definicoes.items()
        ]
        for tipo, definicoes in CAMPOS.items()
    }


@router.post("/importacoes", response_model=ImportacaoDTO, status_code=201)
@limiter.limit("10/minute")
async def enviar(
    request: Request,
    arquivo: UploadFile = File(...),
    empresa: Empresa = Depends(exige_modulo),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conteudo = await arquivo.read(LIMITE_BYTES + 1)
    try:
        estado = servico.receber(db, empresa.id, usuario.id, arquivo.filename or "arquivo", conteudo)
    except ArquivoInvalido as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    return _dto(estado)


@router.get("/importacoes", response_model=list[ImportacaoResumoDTO])
def listar(empresa: Empresa = Depends(exige_modulo), db: Session = Depends(get_db)):
    arquivos = db.scalars(
        select(ArquivoImportado)
        .where(ArquivoImportado.empresa_id == empresa.id)
        .order_by(ArquivoImportado.criado_em.desc(), ArquivoImportado.id.desc())
        .limit(50)
    )
    return [
        ImportacaoResumoDTO(id=a.id, nome=a.nome_original, formato=a.formato, status=a.status, criado_em=a.criado_em)
        for a in arquivos
    ]


@router.get("/importacoes/{arquivo_id}", response_model=ImportacaoDTO)
def detalhar(arquivo_id: int, empresa: Empresa = Depends(exige_modulo), db: Session = Depends(get_db)):
    try:
        return _dto(servico.estado(db, _arquivo_da_empresa(db, arquivo_id, empresa)))
    except servico.ImportacaoInvalida as erro:
        raise HTTPException(status_code=410, detail=str(erro))


@router.put("/importacoes/{arquivo_id}/mapeamento", response_model=ImportacaoDTO)
def mapear(
    arquivo_id: int,
    mapeamento: Mapeamento,
    empresa: Empresa = Depends(exige_modulo),
    db: Session = Depends(get_db),
):
    arquivo = _arquivo_da_empresa(db, arquivo_id, empresa)
    try:
        return _dto(servico.atualizar_mapeamento(db, arquivo, mapeamento))
    except servico.ImportacaoInvalida as erro:
        raise HTTPException(status_code=409, detail=str(erro))


@router.post("/importacoes/{arquivo_id}/confirmar", response_model=DatasetDTO, status_code=201)
def confirmar(arquivo_id: int, empresa: Empresa = Depends(exige_modulo), db: Session = Depends(get_db)):
    arquivo = _arquivo_da_empresa(db, arquivo_id, empresa)
    try:
        dataset = servico.confirmar(db, arquivo)
    except servico.ImportacaoInvalida as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return DatasetDTO.model_validate(dataset, from_attributes=True)


@router.get("/datasets", response_model=list[DatasetDTO])
def listar_datasets(empresa: Empresa = Depends(exige_modulo), db: Session = Depends(get_db)):
    return [DatasetDTO.model_validate(d, from_attributes=True) for d in datasets_da_empresa(db, empresa.id)]


@router.delete("/datasets/{dataset_id}", status_code=204)
def excluir_dataset(dataset_id: int, empresa: Empresa = Depends(exige_modulo), db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.empresa_id != empresa.id:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")
    apagar_dataset(db, dataset)
    db.commit()
    return Response(status_code=204)
