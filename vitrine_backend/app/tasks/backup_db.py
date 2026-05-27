"""Backup automático do SQLite.

Uso:
    uv run python -m app.tasks.backup_db                    # backup + manter 7
    uv run python -m app.tasks.backup_db --keep 14          # manter 14 backups
    uv run python -m app.tasks.backup_db --backup-dir D:\backups  # diretório customizado

Recomendação (Windows Task Scheduler):
    Criar tarefa diária executando o comando acima.
    Horário sugerido: 03:00 (antes da abertura da loja).
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("vitrine.backup_db")

# ── Caminhos padrão ──────────────────────────────────────────────────────
_DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "price_checker.db"
_DEFAULT_BACKUP_DIR = _DEFAULT_DB.parent / "backups"


def _format_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024**2:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / 1024**2:.1f} MB"


def backup_db(db_path: Path, backup_dir: Path, keep: int = 7) -> Path | None:
    """Copia o SQLite para um diretório de backup com timestamp.

    Args:
        db_path: Caminho do arquivo .db.
        backup_dir: Diretório onde os backups serão armazenados.
        keep: Número máximo de backups a manter (os mais antigos são removidos).

    Returns:
        Caminho do arquivo de backup criado, ou None em caso de erro.
    """
    if not db_path.exists():
        logger.error("Banco não encontrado em %s", db_path)
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"price_checker_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_path)
    except OSError as e:
        logger.exception("Erro ao copiar %s para %s: %s", db_path, backup_path, e)
        return None

    size = _format_size(backup_path.stat().st_size)
    logger.info("Backup criado: %s (%s)", backup_path, size)

    # ── Podar backups antigos ─────────────────────────────────────────────
    backups = sorted(backup_dir.glob("price_checker_*.db"))
    while len(backups) > keep:
        old = backups.pop(0)
        old.unlink()
        logger.info("Backup antigo removido: %s", old)

    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Backup do banco SQLite")
    parser.add_argument(
        "--keep",
        type=int,
        default=7,
        help="Número máximo de backups a manter (padrão: 7)",
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=None,
        help="Diretório de backup (padrão: <data_dir>/backups/)",
    )
    args = parser.parse_args()

    # Setup básico de log para uso via CLI
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    db_path = _DEFAULT_DB
    backup_dir = Path(args.backup_dir) if args.backup_dir else _DEFAULT_BACKUP_DIR

    result = backup_db(db_path, backup_dir, keep=args.keep)
    if result is None:
        sys.exit(1)
    print(f"Backup concluído: {result}")
    sys.exit(0)


if __name__ == "__main__":
    main()
