from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def criar_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        return create_engine(url, future=True, connect_args={"check_same_thread": False})
    return create_engine(url, future=True, pool_pre_ping=True)


engine = criar_engine(settings.url_banco_app)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

sqlite_engine = engine
SqliteSession = SessionLocal
