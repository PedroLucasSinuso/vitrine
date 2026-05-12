from app.core.logging_config import setup_logging
from app.infrastructure.db.bootstrap import init_db
from app.application.etl.pipeline import run_etl as run_etl_pipeline

setup_logging()


def run_etl():
    init_db()
    run_etl_pipeline()


if __name__ == "__main__":
    run_etl()