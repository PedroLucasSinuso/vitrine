"""Serviço principal do Intelligence — orquestra cache, detectores e IA."""
import json
import uuid
import logging
from datetime import date, datetime
from app.application.intelligence._utils import utcnow
from sqlalchemy.orm import Session
from app.schemas.intelligence_schema import IntelligenceResponse, IntelligenceJobStatus
from app.domain.models.intelligence_job import IntelligenceJob
from app.application.intelligence.cache import obter_cache, salvar_cache
from app.application.intelligence.cost_control import pode_solicitar, registrar_chamada

logger = logging.getLogger(__name__)


def solicitar_analise(
    db: Session,
    data_inicio: date,
    data_fim: date,
) -> tuple[IntelligenceResponse | None, bool, str | None]:
    """Ponto de entrada principal.
    
    NOTA: TransactionSource (PostgreSQL) não é necessário nesta função.
    A conexão PostgreSQL é criada apenas em _executar_analise (background).
    
    Retorna (response, is_cached, job_id):
    - Cache hit: (response, True, None)
    - Cache miss + pode gerar: (None, False, job_id)
    - Cache miss + bucket cheio: (fallback, False, None)
    """
    # 1. Verifica cache
    cached = obter_cache(db, data_inicio, data_fim)
    if cached:
        response = IntelligenceResponse(**cached)
        return (response, True, None)

    # 2. Verifica se já existe job em processamento (lock anti-duplicação)
    job_existente = (
        db.query(IntelligenceJob)
        .filter(IntelligenceJob.status == "processing")
        .first()
    )
    if job_existente:
        logger.info("Job %s já está em processamento — reutilizando", job_existente.id)
        return (None, False, job_existente.id)

    # 3. Cria novo job
    job_id = str(uuid.uuid4())
    agora = utcnow()
    job = IntelligenceJob(
        id=job_id,
        status="processing",
        criado_em=agora,
    )
    db.add(job)
    db.commit()

    return (None, False, job_id)


def _executar_analise(
    job_id: str,
    data_inicio: date,
    data_fim: date,
) -> None:
    """Executa a análise em background.

    Cria sessão SQLAlchemy própria (não reusa session do request,
    que é fechada quando o request termina). Também cria o
    TransactionSource do PostgreSQL internamente — o request não
    precisa de PostgreSQL, apenas a background task.
    """
    from app.infrastructure.db.session import SqliteSession
    from app.application.erp_factory import create_transaction_source
    from app.application.intelligence.macro_collector import coletar_dados_macro

    db = SqliteSession()
    try:
        source = create_transaction_source(db)
        # 1. Coleta dados
        dados_macro = coletar_dados_macro(db, source, data_inicio, data_fim)

        # 2. Executa detectores
        from app.application.intelligence.detectores.encalhe import EncalheDetector
        from app.application.intelligence.detectores.taxa_troca import TaxaTrocaDetector
        from app.application.intelligence.detectores.sazonalidade import SazonalidadeDetector
        from app.application.intelligence.detectores.erosao_margem import ErosaoMargemDetector
        from app.application.intelligence.detectores.oportunidade_b import OportunidadeBDetector
        from app.application.intelligence.detectores.macro_contexto import MacroContextoDetector
        detectores = [
            ("encalhes", EncalheDetector()),
            ("taxa_troca", TaxaTrocaDetector()),
            ("sazonalidade", SazonalidadeDetector()),
            ("erosao_margem", ErosaoMargemDetector()),
            ("oportunidade_b", OportunidadeBDetector()),
            ("macro_contexto", MacroContextoDetector()),
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
        salvar_cache(db, response.model_dump(), response.fonte, data_inicio, data_fim)

        # 5. Atualiza job
        job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
        if job:
            job.status = "ready"
            job.concluido_em = utcnow()
            db.commit()

    except Exception as e:
        logger.exception("Análise Intelligence falhou: %s", e)
        try:
            job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
            if job:
                job.status = "error"
                job.erro = str(e)
                job.concluido_em = utcnow()
                db.commit()
        except Exception:
            logger.exception("Falha ao atualizar status do job")
    finally:
        db.close()


def _sintetizar_com_ia(
    dados_macro: dict,
    dados_detectores: dict,
) -> IntelligenceResponse:
    """Tenta chain de providers (com imports lazy para fallback silencioso)."""
    providers: list[tuple[str, type]] = []
    for nome, mod_path, cls_name in [
        ("claude", "app.application.intelligence.providers.claude", "ClaudeProvider"),
        ("gpt4o_mini", "app.application.intelligence.providers.openai", "OpenAIProvider"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            provider_cls = getattr(mod, cls_name)
            providers.append((nome, provider_cls))
        except Exception as e:
            logger.warning("Provider %s não disponível: %s", nome, e)

    for nome, provider_cls in providers:
        try:
            provider = provider_cls()
            return provider.sintetizar(dados_macro, dados_detectores)
        except Exception as e:
            logger.warning("Provider %s falhou na execução: %s", nome, e)

    return _sintetizar_fallback(dados_macro, dados_detectores)


def _sintetizar_fallback(
    dados_macro: dict,
    dados_detectores: dict,
) -> IntelligenceResponse:
    """Fallback determinístico usando templates Jinja2."""
    from app.application.intelligence.providers.template import TemplateProvider
    provider = TemplateProvider()
    return provider.sintetizar(dados_macro, dados_detectores)


def consultar_job(db: Session, job_id: str, data_inicio: date | None = None, data_fim: date | None = None) -> IntelligenceJobStatus | None:
    """Retorna status do job para polling."""
    job = db.query(IntelligenceJob).filter(IntelligenceJob.id == job_id).first()
    if not job:
        return None

    resultado = None
    if job.status == "ready":
        if data_inicio and data_fim:
            cached = obter_cache(db, data_inicio, data_fim)
        else:
            cached = obter_cache(db, date(2026, 1, 1), date(2026, 12, 31))  # fallback amplo
        if cached:
            resultado = IntelligenceResponse(**cached)

    return IntelligenceJobStatus(
        job_id=job.id,
        status=job.status,
        resultado=resultado,
        erro=job.erro,
    )
