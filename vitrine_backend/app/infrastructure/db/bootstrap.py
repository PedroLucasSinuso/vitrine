from app.infrastructure.db.database import Base
from app.infrastructure.db.session import sqlite_engine
import app.domain.models.produto
import app.domain.models.cache_status
import app.domain.models.usuario
import app.domain.models.configuracao
import app.domain.models.inventario
def init_db():
    Base.metadata.create_all(bind=sqlite_engine)