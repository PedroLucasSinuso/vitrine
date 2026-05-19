"""Central de configurações operacionais.

Serviço unificado para ler e escrever configurações do sistema no SQLite.
Fallback automático para .env (Settings) quando a chave não existe no banco,
permitindo migração transparente.
"""

import logging
import re
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet

from app.domain.models.configuracao import Configuracao
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Criptografia condicional ────────────────────────────────────────────────
# Se ERPS_ENCRYPTION_KEY estiver configurada no .env, senhas sensíveis
# (ex: erp_password) são criptografadas antes de salvar no banco e
# descriptografadas ao serem lidas. Sem a chave, as senhas são salvas
# em texto plano (compatibilidade retroativa).
_cipher: Fernet | None = None
if settings.erps_encryption_key:
    try:
        _cipher = Fernet(settings.erps_encryption_key.encode())
    except Exception:
        logger.warning("ERPS_ENCRYPTION_KEY inválida — senhas serão salvas em texto plano")

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
    # Aba Geral — Endereço
    "endereco_rua",
    "endereco_numero",
    "endereco_complemento",
    "endereco_bairro",
    "endereco_cidade",
    "endereco_estado",
    "endereco_cep",
    # Aba ERP — campos individuais (substitui erp_postgres_url)
    "erp_host",
    "erp_port",
    "erp_database",
    "erp_user",
    "erp_password",
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
    "erp_password",
}

_PADROES_SENSIVEIS = re.compile(
    r"(password|secret|token|key|api_key|auth_token|sid|(?<!logo_)url)", re.IGNORECASE
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


def _get_env_fallback(chave: str) -> str | None:
    """Tenta ler o valor de uma chave a partir do .env (via Settings).

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

        # Criptografa antes de salvar se for chave protegida
        valor_final = _criptografar(env_val) if chave in _CHAVES_CRIPTOGRAFADAS else env_val
        db.add(Configuracao(
            chave=chave,
            valor=valor_final,
            atualizado_em=datetime.now(timezone.utc),
        ))
        db.commit()
        CHAVES_COPIADAS_DO_ENV.add(chave)
        logger.info("Config seeded from .env | chave=%s", chave)
        return valor_final
    except IntegrityError:
        # Race condition: outro worker já inseriu a chave
        db.rollback()
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()
        return row.valor if row else env_val


_migracao_criptografia_feita = False


def get(db: Session, chave: str, default: str = "") -> str:
    """Retorna o valor de uma configuração.

    Prioridade:
    1. Cache (TTL de 30s)
    2. SQLite (tabela configuracoes)
    3. .env (fallback via Settings, com seed automático)
    4. default informado
    """
    global _migracao_criptografia_feita
    if not _migracao_criptografia_feita:
        _migrar_chaves_criptografia(db)
        _migracao_criptografia_feita = True

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


# ── Função pública para obter valor descriptografado ───────────────────────────


def get_decrypted(db: Session, chave: str, default: str = "") -> str:
    """Retorna o valor descriptografado de uma chave sensível.

    Útil para consumidores que precisam do valor real (ex: montagem de URL
    de conexão), não do hash/cyphertext armazenado.
    """
    valor = get(db, chave, default)
    if chave in _CHAVES_CRIPTOGRAFADAS and valor:
        return _descriptografar(valor)
    return valor


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
        # String vazia = preservar valor atual se já existir algo salvo
        # Impede que o frontend sobrescreva senhas ao enviar "" durante edição
        if not valor:
            existing = db.execute(
                select(Configuracao).where(Configuracao.chave == chave)
            ).scalar_one_or_none()
            if existing and existing.valor and existing.valor != SENTINEL_MASCARADO:
                preservadas.append(chave)
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
        # Criptografa antes de salvar se a chave estiver na lista de protegidas
        if chave in _CHAVES_CRIPTOGRAFADAS and valor and valor != SENTINEL_MASCARADO:
            valor = _criptografar(valor)

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


# ── Chaves que são criptografadas em repouso ────────────────────────────────
_CHAVES_CRIPTOGRAFADAS: set[str] = {"erp_password"}


def _migrar_chaves_criptografia(db: Session) -> None:
    """Re-salva chaves protegidas que ainda estão em texto puro.

    Executado uma vez na inicialização (via `get()` ou explicitamente).
    Detecta se o valor já está criptografado tentando descriptografar:
    - Se falhar → é texto puro → criptografa e salva.
    - Se funcionar → já está criptografado → pula.
    """
    if not _cipher:
        return  # sem chave de criptografia configurada, nada a migrar
    for chave in _CHAVES_CRIPTOGRAFADAS:
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()
        if row is None or not row.valor:
            continue
        # Tenta descriptografar — se falhar é texto puro
        try:
            _cipher.decrypt(row.valor.encode())
            # OK, já criptografado
            continue
        except Exception:
            pass  # texto puro — precisa migrar
        try:
            row.valor = _cipher.encrypt(row.valor.encode()).decode()
            row.atualizado_em = datetime.now(timezone.utc)
            db.commit()
            logger.info("Chave criptografada na migração | chave=%s", chave)
        except Exception as e:
            db.rollback()
            logger.error("Erro ao migrar chave para criptografia | chave=%s erro=%s", chave, e)


def _criptografar(valor: str) -> str:
    """Criptografa um valor usando Fernet (simétrico)."""
    if not _cipher or not valor:
        return valor
    return _cipher.encrypt(valor.encode()).decode()


def _descriptografar(valor: str) -> str:
    """Descriptografa um valor previamente criptografado com Fernet.

    Se o valor já estiver em texto puro (legado anterior à criptografia),
    retorna o próprio valor como fallback — sem quebrar a conexão.
    """
    if not _cipher or not valor:
        return valor
    try:
        return _cipher.decrypt(valor.encode()).decode()
    except Exception:
        # Pode ser valor legado (texto puro) ou corrompido.
        # Em ambos os casos, retornar o valor bruto é mais seguro
        # do que retornar "" e quebrar a montagem da URL.
        logger.warning(
            "Valor não parece criptografado — retornando como está "
            "(pode ser legado anterior à criptografia). chave=erp_password"
        )
        return valor


def montar_url_postgres(db: Session) -> str:
    """Monta a URL de conexão PostgreSQL a partir dos campos individuais.

    Lê erp_host, erp_port, erp_database, erp_user do ConfigService e
    descriptografa erp_password automaticamente via get_decrypted().
    """
    host = get(db, "erp_host")
    port = get(db, "erp_port", "5432")
    database = get(db, "erp_database")
    user = get(db, "erp_user")
    enc_password = get(db, "erp_password")

    if not all([host, database, user, enc_password]):
        return ""

    password = get_decrypted(db, "erp_password")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def invalidar_cache() -> None:
    """Limpa o cache interno."""
    _cache.clear()
