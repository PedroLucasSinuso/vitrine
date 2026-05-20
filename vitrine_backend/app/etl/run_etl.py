"""CLI para rodar sync manualmente (substitui o antigo run_etl)."""
from app.core.logging_config import setup_logging
from app.application.sync_service import run_sync_scheduled

setup_logging()


def run_etl():
    run_sync_scheduled()


if __name__ == "__main__":
    run_etl()
