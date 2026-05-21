import logging
from sqlalchemy import text
from app.infrastructure.db.database import Base
from app.infrastructure.db.session import sqlite_engine
import app.domain.models.produto
import app.domain.models.cache_status
import app.domain.models.usuario
import app.domain.models.configuracao
import app.domain.models.inventario
import app.domain.models.whatsapp_contato
import app.domain.models.email_contato
import app.domain.models.sync_job

logger = logging.getLogger(__name__)


def _run_migrations():
    """Executa migrações incrementais (ALTER TABLE) que o create_all não cobre."""
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("ALTER TABLE itens_inventario ADD COLUMN observacao TEXT"))
            conn.commit()
            logger.info("Migration: coluna 'observacao' adicionada a itens_inventario")
    except Exception:
        # Coluna já existe — ignora
        pass


def init_db():
    _warn_fernet_key_rotation()
    Base.metadata.create_all(bind=sqlite_engine)
    _run_migrations()


def _warn_fernet_key_rotation():
    """Previne rotação da chave Fernet após o primeiro uso.
    
    Se ERPS_ENCRYPTION_KEY for alterada depois que senhas já foram
    criptografadas no banco, as senhas existentes se tornam ilegíveis
    permanentemente (a chave antiga é necessária para descriptografar).
    """
    from app.core.config import settings
    if settings.erps_encryption_key:
        logger.warning(
            "ERPS_ENCRYPTION_KEY está configurada. ATENÇÃO: "
            "NÃO altere esta chave após o primeiro uso — senhas "
            "criptografadas no banco se tornarão ilegíveis "
            "permanentemente. Consulte a documentação em README.md "
            "para mais detalhes."
        )