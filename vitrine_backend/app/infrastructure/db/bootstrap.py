import os
import atexit
import threading
import logging

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