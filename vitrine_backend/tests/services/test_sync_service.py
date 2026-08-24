"""Testes do SyncService (app.application.sync_service)."""
from decimal import Decimal
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.sync_service import SyncService
from app.domain.models.cache_status import CacheStatus
from app.domain.models.historico_preco import HistoricoPreco
from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.models.sync_job import SyncJob
from app.infrastructure.db.database import Base
from app.domain.models.empresa import Empresa


# ── Engine e sessão compartilhados ─────────────────────────────────────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

EMPRESA_ID = 1
with SessionLocal() as _s:
    _s.add(Empresa(id=EMPRESA_ID, nome="Empresa Teste", slug="empresa-teste", status="ativa"))
    _s.commit()


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
        service = SyncService(source, db, empresa_id=EMPRESA_ID)

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


class TestSyncComProdutosValidos:
    """sync com produtos válidos (T2)."""

    def test_sync_com_produtos_validos(self, db):
        """Sync com produtos válidos deve retornar SyncResult com contagens."""
        # Arrange
        from app.core.models.product import Product
        source = Mock()
        source.get_all_products.return_value = [
            Product(internal_code='001', name='Prod 1', group='G', family='F', barcodes=['123', '456']),
            Product(internal_code='002', name='Prod 2', group='G', family='F', barcodes=['789']),
        ]

        service = SyncService(source, db, empresa_id=EMPRESA_ID)
        result = service.sync()

        assert result.produtos_count == 2
        assert result.codigos_count == 3
        source.get_all_products.assert_called_once()

    def test_sync_persiste_produtos_no_banco(self, db):
        """Sync deve persistir produtos no banco SQLite."""
        from app.core.models.product import Product
        from app.domain.models.produto import Produto

        source = Mock()
        source.get_all_products.return_value = [
            Product(internal_code='001', name='Prod 1', group='G', family='F', sale_price=Decimal("10.50"), cost_price=Decimal("5.00"), stock=100.0),
        ]

        service = SyncService(source, db, empresa_id=EMPRESA_ID)
        service.sync()

        produtos_db = db.query(Produto).all()
        assert len(produtos_db) == 1
        assert produtos_db[0].codigo_chamada == '001'
        assert produtos_db[0].preco_venda == 10.50

    def test_sync_persiste_codigos_de_barras(self, db):
        """Sync deve persistir códigos de barras associados."""
        from app.core.models.product import Product
        from app.domain.models.produto import ProdutoCodigo

        source = Mock()
        source.get_all_products.return_value = [
            Product(internal_code='001', name='Prod 1', group='G', family='F', barcodes=['7891234567890', '7890987654321']),
        ]

        service = SyncService(source, db, empresa_id=EMPRESA_ID)
        service.sync()

        codigos = db.query(ProdutoCodigo).all()
        assert len(codigos) == 2
        codigos_str = [c.codigo for c in codigos]
        assert '7891234567890' in codigos_str
        assert '7890987654321' in codigos_str

    def test_sync_com_lista_vazia(self, db):
        """Sync com 0 produtos deve funcionar e retornar SyncResult zero."""
        source = Mock()
        source.get_all_products.return_value = []
        from app.domain.models.produto import Produto, ProdutoCodigo
        from app.domain.models.cache_status import CacheStatus

        service = SyncService(source, db, empresa_id=EMPRESA_ID)
        result = service.sync()

        assert result.produtos_count == 0
        assert result.codigos_count == 0
        # Deve ter criado um CacheStatus de sucesso
        cache_status = db.query(CacheStatus).order_by(CacheStatus.id.desc()).first()
        assert cache_status is not None
        assert cache_status.status == "sucesso"
        # Banco deve estar limpo
        assert db.query(Produto).count() == 0
        assert db.query(ProdutoCodigo).count() == 0

    def test_sync_com_erro_deve_chamar_sync_com_erro(self, db):
        """Sync com exceção no source deve chamar sync_com_erro e relançar."""
        source = Mock()
        source.get_all_products.side_effect = ValueError("Falha na fonte")

        service = SyncService(source, db, empresa_id=EMPRESA_ID)

        with pytest.raises(RuntimeError, match="Erro ao sincronizar dados do ERP"):
            service.sync()

        # sync_com_erro cria CacheStatus com status=erro
        from app.domain.models.cache_status import CacheStatus
        cache_status = db.query(CacheStatus).order_by(CacheStatus.id.desc()).first()
        assert cache_status is not None
        assert cache_status.status == "erro"
