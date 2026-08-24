"""Criptografia Fernet para configurações sensíveis — isolado do config_service.py.

Usa ``cryptography.fernet.MultiFernet`` (em vez de um único ``Fernet``) para
permitir rotação de chave sem perder acesso a valores já criptografados:

- Criptografia sempre usa a chave PRIMÁRIA (``ERPS_ENCRYPTION_KEY``).
- Descriptografia tenta a chave primária e, se falhar, cada chave listada em
  ``ERPS_ENCRYPTION_KEY_OLD`` (separadas por vírgula) — na ordem informada.

Isso resolve o problema anterior (chave única, imutável): antes, trocar
``ERPS_ENCRYPTION_KEY`` tornava senhas já salvas ilegíveis para sempre.
Agora o fluxo de rotação é:

1. Gere uma chave nova.
2. Mova a chave atual para ``ERPS_ENCRYPTION_KEY_OLD`` (acrescente à lista se
   já houver outras) e coloque a chave nova em ``ERPS_ENCRYPTION_KEY``.
3. Rode ``uv run python scripts/rotate_encryption_key.py`` — ele decifra cada
   valor sensível com qualquer chave da lista e re-grava usando só a nova.
4. Depois de confirmar que tudo funciona, as chaves antigas podem ser
   removidas de ``ERPS_ENCRYPTION_KEY_OLD``.

Se nenhuma chave estiver configurada, os valores são salvos em texto plano
(compatibilidade retroativa).
"""

import logging
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_cipher() -> MultiFernet | None:
    """Monta o MultiFernet a partir da chave primária + chaves antigas.

    A primeira chave válida da lista é a primária (usada para criptografar
    valores novos); as demais só servem para conseguir descriptografar
    valores gravados com uma chave anterior, durante uma rotação.
    """
    chaves_raw = [settings.erps_encryption_key] + [
        chave.strip()
        for chave in settings.erps_encryption_key_old.split(",")
        if chave.strip()
    ]

    fernets: list[Fernet] = []
    for chave in chaves_raw:
        if not chave:
            continue
        try:
            fernets.append(Fernet(chave.encode()))
        except Exception:
            logger.warning(
                "Uma das chaves ERPS_ENCRYPTION_KEY* é inválida — ignorada"
            )

    if not fernets:
        return None
    return MultiFernet(fernets)


# Cipher global — inicializado uma vez no import
_cipher: MultiFernet | None = _build_cipher()

# Sentinel value usado pelo frontend para campos mascarados.
# Quando o PATCH recebe este valor, o backend interpreta como
# "não alterar" — útil para campos sensíveis que o frontend
# não pode revelar.
SENTINEL_MASCARADO = "***configurado***"

# Chaves que são criptografadas em repouso
CHAVES_CRIPTOGRAFADAS: set[str] = {"erp_password"}


def is_cipher_available() -> bool:
    """Retorna ``True`` se ao menos uma chave Fernet válida foi carregada."""
    return _cipher is not None


def encrypt(valor: str) -> str:
    """Criptografa um valor usando a chave primária (Fernet simétrico).

    Se a cifra não estiver disponível, retorna o valor original
    (texto plano — compatibilidade retroativa).
    """
    if not _cipher or not valor:
        return valor
    return _cipher.encrypt(valor.encode()).decode()


def decrypt(valor: str) -> str:
    """Descriptografa um valor tentando a chave primária e, na sequência,
    cada chave antiga em ``ERPS_ENCRYPTION_KEY_OLD``.

    Se nenhuma chave decifrar o valor (texto legado anterior à criptografia,
    ou dado corrompido), retorna o próprio valor como fallback — sem quebrar
    a aplicação. Se a cifra não estiver disponível, retorna o valor original.
    """
    if not _cipher or not valor:
        return valor
    try:
        return _cipher.decrypt(valor.encode()).decode()
    except InvalidToken:
        logger.warning(
            "Valor não decifrável com nenhuma chave configurada — retornando "
            "como está (pode ser texto legado anterior à criptografia, ou "
            "uma chave antiga que já saiu de ERPS_ENCRYPTION_KEY_OLD)."
        )
        return valor
    except Exception:
        logger.warning("Falha inesperada ao descriptografar — retornando valor bruto")
        return valor


def migrar_chaves_criptografia(db_session) -> None:
    """Re-salva chaves protegidas que ainda estão em texto puro.

    Executado uma vez na inicialização. Detecta se o valor já está
    criptografado tentando descriptografar (com qualquer chave conhecida):
    - Se falhar → é texto puro → criptografa com a chave primária e salva.
    - Se funcionar → já está criptografado → pula.
    """
    if not _cipher:
        return  # Sem chave de criptografia configurada, nada a migrar

    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.domain.models.configuracao import Configuracao

    # Configuracao.chave não é mais única globalmente (PK composta com
    # empresa_id) — cada empresa tem sua própria linha por chave, então
    # é preciso migrar TODAS as linhas que casam com CHAVES_CRIPTOGRAFADAS,
    # não só uma por nome de chave.
    rows = db_session.execute(
        select(Configuracao).where(Configuracao.chave.in_(CHAVES_CRIPTOGRAFADAS))
    ).scalars().all()
    for row in rows:
        if not row.valor:
            continue
        # Tenta descriptografar — se falhar é texto puro
        try:
            _cipher.decrypt(row.valor.encode())
            # OK, já criptografado com alguma das chaves conhecidas
            continue
        except Exception:
            pass  # Texto puro — precisa migrar
        try:
            row.valor = _cipher.encrypt(row.valor.encode()).decode()
            row.atualizado_em = datetime.now(timezone.utc)
            db_session.commit()
            logger.info(
                "Chave criptografada na migração | empresa_id=%s chave=%s",
                row.empresa_id, row.chave,
            )
        except Exception as e:
            db_session.rollback()
            logger.error(
                "Erro ao migrar chave para criptografia | empresa_id=%s chave=%s erro=%s",
                row.empresa_id, row.chave, e,
            )


def reencriptar_com_chave_atual(db_session) -> int:
    """Re-criptografa todo valor sensível com a chave PRIMÁRIA atual.

    Usado no processo de rotação (ver docstring do módulo e
    ``scripts/rotate_encryption_key.py``): decifra cada valor com qualquer
    chave conhecida (primária ou antiga) e regrava usando só a primária,
    para que as chaves antigas possam eventualmente ser removidas de
    ``ERPS_ENCRYPTION_KEY_OLD``.

    Retorna a quantidade de valores efetivamente re-criptografados.
    """
    if not _cipher:
        return 0

    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.domain.models.configuracao import Configuracao

    total = 0
    rows = db_session.execute(
        select(Configuracao).where(Configuracao.chave.in_(CHAVES_CRIPTOGRAFADAS))
    ).scalars().all()
    for row in rows:
        if not row.valor:
            continue
        try:
            valor_plano = _cipher.decrypt(row.valor.encode()).decode()
        except InvalidToken:
            logger.warning(
                "Não foi possível decifrar '%s' (empresa_id=%s) com nenhuma chave "
                "conhecida — pulando (verifique se a chave antiga ainda está em "
                "ERPS_ENCRYPTION_KEY_OLD).",
                row.chave, row.empresa_id,
            )
            continue
        row.valor = _cipher.encrypt(valor_plano.encode()).decode()
        row.atualizado_em = datetime.now(timezone.utc)
        db_session.commit()
        total += 1
        logger.info(
            "Chave re-criptografada com a chave primária atual | empresa_id=%s chave=%s",
            row.empresa_id, row.chave,
        )
    return total
