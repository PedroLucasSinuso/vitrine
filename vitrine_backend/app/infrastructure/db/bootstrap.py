import os
import atexit
import importlib
import pkgutil
import logging
import threading
from pathlib import Path
from sqlalchemy import inspect
from app.infrastructure.db.session import sqlite_engine

# Auto-scan de models: todo .py em app/domain/models/ é importado para
# registrar no Base.metadata (M11; ver app.infrastructure.db.database.Base,
# usado por migrations/env.py). Isso evita esquecer de adicionar imports
# manuais quando um novo model é criado.
import app.domain.models as _models_pkg
for _module_info in pkgutil.iter_modules(_models_pkg.__path__):
    importlib.import_module(f"app.domain.models.{_module_info.name}")

logger = logging.getLogger(__name__)

_migration_feita = False
_init_db_lock = threading.Lock()

_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


def _run_alembic_migrations():
    """Aplica o schema via Alembic — substitui create_all() + as antigas
    migrações manuais (ALTER TABLE em try/except).

    A revisão baseline (migrations/versions/..._baseline...) foi gerada por
    autogenerate a partir dos models atuais, então é equivalente ao schema
    que create_all() + as migrações ad-hoc antigas já produziam.

    Bancos que já existiam ANTES da introdução do Alembic não têm a tabela
    'alembic_version' — nesse caso, em vez de tentar recriar tabelas que já
    existem, o banco é "carimbado" na revisão baseline primeiro (stamp),
    e só então 'upgrade head' roda (como no-op, já que baseline == head).
    Bancos novos simplesmente rodam 'upgrade head' e recebem o schema
    completo pela migração baseline.
    """
    from alembic.config import Config
    from alembic import command

    cfg = Config(str(_ALEMBIC_INI))

    inspector = inspect(sqlite_engine)
    tabelas_existentes = set(inspector.get_table_names())
    tem_schema_anterior_ao_alembic = (
        "usuarios" in tabelas_existentes and "alembic_version" not in tabelas_existentes
    )

    if tem_schema_anterior_ao_alembic:
        logger.info(
            "Banco existente sem controle do Alembic — carimbando na revisão "
            "baseline antes de aplicar novas migrações"
        )
        command.stamp(cfg, "head")

    command.upgrade(cfg, "head")


def init_db():
    global _migration_feita
    with _init_db_lock:
        if _migration_feita:
            return
        _warn_fernet_key_rotation()
        _run_alembic_migrations()

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
    """Avisa sobre o processo correto de rotação da chave Fernet.

    ERPS_ENCRYPTION_KEY agora suporta rotação segura via
    ERPS_ENCRYPTION_KEY_OLD (ver app/application/config_crypto.py):
    trocar a chave primária SEM antes mover a chave anterior para
    ERPS_ENCRYPTION_KEY_OLD ainda torna as senhas já criptografadas
    ilegíveis, então o aviso permanece — mas agora existe um caminho
    de saída (scripts/rotate_encryption_key.py) em vez de perda
    permanente.
    """
    from app.core.config import settings
    if settings.erps_encryption_key:
        logger.warning(
            "ERPS_ENCRYPTION_KEY está configurada. Para trocar esta chave "
            "com segurança, NÃO edite ERPS_ENCRYPTION_KEY diretamente: "
            "mova o valor atual para ERPS_ENCRYPTION_KEY_OLD, defina a "
            "chave nova em ERPS_ENCRYPTION_KEY e rode "
            "'uv run python scripts/rotate_encryption_key.py'. "
            "Consulte a documentação em README.md para mais detalhes."
        )