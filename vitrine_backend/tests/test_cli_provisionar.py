import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

from tests.bancos import _banco_isolado


def _url_sqlite(tmp_path):
    return f"sqlite:///{tmp_path / 'cli.db'}"


def _url_postgres(_tmp_path):
    return _banco_isolado(os.environ["TEST_DATABASE_URL"], "cli")


@pytest.fixture(params=[
    pytest.param(_url_sqlite, id="sqlite"),
    pytest.param(
        _url_postgres,
        id="postgres",
        marks=pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não definida"),
    ),
])
def url_banco(request, tmp_path):
    return request.param(tmp_path)


def _rodar(url, comando, *args):
    ambiente = {**os.environ, "DATABASE_URL": url, "SQLITE_URL": url}
    return subprocess.run(
        [sys.executable, "-m", "app.cli", comando, *args],
        env=ambiente, capture_output=True, text=True, timeout=120,
    )


def _empresa(url, slug):
    engine = create_engine(url)
    try:
        with engine.connect() as conexao:
            return conexao.execute(
                text("SELECT segmento, modo FROM empresas WHERE slug = :slug"), {"slug": slug}
            ).one_or_none()
    finally:
        engine.dispose()


def test_provisionar_sem_flags_cria_supermercado_legado(url_banco):
    resultado = _rodar(url_banco, "provisionar-empresa", "Mercado", "mercado", "admin.mercado", "Admin", "senha-forte")

    assert resultado.returncode == 0, resultado.stderr
    assert tuple(_empresa(url_banco, "mercado")) == ("supermercado", "legado")


def test_provisionar_com_segmento_e_modo(url_banco):
    resultado = _rodar(
        url_banco, "provisionar-empresa", "Loja", "loja", "admin.loja", "Admin", "senha-forte",
        "--segmento", "moda", "--modo", "upload",
    )

    assert resultado.returncode == 0, resultado.stderr
    assert tuple(_empresa(url_banco, "loja")) == ("moda", "upload")


def test_segmento_invalido_e_recusado(tmp_path):
    resultado = _rodar(
        _url_sqlite(tmp_path), "provisionar-empresa", "Loja", "loja", "admin.loja", "Admin", "senha",
        "--segmento", "farmacia",
    )

    assert resultado.returncode != 0
    assert "farmacia" in resultado.stderr


def test_help_da_demo_nao_provisiona(tmp_path):
    url = _url_sqlite(tmp_path)

    resultado = _rodar(url, "provisionar-demo", "--help")

    assert resultado.returncode == 0
    assert "usage" in resultado.stdout
    assert not (tmp_path / "cli.db").exists()
