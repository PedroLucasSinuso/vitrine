"""Criptografia Fernet para configurações sensíveis — isolado do config_service.py.

Usa ``cryptography.fernet.Fernet`` para criptografar valores de chaves
sensíveis (ex: erp_password) antes de persistir no SQLite.

Se ``ERPS_ENCRYPTION_KEY`` não estiver configurada no .env, as senhas
são salvas em texto plano (compatibilidade retroativa).
"""

import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cipher global — inicializado uma vez no import
_cipher: Fernet | None = None
if settings.erps_encryption_key:
    try:
        _cipher = Fernet(settings.erps_encryption_key.encode())
    except Exception:
        logger.warning("ERPS_ENCRYPTION_KEY inválida — senhas serão salvas em texto plano")

# Sentinel value usado pelo frontend para campos mascarados.
# Quando o PATCH recebe este valor, o backend interpreta como
# "não alterar" — útil para campos sensíveis que o frontend
# não pode revelar.
SENTINEL_MASCARADO = "***configurado***"

# Chaves que são criptografadas em repouso
CHAVES_CRIPTOGRAFADAS: set[str] = {"erp_password"}


def is_cipher_available() -> bool:
    """Retorna ``True`` se a cifra Fernet foi inicializada com sucesso."""
    return _cipher is not None


def encrypt(valor: str) -> str:
    """Criptografa um valor usando Fernet (simétrico).

    Se a cifra não estiver disponível, retorna o valor original
    (texto plano — compatibilidade retroativa).
    """
    if not _cipher or not valor:
        return valor
    return _cipher.encrypt(valor.encode()).decode()


def decrypt(valor: str) -> str:
    """Descriptografa um valor previamente criptografado com Fernet.

    Se o valor já estiver em texto puro (legado anterior à criptografia),
    retorna o próprio valor como fallback — sem quebrar a aplicação.
    Se a cifra não estiver disponível, retorna o valor original.
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
            "(pode ser legado anterior à criptografia)."
        )
        return valor


def migrar_chaves_criptografia(db_session) -> None:
    """Re-salva chaves protegidas que ainda estão em texto puro.

    Executado uma vez na inicialização. Detecta se o valor já está
    criptografado tentando descriptografar:
    - Se falhar → é texto puro → criptografa e salva.
    - Se funcionar → já está criptografado → pula.
    """
    if not _cipher:
        return  # Sem chave de criptografia configurada, nada a migrar

    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.domain.models.configuracao import Configuracao

    for chave in CHAVES_CRIPTOGRAFADAS:
        row = db_session.execute(
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
            pass  # Texto puro — precisa migrar
        try:
            row.valor = _cipher.encrypt(row.valor.encode()).decode()
            row.atualizado_em = datetime.now(timezone.utc)
            db_session.commit()
            logger.info("Chave criptografada na migração | chave=%s", chave)
        except Exception as e:
            db_session.rollback()
            logger.error(
                "Erro ao migrar chave para criptografia | chave=%s erro=%s", chave, e
            )
