import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pydantic import ValidationError

from app.application.importacao import ia
from app.application.importacao.aplicacao import ResultadoAplicacao, aplicar
from app.application.importacao.extracao import Grade, extrair
from app.application.importacao.mapeamento import Mapeamento
from app.application.importacao.normalizacao import assinatura_linha
from app.application.importacao.persistencia import gravar_dataset
from app.core.config import settings
from app.domain.models.empresa import Empresa
from app.domain.models.importacao import ArquivoImportado, Dataset, TemplateImportacao

LINHAS_PROCURADAS_PARA_TEMPLATE = 40
TENTATIVAS_IA = 2
PREFIXO_TENANT_DEMO = "demo"


class ImportacaoInvalida(Exception):
    pass


@dataclass
class EstadoImportacao:
    arquivo: ArquivoImportado
    grade: Grade
    mapeamento: Mapeamento | None
    resultado: ResultadoAplicacao | None
    duplicado_de: int | None


def _diretorio(empresa_id: int) -> Path:
    caminho = Path(settings.importacao_dir) / str(empresa_id)
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def _status(resultado: ResultadoAplicacao) -> str:
    if resultado.erros:
        return "aguardando_mapeamento"
    return "divergente" if resultado.validacao.status == "divergente" else "pronto"


def _template_mais_recente(db: Session, assinatura: str) -> TemplateImportacao | None:
    return db.scalar(
        select(TemplateImportacao)
        .where(TemplateImportacao.assinatura == assinatura)
        .order_by(TemplateImportacao.versao.desc())
        .limit(1)
    )


def _procurar_template(db: Session, grade: Grade) -> tuple[TemplateImportacao, Mapeamento] | None:
    for indice, linha in enumerate(grade.linhas[:LINHAS_PROCURADAS_PARA_TEMPLATE]):
        assinatura = assinatura_linha(linha)
        if assinatura is None:
            continue
        template = _template_mais_recente(db, assinatura)
        if template is not None:
            return template, Mapeamento(**template.mapeamento, linha_cabecalho=indice)
    return None


def _ia_disponivel_para(db: Session, empresa_id: int) -> bool:
    if not ia.ia_configurada():
        return False
    empresa = db.get(Empresa, empresa_id)
    if empresa is None or empresa.slug.startswith(PREFIXO_TENANT_DEMO):
        return False
    inicio_do_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usadas = db.scalar(
        select(func.count()).select_from(ArquivoImportado).where(
            ArquivoImportado.empresa_id == empresa_id,
            ArquivoImportado.ia_usada.is_(True),
            ArquivoImportado.criado_em >= inicio_do_mes,
        )
    )
    return usadas < settings.ia_cota_mensal


def _problema(resultado: ResultadoAplicacao) -> str | None:
    if resultado.validacao.status == "divergente":
        campos = ", ".join(
            f"{d.campo} (calculado {d.calculado}, relatório {d.informado})" for d in resultado.validacao.diferencas
        )
        return f"os totais não conferem: {campos}"
    if not resultado.registros:
        return "nenhuma linha válida foi lida com esse mapeamento"
    return None


def _mapear_com_ia(grade: Grade) -> tuple[Mapeamento | None, ResultadoAplicacao | None, ia.SugestaoIa | None]:
    erro, melhor = None, (None, None, None)
    for _ in range(TENTATIVAS_IA):
        sugestao = ia.sugerir_mapeamento(grade, erro)
        try:
            mapeamento = Mapeamento(**sugestao.mapeamento)
        except ValidationError as falha:
            erro = "; ".join(e["msg"] for e in falha.errors())
            continue
        resultado = aplicar(grade, mapeamento)
        melhor = (mapeamento, resultado, sugestao)
        erro = _problema(resultado)
        if erro is None:
            break
    return melhor


def _duplicado(db: Session, arquivo: ArquivoImportado) -> int | None:
    return db.scalar(
        select(ArquivoImportado.id).where(
            ArquivoImportado.empresa_id == arquivo.empresa_id,
            ArquivoImportado.sha256 == arquivo.sha256,
            ArquivoImportado.status == "confirmado",
            ArquivoImportado.id != arquivo.id,
        ).limit(1)
    )


def _ler_grade(arquivo: ArquivoImportado) -> Grade:
    if not arquivo.caminho or not Path(arquivo.caminho).exists():
        raise ImportacaoInvalida("O arquivo original não está mais disponível. Envie de novo.")
    return extrair(Path(arquivo.caminho).read_bytes(), arquivo.nome_original)


def receber(db: Session, empresa_id: int, usuario_id: int | None, nome: str, conteudo: bytes) -> EstadoImportacao:
    grade = extrair(conteudo, nome)
    destino = _diretorio(empresa_id) / f"{uuid.uuid4().hex}.{grade.formato}"
    destino.write_bytes(conteudo)

    arquivo = ArquivoImportado(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        nome_original=nome,
        formato=grade.formato,
        tamanho=len(conteudo),
        sha256=hashlib.sha256(conteudo).hexdigest(),
        caminho=str(destino),
        status="aguardando_mapeamento",
        expira_em=datetime.now(timezone.utc) + timedelta(days=settings.importacao_retencao_dias),
    )
    mapeamento, resultado = None, None
    encontrado = _procurar_template(db, grade)
    if encontrado:
        template, mapeamento = encontrado
        resultado = aplicar(grade, mapeamento)
        arquivo.template_id = template.id
        arquivo.mapeamento = mapeamento.model_dump(mode="json")
        arquivo.status = _status(resultado)
    elif _ia_disponivel_para(db, empresa_id):
        arquivo.ia_usada = True
        try:
            mapeamento, resultado, sugestao = _mapear_com_ia(grade)
        except ia.IaIndisponivel as erro:
            arquivo.sugestao_ia = {"erro": str(erro)}
        else:
            if mapeamento is not None:
                arquivo.mapeamento = mapeamento.model_dump(mode="json")
                arquivo.status = _status(resultado)
            arquivo.sugestao_ia = {
                "confianca": sugestao.confianca if sugestao else None,
                "duvidas": sugestao.duvidas if sugestao else [],
                "modelo": settings.ia_modelo,
            }
    db.add(arquivo)
    db.commit()
    return EstadoImportacao(arquivo, grade, mapeamento, resultado, _duplicado(db, arquivo))


def estado(db: Session, arquivo: ArquivoImportado) -> EstadoImportacao:
    grade = _ler_grade(arquivo)
    mapeamento = Mapeamento(**arquivo.mapeamento) if arquivo.mapeamento else None
    resultado = aplicar(grade, mapeamento) if mapeamento else None
    return EstadoImportacao(arquivo, grade, mapeamento, resultado, _duplicado(db, arquivo))


def atualizar_mapeamento(db: Session, arquivo: ArquivoImportado, mapeamento: Mapeamento) -> EstadoImportacao:
    if arquivo.status == "confirmado":
        raise ImportacaoInvalida("Esta importação já foi confirmada.")
    grade = _ler_grade(arquivo)
    resultado = aplicar(grade, mapeamento)
    arquivo.mapeamento = mapeamento.model_dump(mode="json")
    arquivo.status = _status(resultado)
    db.commit()
    return EstadoImportacao(arquivo, grade, mapeamento, resultado, _duplicado(db, arquivo))


def _registrar_template(db: Session, grade: Grade, mapeamento: Mapeamento, empresa_id: int) -> TemplateImportacao | None:
    assinatura = assinatura_linha(grade.linhas[mapeamento.linha_cabecalho])
    if assinatura is None:
        return None
    atual = _template_mais_recente(db, assinatura)
    conteudo = mapeamento.sem_posicao()
    if atual is not None and atual.mapeamento == conteudo:
        atual.usos += 1
        return atual
    novo = TemplateImportacao(
        assinatura=assinatura,
        versao=(atual.versao + 1) if atual else 1,
        tipo=mapeamento.tipo.value,
        mapeamento=conteudo,
        criado_por_empresa_id=empresa_id,
        usos=1,
    )
    db.add(novo)
    db.flush()
    return novo


def confirmar(db: Session, arquivo: ArquivoImportado) -> Dataset:
    if arquivo.status == "confirmado":
        raise ImportacaoInvalida("Esta importação já foi confirmada.")
    if not arquivo.mapeamento:
        raise ImportacaoInvalida("Defina o mapeamento das colunas antes de confirmar.")
    grade = _ler_grade(arquivo)
    mapeamento = Mapeamento(**arquivo.mapeamento)
    resultado = aplicar(grade, mapeamento)
    if not resultado.confirmavel:
        motivo = resultado.erros[0] if resultado.erros else "Os totais não conferem com o relatório."
        raise ImportacaoInvalida(motivo)

    template = _registrar_template(db, grade, mapeamento, arquivo.empresa_id)
    dataset = gravar_dataset(
        db,
        empresa_id=arquivo.empresa_id,
        tipo=mapeamento.tipo,
        periodo=resultado.periodo,
        registros=resultado.registros,
        nome_origem=arquivo.nome_original,
        arquivo_id=arquivo.id,
        template_id=template.id if template else None,
    )
    arquivo.status = "confirmado"
    arquivo.template_id = template.id if template else arquivo.template_id
    db.commit()
    return dataset
