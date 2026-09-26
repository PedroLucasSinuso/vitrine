import pytest

from tests.test_cli_provisionar import _empresa, _rodar, _url_sqlite


def test_provisionar_empresa_do_segmento_equipe_em_modo_upload(tmp_path):
    url = _url_sqlite(tmp_path)

    resultado = _rodar(
        url, "provisionar-empresa", "Loja Taco", "loja-taco", "gerente.taco", "Gerente", "senha-forte",
        "--segmento", "equipe", "--modo", "upload",
    )

    assert resultado.returncode == 0, resultado.stderr
    assert tuple(_empresa(url, "loja-taco")) == ("equipe", "upload")
