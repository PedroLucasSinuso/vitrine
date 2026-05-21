"""Testes do SyncService (app.application.sync_service)."""
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.sync_service import SyncService
from app.domain.models.cache_status import CacheStatus
from app.infrastructure.db.database import Base


# ── Engine e sessão compartilhados ─────────────────────────────────────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Cria uma sessão limpa para cada teste."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup(db):
    """Limpa tabela entre testes."""
    yield
    db.execute(CacheStatus.__table__.delete())
    db.commit()


class TestSyncComErro:
    """sync_com_erro recovery path (T3)."""

    def test_sync_com_erro_cria_cache_status_erro(self, db):
        """Mock source falha → sync_com_erro é chamado → CacheStatus com status=erro."""
        # 1. Criar mock do ProductSource que levanta exceção
        source = Mock()
        source.get_all_products.side_effect = RuntimeError("Falha simulada no ERP")

        # 2. Executar sync (deve chamar sync_com_erro internamente)
        service = SyncService(source, db)

        with pytest.raises(RuntimeError, match="Erro ao sincronizar dados do ERP"):
            service.sync()

        # 3. Verificar que source.get_all_products foi chamado
        source.get_all_products.assert_called_once()

        # 4. Verificar que um CacheStatus com status="erro" foi criado
        #    (a mensagem é sanitizada pelo error_handler)
        cache_status = db.query(CacheStatus).order_by(
            CacheStatus.id.desc()
        ).first()
        assert cache_status is not None
        assert cache_status.status == "erro"
        assert cache_status.erro is not None
        # sanitizar_erro retorna msg genérica para RuntimeError
        assert "interno" in cache_status.erro.lower()
