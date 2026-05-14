from sqlalchemy import Engine, create_engine
from app.core.config import settings


_engine: Engine | None = None


def get_bi_engine() -> Engine:
    """Retorna o engine SQLAlchemy para o PostgreSQL, criando se necessário."""
    global _engine
    if _engine is None:
        if not settings.postgres_url:
            raise RuntimeError(
                "POSTGRES_URL não configurado. "
                "O módulo BI requer conexão com o PostgreSQL."
            )
        _engine = create_engine(
            settings.postgres_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
            connect_args={"connect_timeout": 10},
        )
    return _engine