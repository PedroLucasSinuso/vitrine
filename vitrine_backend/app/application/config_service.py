"""Central de configurações operacionais.

Serviço unificado para ler e escrever configurações do sistema no SQLite.
Fallback automático para .env (Settings) quando a chave não existe no banco,
permitindo migração transparente.
"""

import logging
import re
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.domain.models.configuracao import Configuracao
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache leve com TTL (segundos) — evita ler do banco a cada chamada,
# mas sem os problemas de invalidação manual entre workers.
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 30

CHAVES_COPIADAS_DO_ENV: set[str] = set()

# ── Whitelist de chaves editáveis via API ──────────────────────────────────
# Qualquer chave não listada aqui será rejeitada por set_many().
# Mantenha esta lista sincronizada com as abas da UI de Admin > Configurações.
CHAVES_EDITAVEIS: set[str] = {
    # Aba Geral
    "nome_estabelecimento",
    "logo_url",
    # Aba ERP
    "erp_postgres_url",
    "cache_refresh_interval",
    # Aba WhatsApp
    "twilio_account_sid",
    "twilio_auth_token",
    "twilio_from_number",
    # Aba E-mail
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "email_from",
    # Aba Intelligence / Agendamentos
    "report_day",
    "report_time",
    "report_email_day",
    "report_email_time",
    "etl_interval_minutes",
    "relatorio_dias_retroativos",
    # Aba Sistema
    "anthropic_api_key",
    "openai_api_key",
}

# Chaves sensíveis — nunca retornar valor real no GET.
# Usa heurística por nome + lista explícita para segurança extra.
_CHAVES_SENSIVEIS_POR_PADRAO: set[str] = {
    "twilio_auth_token", "twilio_account_sid",
    "smtp_password", "anthropic_api_key", "openai_api_key",
    "erp_postgres_url",
}

_PADROES_SENSIVEIS = re.compile(
    r"(password|secret|token|key|api_key|auth_token|sid)", re.IGNORECASE
)


def is_sensitive(chave: str) -> bool:
    """Retorna True se a chave é considerada sensível (não expor valor real)."""
    if chave in _CHAVES_SENSIVEIS_POR_PADRAO:
        return True
    if _PADROES_SENSIVEIS.search(chave):
        return True
    return False


# Mapeamento de chaves do banco para atributos do Settings (.env)
_ENV_FALLBACK_MAP: dict[str, str] = {
    "erp_postgres_url": "postgres_url",
    "twilio_account_sid": "twilio_account_sid",
    "twilio_auth_token": "twilio_auth_token",
    "twilio_from_number": "twilio_from_number",
    "smtp_host": "smtp_host",
    "smtp_port": "smtp_port",
    "smtp_user": "smtp_user",
    "smtp_password": "smtp_password",
    "email_from": "email_from",
    "cache_refresh_interval": "cache_refresh_interval",
}


def _get_env_fallback(chave: str) -> str | None:
    """Tenta ler o valor de uma chave a partir do .env (via Settings)."""
    attr_name = _ENV_FALLBACK_MAP.get(chave)
    if not attr_name:
        return None
    val = getattr(settings, attr_name, None)
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val)


def _seed_from_env(db: Session, chave: str) -> str | None:
    """Copia o valor do .env para o banco se a chave não existir.

    Tolerante a race condition: se dois workers tentarem inserir ao mesmo tempo,
    captura IntegrityError e faz refetch.
    """
    # Só tenta seed se a chave está no map de fallback
    if chave not in _ENV_FALLBACK_MAP:
        return None

    env_val = _get_env_fallback(chave)
    if env_val is None:
        return None

    try:
        existing = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()
        if existing:
            return existing.valor

        db.add(Configuracao(
            chave=chave,
            valor=env_val,
            atualizado_em=datetime.now(timezone.utc),
        ))
        db.commit()
        CHAVES_COPIADAS_DO_ENV.add(chave)
        logger.info("Config seeded from .env | chave=%s", chave)
        return env_val
    except IntegrityError:
        # Race condition: outro worker já inseriu a chave
        db.rollback()
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()
        return row.valor if row else env_val


def get(db: Session, chave: str, default: str = "") -> str:
    """Retorna o valor de uma configuração.

    Prioridade:
    1. Cache (TTL de 30s)
    2. SQLite (tabela configuracoes)
    3. .env (fallback via Settings, com seed automático)
    4. default informado
    """
    now = datetime.now(timezone.utc).timestamp()

    # 1. Cache
    cached = _cache.get(chave)
    if cached is not None and (now - cached[1]) < CACHE_TTL:
        return cached[0]

    # 2. SQLite
    row = db.execute(
        select(Configuracao).where(Configuracao.chave == chave)
    ).scalar_one_or_none()
    if row is not None and row.valor:
        _cache[chave] = (row.valor, now)
        return row.valor

    # 3. Fallback .env com seed automático
    # Só tenta seed para chaves que estão no map de fallback
    if chave in _ENV_FALLBACK_MAP:
        seeded = _seed_from_env(db, chave)
        if seeded is not None:
            _cache[chave] = (seeded, now)
            return seeded

    # 4. Default
    return default


# Sentinel value usado pelo frontend para campos mascarados.
# Quando o PATCH recebe este valor, o backend interpreta como
# "não alterar" — útil para campos sensíveis que o frontend
# não pode revelar.
SENTINEL_MASCARADO = "***configurado***"


def set_many(db: Session, valores: dict[str, str]) -> None:
    """Salva múltiplas configurações no banco.

    Valida contra CHAVES_EDITAVEIS — chaves não autorizadas são ignoradas
    com warning (não quebram a requisição para evitar frustração na UI).

    Trata SENTINEL_MASCARADO como "não alterar": se o frontend enviar
    o sentinel para uma chave existente, o valor atual é preservado.
    """
    now = datetime.now(timezone.utc)
    salvas: list[str] = []
    ignoradas: list[str] = []
    preservadas: list[str] = []
    for chave, valor in valores.items():
        if chave not in CHAVES_EDITAVEIS:
            ignoradas.append(chave)
            logger.warning("Tentativa de salvar chave não editável | chave=%s", chave)
            continue
        # Sentinel = preservar valor atual
        if valor == SENTINEL_MASCARADO:
            # Verifica se a chave já existe — se não existir, salva o sentinel
            # (caso o usuário queira literalmente "***configurado***" como valor,
            #  cenário improvável mas seguro)
            existing = db.execute(
                select(Configuracao).where(Configuracao.chave == chave)
            ).scalar_one_or_none()
            if existing:
                preservadas.append(chave)
                continue
        existing = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()
        if existing:
            existing.valor = valor
            existing.atualizado_em = now
        else:
            db.add(Configuracao(
                chave=chave,
                valor=valor,
                atualizado_em=now,
            ))
        salvas.append(chave)
    db.commit()
    invalidar_cache()
    if salvas:
        logger.info("Configurações salvas | chaves=%s", salvas)
    if preservadas:
        logger.info("Configurações preservadas (sentinel) | chaves=%s", preservadas)
    if ignoradas:
        logger.info("Configurações ignoradas (não editáveis) | chaves=%s", ignoradas)


def invalidar_cache() -> None:
    """Limpa o cache interno."""
    _cache.clear()
