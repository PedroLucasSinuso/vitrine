"""Serviço principal do Intelligence — orquestra cache, detectores e IA."""
import json
import uuid
import logging
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.application.intelligence.cache import obter_cache, salvar_cache
from app.application.intelligence.cost_control import pode_solicitar, registrar_chamada
from app.schemas.intelligence_schema import IntelligenceResponse, IntelligenceJobStatus
from app.domain.models.intelligence_job import IntelligenceJob

logger = logging.getLogger(__name__)


def solicitar_analise(
    db: Session,
    source: TransactionSource,
) -> tuple[IntelligenceResponse | None, bool, str | None]:
    """Ponto de entrada principal.
    
    Retorna (response, is_cached, job_id):
    - Cache hit: (response, True, None)
    - Cache miss + pode gerar: (None, False, job_id)
    - Cache miss + bucket cheio: (fallback, False, None)
    """
    # 1. Verifica cache
    cached = obter_cache(db)
    if cached:
        response = IntelligenceResponse(**cached)
        return (response, True, None)

    # 2. Cria job (sempre — mesmo sem IA, o service executa)
    job_id = str(uuid.uuid4())
    agora = datetime.now(timezone.utc)
    job = IntelligenceJob(
        id=job_id,
        status="processing",
        criado_em=agora,
    )
    db.add(job)
    db.commit()

    return (None, False, job_id)


def _executar_analise(
    db: Session,
    source: TransactionSource,
    job_id: str,
    data_inicio: date,
    data_fim: date,
) -> None:
    """Executa a análise em background."""
    from app.application.intelligence.macro_collector import coletar_dados_macro

    try:
        # 1. Coleta dados
        dados_macro = coletar_dados_macro(db, source, data_inicio, data_fim)

        # 2. Executa detectores
        from app.application.intelligence.detectores.encalhe import EncalheDetector
        detectores = [
            ("encalhes", EncalheDetector()),
        ]
        dados_detectores = {}
        for nome, detector in detectores:
            try:
                resultado = detector.detectar(db, source, data_inicio, data_fim)
                dados_detectores[nome] = resultado
            except Exception as e:
                logger.warning("Detector %s falhou: %s", nome, e)
                dados_detectores[nome] = []

        # 3. Se bucket cheio, fallback determinístico
        from app.core.config import settings
        usar_ia = pode_solicitar(db, max_calls=settings.intelligence_max_calls_per_month)

        if usar_ia:
            response = _sintetizar_com_ia(dados_macro, dados_detectores)
            registrar_chamada(db)
        else:
            response = _sintetizar_fallback(dados_macro, dados_detectores)

        # 4. Salva cache
        salvar_cache(db, response.model_dump(), response.fonte)

        # 5. Atualiza job
        job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
        if job:
            job.status = "ready"
            job.concluido_em = datetime.now(timezone.utc)
            db.commit()

    except Exception as e:
        logger.exception("Análise Intelligence falhou: %s", e)
        job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
        if job:
            job.status = "error"
            job.erro = str(e)
            job.concluido_em = datetime.now(timezone.utc)
            db.commit()


def _sintetizar_com_ia(
    dados_macro: dict,
    dados_detectores: dict,
) -> IntelligenceResponse:
    """Tenta chain de providers. Se tudo falhar, cai pra fallback."""
    from app.application.intelligence.providers.claude import ClaudeProvider
    from app.application.intelligence.providers.openai import OpenAIProvider
    from app.application.intelligence.providers.template import TemplateProvider

    providers = [
        ("claude", ClaudeProvider),
        ("gpt4o_mini", OpenAIProvider),
    ]

    for nome, provider_cls in providers:
        try:
            provider = provider_cls()
            return provider.sintetizar(dados_macro, dados_detectores)
        except Exception as e:
            logger.warning("Provider %s falhou: %s", nome, e)

    return _sintetizar_fallback(dados_macro, dados_detectores)


def _sintetizar_fallback(
    dados_macro: dict,
    dados_detectores: dict,
) -> IntelligenceResponse:
    """Fallback determinístico usando templates Jinja2."""
    from app.application.intelligence.providers.template import TemplateProvider
    provider = TemplateProvider()
    return provider.sintetizar(dados_macro, dados_detectores)


def consultar_job(db: Session, job_id: str) -> IntelligenceJobStatus | None:
    """Retorna status do job para polling."""
    job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
    if not job:
        return None

    resultado = None
    if job.status == "ready" and job.resultado_hash:
        cached = obter_cache(db)
        if cached:
            resultado = IntelligenceResponse(**cached)

    return IntelligenceJobStatus(
        job_id=job.id,
        status=job.status,
        resultado=resultado,
        erro=job.erro,
    )
