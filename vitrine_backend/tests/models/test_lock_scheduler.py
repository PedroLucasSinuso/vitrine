import os

import pytest
from sqlalchemy import create_engine

from app.infrastructure.db.bootstrap import adquirir_lock_postgres

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não definida"
)

CHAVE_TESTE = 991_001


def test_advisory_lock_so_permite_um_dono_por_vez():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        primeiro = adquirir_lock_postgres(engine, CHAVE_TESTE)
        segundo = adquirir_lock_postgres(engine, CHAVE_TESTE)
        assert primeiro is not None
        assert segundo is None

        primeiro.close()
        terceiro = adquirir_lock_postgres(engine, CHAVE_TESTE)
        assert terceiro is not None
        terceiro.close()
    finally:
        engine.dispose()
