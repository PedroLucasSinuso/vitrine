import os
import socket
import threading
import logging
from datetime import datetime, timedelta, timezone

from app.infrastructure.db.database import Base
from app.infrastructure.db.session import sqlite_engine

logger = logging.getLogger(__name__)

_migration_feita = False
_init_db_lock = threading.Lock()


def _run_migrations():
    """Executa migrações via Alembic.

    1. Stamp head — garante que DBs existentes (sem alembic_version)
       sejam marcadas como atualizadas.
    2. Upgrade head — aplica pendentes (seguro no-op se já atualizado).
    """
    from alembic.config import Config
    from alembic import command

    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    alembic_cfg = Config(os.path.join(_base, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(_base, "alembic"))
    command.stamp(alembic_cfg, "head")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migration: Alembic head verificado")


def init_db():
    global _migration_feita
    with _init_db_lock:
        if _migration_feita:
            return
        # Import all domain models para registrar no Base.metadata
        # ANTES de create_all(). Inclui modelos de intelligence, etc.
        import app.domain.models  # noqa: F401
        _warn_fernet_key_rotation()
        Base.metadata.create_all(bind=sqlite_engine)
        _run_migrations()

        # Migração de chaves criptografadas (config_crypto / config_service)
        try:
            from app.application.config_crypto import migrar_chaves_criptografia
            from app.infrastructure.db.session import SqliteSession
            session = SqliteSession()
            try:
                migrar_chaves_criptografia(session)
            finally:
                session.close()
        except Exception:
            logger.exception("Erro na migração de criptografia de chaves")

        _migration_feita = True


STALE_LOCK_MINUTES = 10


def acquire_scheduler_lock() -> bool:
    """Adquire lock do scheduler via SQLite.

    Usa tabela scheduler_lock (singleton row, id=1).
    - Se não existe → INSERT (lock adquirido)
    - Se existe e heartbeat recente → False (outro worker ativo)
    - Se existe e heartbeat expirado → UPDATE (lock roubado)

    Mais robusto que PID file: funciona em qualquer SO, auto-expira
    após STALE_LOCK_MINUTES sem heartbeat, visível via SQL.
    """
    from app.infrastructure.db.session import SqliteSession
    from app.domain.models.scheduler_lock import SchedulerLock

    hostname = socket.gethostname()
    pid = os.getpid()

    session = SqliteSession()
    try:
        lock = session.get(SchedulerLock, 1)
        now = datetime.now(timezone.utc)

        if lock is None:
            # Nenhum lock — cria
            session.add(SchedulerLock(
                id=1, pid=pid, hostname=hostname,
                acquired_at=now, heartbeat_at=now,
            ))
            session.commit()
            logger.info("Scheduler lock adquirido | pid=%s hostname=%s", pid, hostname)
            return True

        # Lock existe — verifica se é stale
        idade_heartbeat = now - lock.heartbeat_at.replace(tzinfo=timezone.utc)
        if idade_heartbeat < timedelta(minutes=STALE_LOCK_MINUTES):
            logger.warning(
                "Scheduler lock ocupado por pid=%s hostname=%s "
                "(heartbeat há %.0f min)",
                lock.pid, lock.hostname, idade_heartbeat.total_seconds() / 60,
            )
            return False

        # Lock stale — rouba
        lock.pid = pid
        lock.hostname = hostname
        lock.acquired_at = now
        lock.heartbeat_at = now
        session.commit()
        logger.info(
            "Scheduler lock roubado de pid=%s hostname=%s | pid=%s",
            lock.pid, lock.hostname, pid,
        )
        return True
    except Exception:
        logger.exception("Erro ao adquirir scheduler lock")
        return False
    finally:
        session.close()


def heartbeat_scheduler_lock() -> None:
    """Atualiza heartbeat do lock. Chamado pelo scheduler a cada 5 min."""
    from app.infrastructure.db.session import SqliteSession
    from app.domain.models.scheduler_lock import SchedulerLock

    session = SqliteSession()
    try:
        lock = session.get(SchedulerLock, 1)
        if lock and lock.pid == os.getpid():
            lock.heartbeat_at = datetime.now(timezone.utc)
            session.commit()
    except Exception:
        logger.warning("Falha ao atualizar heartbeat do scheduler lock", exc_info=True)
    finally:
        session.close()


def release_scheduler_lock() -> None:
    """Remove lock do scheduler. Chamado no shutdown."""
    from app.infrastructure.db.session import SqliteSession
    from app.domain.models.scheduler_lock import SchedulerLock

    session = SqliteSession()
    try:
        lock = session.get(SchedulerLock, 1)
        if lock and lock.pid == os.getpid():
            session.delete(lock)
            session.commit()
            logger.info("Scheduler lock liberado | pid=%s", os.getpid())
    except Exception:
        logger.warning("Falha ao liberar scheduler lock", exc_info=True)
    finally:
        session.close()


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