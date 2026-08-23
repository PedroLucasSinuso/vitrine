"""Central de configurações operacionais.

Serviço unificado para ler e escrever configurações do sistema no SQLite.
Fallback automático para .env (Settings) quando a chave não existe no banco,
permitindo migração transparente.

Multi-tenant (Fase 1): toda configuração (ERP, Twilio, SMTP, ...) é por
empresa — ``Configuracao`` tem PK composta (empresa_id, chave). Toda
função pública deste módulo agora recebe ``empresa_id`` como primeiro
parâmetro (depois de ``db``) e nunca deve ser chamada sem ele para
qualquer coisa além de chaves ``is_only_env`` (que continuam vindo só do
.env, sem tenant). O cache em memória (config_cache) usa uma chave
composta ``"{empresa_id}:{chave}"`` — sem isso, o valor de uma empresa
vazaria para outra por até 30s (TTL do cache).

Responsabilidades delegadas a módulos especializados:
  - ``config_cache``: Cache TTL + thread lock
  - ``config_crypto``: Fernet encryption/decryption
  - ``config_validator``: Whitelist de chaves editáveis e validação de sensibilidade
"""

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.domain.models.configuracao import Configuracao
from app.core.config import settings

# ── Delegado: cache ──────────────────────────────────────────────────
from app.application.config_cache import (
    get_from_cache,
    set_in_cache,
    invalidate_cache as _invalidate_cache_impl,
    _cache,  # exposto para testes (test_config_service)
)

# ── Delegado: criptografia ───────────────────────────────────────────
from app.application.config_crypto import (
    encrypt as _encrypt,
    decrypt as _decrypt,
    SENTINEL_MASCARADO,
    CHAVES_CRIPTOGRAFADAS,
    migrar_chaves_criptografia as _migrar_chaves_criptografia_impl,
)

# ── Delegado: validação ──────────────────────────────────────────────
from app.application.config_validator import (
    is_sensitive,
    CHAVES_EDITAVEIS,
    is_only_env,
    CHAVES_SOMENTE_ENV as _CHAVES_SOMENTE_ENV,
)

logger = logging.getLogger(__name__)

# Re-export da API pública para não quebrar consumidores existentes
invalidar_cache = _invalidate_cache_impl
_migrar_chaves_criptografia = _migrar_chaves_criptografia_impl

# Flag para rastrear chaves copiadas do .env (usado internamente)
CHAVES_COPIADAS_DO_ENV: set[str] = set()

# Mapeamento de chaves do banco para atributos do Settings (.env)
_ENV_FALLBACK_MAP: dict[str, str] = {
    "erp_host": "postgres_host",
    "erp_port": "postgres_port",
    "erp_database": "postgres_database",
    "erp_user": "postgres_user",
    "erp_password": "postgres_password",
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


def _cache_key(empresa_id: int, chave: str) -> str:
    """Chave composta usada no cache em memória — nunca usar `chave` sozinha,
    ou o valor de uma empresa vaza para outra durante o TTL do cache."""
    return f"{empresa_id}:{chave}"


def _get_env_fallback(chave: str) -> str | None:
    """Tenta ler o valor de uma chave a partir do .env (via Settings).

    Só existe UM .env por processo (não é por empresa) — usado como seed
    inicial na primeira empresa/instalação. Empresas criadas depois não
    herdam .env automaticamente (fazem sentido configurar via UI mesmo).

    Para chaves ERP (erp_host, erp_port, ...), também tenta parsear
    o postgres_url legado como fallback adicional, garantindo
    retrocompatibilidade.
    """
    attr_name = _ENV_FALLBACK_MAP.get(chave)
    if not attr_name:
        return None
    val = getattr(settings, attr_name, None)
    if val and (not isinstance(val, str) or val.strip()):
        return str(val)

    # Fallback: se o .env ainda tem POSTGRES_URL, tenta parsear para
    # extrair o campo individual (ex: erp_host → postgres_url → parse)
    _MAPA_URL_PARTES = {
        "erp_host": 0,
        "erp_port": 1,
        "erp_user": 2,
        "erp_password": 3,
        "erp_database": 4,
    }
    if chave in _MAPA_URL_PARTES and settings.postgres_url:
        return _extrair_de_url_legado(chave, _MAPA_URL_PARTES)
    return None


def _extrair_de_url_legado(chave: str, mapa: dict[str, int]) -> str | None:
    """Extrai campo individual de uma postgresql:// URL legada."""
    try:
        parsed = urlparse(settings.postgres_url)
        idx = mapa[chave]
        partes = {
            0: parsed.hostname or "",
            1: str(parsed.port) if parsed.port else "5432",
            2: parsed.username or "",
            3: unquote(parsed.password) if parsed.password else "",
            4: parsed.path.lstrip("/") if parsed.path else "",
        }
        val = partes.get(idx)
        return val if val else None
    except Exception:
        return None


def _seed_from_env(db: Session, empresa_id: int, chave: str) -> str | None:
    """Copia o valor do .env para o banco se a chave não existir PARA ESSA EMPRESA.

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
            select(Configuracao).where(
                Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
            )
        ).scalar_one_or_none()
        if existing:
            return existing.valor

        # Criptografa antes de salvar se for chave protegida
        valor_final = _encrypt(env_val) if chave in CHAVES_CRIPTOGRAFADAS else env_val
        db.add(Configuracao(
            empresa_id=empresa_id,
            chave=chave,
            valor=valor_final,
            atualizado_em=datetime.now(timezone.utc),
        ))
        db.commit()
        CHAVES_COPIADAS_DO_ENV.add(chave)
        logger.info("Config seeded from .env | empresa_id=%s chave=%s", empresa_id, chave)
        return valor_final
    except IntegrityError:
        # Race condition: outro worker já inseriu a chave
        db.rollback()
        row = db.execute(
            select(Configuracao).where(
                Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
            )
        ).scalar_one_or_none()
        return row.valor if row else env_val


def get(db: Session, empresa_id: int, chave: str, default: str = "") -> str:
    """Retorna o valor de uma configuração DA EMPRESA informada.

    Prioridade:
    1. Cache (TTL de 30s, chaveado por empresa+chave)
    2. SQLite (tabela configuracoes)
    3. .env (fallback via Settings, com seed automático)
    4. default informado
    """
    # 0. Chaves que só vêm do .env — ignoram cache, banco E empresa
    if is_only_env(chave):
        env_val: str | None = getattr(settings, chave, None)
        return env_val if env_val else default

    now = datetime.now(timezone.utc).timestamp()
    ck = _cache_key(empresa_id, chave)

    # 1. Cache
    cached = get_from_cache(ck, now)
    if cached is not None:
        return cached

    # 2. SQLite
    row = db.execute(
        select(Configuracao).where(
            Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
        )
    ).scalar_one_or_none()
    if row is not None and row.valor:
        set_in_cache(ck, row.valor, now)
        return row.valor

    # 3. Fallback .env com seed automático
    if chave in _ENV_FALLBACK_MAP:
        seeded = _seed_from_env(db, empresa_id, chave)
        if seeded is not None:
            set_in_cache(ck, seeded, now)
            return seeded

    # 4. Default
    return default


def get_many(db: Session, empresa_id: int, chaves: list[str]) -> dict[str, str]:
    """Retorna múltiplas configurações DA EMPRESA em uma única query (m3).

    Popula o cache interno para todas as chaves encontradas.
    Chaves não encontradas retornam string vazia (mesmo comportamento
    de ``get()`` sem default).
    """
    now = datetime.now(timezone.utc).timestamp()
    resultado: dict[str, str] = {}

    # Separa chaves que só vêm do .env
    pendentes: list[str] = []
    for chave in chaves:
        if is_only_env(chave):
            env_val: str | None = getattr(settings, chave, None)
            resultado[chave] = env_val if env_val else ""
        else:
            pendentes.append(chave)

    if not pendentes:
        return resultado

    # Cache hit
    for chave in pendentes:
        cached = get_from_cache(_cache_key(empresa_id, chave), now)
        if cached is not None:
            resultado[chave] = cached

    ainda_pendentes = [c for c in pendentes if c not in resultado]
    if not ainda_pendentes:
        return resultado

    # Batch query SQLite
    rows = db.execute(
        select(Configuracao).where(
            Configuracao.empresa_id == empresa_id,
            Configuracao.chave.in_(ainda_pendentes),
        )
    ).scalars().all()
    row_map = {r.chave: r.valor for r in rows}

    for chave in ainda_pendentes:
        valor = row_map.get(chave, "")
        if valor:
            set_in_cache(_cache_key(empresa_id, chave), valor, now)
        resultado[chave] = valor

    # Seed do .env para chaves não encontradas (apenas chaves do fallback map)
    for chave in ainda_pendentes:
        if not resultado[chave] and chave in _ENV_FALLBACK_MAP:
            seeded = _seed_from_env(db, empresa_id, chave)
            if seeded is not None:
                set_in_cache(_cache_key(empresa_id, chave), seeded, now)
                resultado[chave] = seeded

    return resultado


def get_decrypted(db: Session, empresa_id: int, chave: str, default: str = "") -> str:
    """Retorna o valor descriptografado de uma chave sensível DA EMPRESA.

    Útil para consumidores que precisam do valor real (ex: montagem de URL
    de conexão), não do hash/cyphertext armazenado.
    """
    valor = get(db, empresa_id, chave, default)
    if chave in CHAVES_CRIPTOGRAFADAS and valor:
        return _decrypt(valor)
    return valor


def set_many(db: Session, empresa_id: int, valores: dict[str, str]) -> list[str]:
    """Salva múltiplas configurações DA EMPRESA no banco.

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
        # Bloqueia chaves que só podem vir do .env (ex: jwt_secret)
        if is_only_env(chave):
            ignoradas.append(chave)
            logger.warning(
                "Tentativa de salvar chave protegida (somente .env) | chave=%s", chave
            )
            continue
        if chave not in CHAVES_EDITAVEIS:
            ignoradas.append(chave)
            logger.warning("Tentativa de salvar chave não editável | chave=%s", chave)
            continue

        # String vazia = preservar valor atual se já existir algo salvo
        if not valor:
            existing = db.execute(
                select(Configuracao).where(
                    Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
                )
            ).scalar_one_or_none()
            if existing and existing.valor and existing.valor != SENTINEL_MASCARADO:
                preservadas.append(chave)
                continue

        # Sentinel = preservar valor atual
        if valor == SENTINEL_MASCARADO:
            existing = db.execute(
                select(Configuracao).where(
                    Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
                )
            ).scalar_one_or_none()
            if existing:
                preservadas.append(chave)
                continue

        # Criptografa antes de salvar se a chave estiver na lista de protegidas
        if chave in CHAVES_CRIPTOGRAFADAS and valor and valor != SENTINEL_MASCARADO:
            valor = _encrypt(valor)

        existing = db.execute(
            select(Configuracao).where(
                Configuracao.empresa_id == empresa_id, Configuracao.chave == chave
            )
        ).scalar_one_or_none()
        if existing:
            existing.valor = valor
            existing.atualizado_em = now
        else:
            db.add(Configuracao(
                empresa_id=empresa_id,
                chave=chave,
                valor=valor,
                atualizado_em=now,
            ))
        salvas.append(chave)
    db.commit()
    invalidar_cache()
    if salvas:
        logger.info("Configurações salvas | empresa_id=%s chaves=%s", empresa_id, salvas)
    if preservadas:
        logger.info("Configurações preservadas (sentinel) | empresa_id=%s chaves=%s", empresa_id, preservadas)
    if ignoradas:
        logger.info("Configurações ignoradas (não editáveis) | empresa_id=%s chaves=%s", empresa_id, ignoradas)

    return ignoradas


def montar_url_postgres(db: Session, empresa_id: int) -> str:
    """Monta a URL de conexão PostgreSQL (do ERP DA EMPRESA) a partir dos
    campos individuais.

    Lê erp_host, erp_port, erp_database, erp_user do ConfigService e
    descriptografa erp_password automaticamente via ``get_decrypted()``.
    Usa ``get_many()`` (m3) para fazer uma única query em vez de 5 ``get()`` separados.
    """
    _CHAVES_ERP = ["erp_host", "erp_port", "erp_database", "erp_user", "erp_password"]
    valores = get_many(db, empresa_id, _CHAVES_ERP)

    host = valores.get("erp_host", "")
    port = valores.get("erp_port", "5432")
    database = valores.get("erp_database", "")
    user = valores.get("erp_user", "")
    enc_password = valores.get("erp_password", "")

    if not all([host, database, user, enc_password]):
        return ""

    password = _decrypt(enc_password) if enc_password else enc_password
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
