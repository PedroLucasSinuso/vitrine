from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from app.application.config_service import montar_url_postgres


def get_alterdata_engine(db: Session) -> Engine:
    """Retorna um engine SQLAlchemy para o PostgreSQL do Alterdata.

    A URL de conexão é montada dinamicamente a partir das configurações
    do ERP armazenadas no SQLite (erp_host, erp_port, etc.) via
    montar_url_postgres(). Cada chamada recria o engine para refletir
    alterações de configuração em tempo real.
    """
    url = montar_url_postgres(db)
    if not url:
        raise RuntimeError(
            "ERP não configurado. "
            "Acesse Admin > Configurações > ERP para configurar os campos "
            "de conexão (host, porta, database, usuário e senha)."
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
        connect_args={"connect_timeout": 10},
    )
