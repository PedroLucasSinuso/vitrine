import os
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.sync_service import SyncService
from app.domain.models.empresa import Empresa
from app.domain.models.historico_preco import HistoricoPreco
from app.domain.models.produto import Produto, ProdutoCodigo
from app.infrastructure.db.database import Base
from vitrine_core.models.product import Product

EMPRESA_ID = 1
OUTRA_EMPRESA_ID = 2


def _engine_sqlite_com_fk():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _ligar_fk(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    return engine


def _engines():
    yield pytest.param(_engine_sqlite_com_fk, id="sqlite-fk")
    url = os.environ.get("TEST_DATABASE_URL")
    yield pytest.param(
        (lambda: create_engine(url)) if url else None,
        id="postgres",
        marks=pytest.mark.skipif(not url, reason="TEST_DATABASE_URL não definida"),
    )


@pytest.fixture(params=list(_engines()))
def db(request):
    engine = request.param()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine, autoflush=False)()
    sessao.add_all([
        Empresa(id=EMPRESA_ID, nome="Loja", slug="loja", status="ativa"),
        Empresa(id=OUTRA_EMPRESA_ID, nome="Outra", slug="outra", status="ativa"),
    ])
    sessao.commit()
    yield sessao
    sessao.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _produto(codigo, preco="10.00", barcodes=("789",), nome=None):
    return Product(
        internal_code=codigo,
        name=nome or f"Produto {codigo}",
        group="G",
        family="F",
        sale_price=Decimal(preco),
        cost_price=Decimal("5.00"),
        barcodes=list(barcodes),
    )


def _sincronizar(db, produtos, empresa_id=EMPRESA_ID):
    source = Mock()
    source.get_all_products.return_value = produtos
    return SyncService(source, db, empresa_id=empresa_id).sync()


def _historico(db, codigo, empresa_id=EMPRESA_ID):
    return db.scalars(
        select(HistoricoPreco).where(
            HistoricoPreco.empresa_id == empresa_id,
            HistoricoPreco.codigo_chamada == codigo,
        )
    ).all()


def test_sync_repetido_preserva_historico_de_preco(db):
    _sincronizar(db, [_produto("001", "10.00")])
    _sincronizar(db, [_produto("001", "12.00")])

    precos = sorted(h.preco_venda for h in _historico(db, "001"))
    assert precos == [10.0, 12.0]


def test_sync_atualiza_dados_do_produto_existente(db):
    _sincronizar(db, [_produto("001", "10.00", nome="Antigo")])
    _sincronizar(db, [_produto("001", "12.00", nome="Novo")])

    produto = db.get(Produto, (EMPRESA_ID, "001"))
    db.refresh(produto)
    assert produto.nome == "Novo"
    assert produto.preco_venda == 12.0


def test_sync_substitui_codigos_de_barras(db):
    _sincronizar(db, [_produto("001", barcodes=("111", "222"))])
    _sincronizar(db, [_produto("001", barcodes=("333",))])

    codigos = db.scalars(
        select(ProdutoCodigo.codigo).where(ProdutoCodigo.empresa_id == EMPRESA_ID)
    ).all()
    assert codigos == ["333"]


def test_produto_que_saiu_do_erp_e_removido_sem_afetar_os_demais(db):
    _sincronizar(db, [_produto("001"), _produto("002")])
    _sincronizar(db, [_produto("002")])

    assert db.get(Produto, (EMPRESA_ID, "001")) is None
    assert _historico(db, "001") == []
    assert len(_historico(db, "002")) == 2


def test_sync_de_uma_empresa_nao_toca_a_outra(db):
    _sincronizar(db, [_produto("001")], empresa_id=OUTRA_EMPRESA_ID)
    _sincronizar(db, [_produto("001")])
    _sincronizar(db, [])

    assert db.get(Produto, (OUTRA_EMPRESA_ID, "001")) is not None
    assert len(_historico(db, "001", empresa_id=OUTRA_EMPRESA_ID)) == 1


def test_fk_esta_ligada_no_banco_de_teste(db):
    if db.bind.dialect.name != "sqlite":
        pytest.skip("Postgres sempre aplica FK")
    assert db.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_historico_referencia_o_id_numerico_do_job_disparado(db):
    from datetime import datetime, timezone

    from app.domain.models.sync_job import SyncJob

    job = SyncJob(
        empresa_id=EMPRESA_ID,
        job_id="ae8a4f45",
        status="em_progresso",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()

    source = Mock()
    source.get_all_products.return_value = [_produto("001")]
    SyncService(source, db, empresa_id=EMPRESA_ID).sync(job_id="ae8a4f45")

    assert [h.sync_job_id for h in _historico(db, "001")] == [job.id]
