import os
import atexit
import logging
import threading
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
import app.domain.models.token_blacklist
import app.domain.models.historico_preco  # noqa — registra o model no Base.metadata

logger = logging.getLogger(__name__)

_migration_feita = False
_init_db_lock = threading.Lock()


def _run_migrations():
    """Executa migrações incrementais (ALTER TABLE) que o create_all não cobre."""
    # Migration: coluna 'observacao' em itens_inventario
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("ALTER TABLE itens_inventario ADD COLUMN observacao TEXT"))
            conn.commit()
            logger.info("Migration: coluna 'observacao' adicionada a itens_inventario")
    except Exception:
        pass

    # Migration: coluna 'token_version' em usuarios (JWT revogação)
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            logger.info("Migration: coluna 'token_version' adicionada a usuarios")
    except Exception:
        pass

    # Migration: limpar jwt_secret do banco (agora é somente .env)
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("DELETE FROM configuracoes WHERE chave = 'jwt_secret'"))
            conn.commit()
            logger.info("Migration: jwt_secret removido da tabela configuracoes")
    except Exception:
        pass

    # Migration: cleanup de tokens expirados na blacklist (+30 dias)
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("DELETE FROM token_blacklist WHERE expires_at < datetime('now', '-30 days')"))
            conn.commit()
            logger.info("Migration: token_blacklist limpa (entradas >30 dias)")
    except Exception:
        pass

    # Migration: índice composto para historico_precos
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_hp_codigo_data "
                "ON historico_precos(codigo_chamada, data_coleta)"
            ))
            conn.commit()
    except Exception:
        pass

    # Migration: coluna 'ativo' em produtos
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("ALTER TABLE produtos ADD COLUMN ativo BOOLEAN NOT NULL DEFAULT 1"))
            conn.commit()
            logger.info("Migration: coluna 'ativo' adicionada a produtos")
    except Exception:
        pass


def init_db():
    global _migration_feita
    with _init_db_lock:
        if _migration_feita:
            return
        _warn_fernet_key_rotation()
        Base.metadata.create_all(bind=sqlite_engine)
        _run_migrations()

        # Migração de chaves criptografadas (config_service)
        try:
            from app.application.config_service import _migrar_chaves_criptografia
            from app.infrastructure.db.session import SqliteSession
            session = SqliteSession()
            try:
                _migrar_chaves_criptografia(session)
            finally:
                session.close()
        except Exception:
            logger.exception("Erro na migração de criptografia de chaves")

        _migration_feita = True


_SCHEDULER_LOCK_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".scheduler.lock"
)
_SCHEDULER_LOCK_FILE = os.path.abspath(_SCHEDULER_LOCK_FILE)


def acquire_scheduler_lock() -> bool:
    """Tenta adquirir lock exclusivo para o scheduler multi-worker.

    Cria um arquivo PID lock (.scheduler.lock). Se outro worker já
    criou o lock e o processo ainda está vivo, retorna False.
    Se o processo morreu (stale lock), remove e tenta novamente.
    """
    try:
        fd = os.open(_SCHEDULER_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        atexit.register(lambda: os.unlink(_SCHEDULER_LOCK_FILE) if os.path.exists(_SCHEDULER_LOCK_FILE) else None)
        logger.info("Scheduler lock adquirido | pid=%s", os.getpid())
        return True
    except FileExistsError:
        # Lock existe — verifica se processo ainda está vivo
        try:
            with open(_SCHEDULER_LOCK_FILE) as f:
                pid = int(f.read().strip())
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x100000, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    logger.warning("Scheduler lock ocupado por pid=%s", pid)
                    return False
                # Processo morto — lock stale
            else:
                import errno
                try:
                    os.kill(pid, 0)
                    logger.warning("Scheduler lock ocupado por pid=%s", pid)
                    return False
                except OSError as e:
                    if e.errno != errno.ESRCH:
                        raise
                    # Processo morto
        except (ValueError, OSError, FileNotFoundError):
            pass
        # Stale lock — remove e tenta novamente
        try:
            os.unlink(_SCHEDULER_LOCK_FILE)
            return acquire_scheduler_lock()
        except OSError:
            return False


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