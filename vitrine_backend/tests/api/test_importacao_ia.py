import pytest

from app.application.importacao import ia
from app.core.config import settings
from tests.api.test_importacao import _cabecalho, _enviar, _mapeamento
from tests.importacao import relatorios as rel


@pytest.fixture(autouse=True)
def pasta_de_importacao(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "importacao_dir", str(tmp_path / "importacoes"))


def _certo():
    return {**_mapeamento(rel.linha_cabecalho_vendedores()), "separador_decimal": ",", "formato_data": "dd/mm/aaaa"}


@pytest.fixture
def ia_falsa(monkeypatch):
    chamadas = []
    respostas = []

    def sugerir(grade, erro_anterior=None, cliente=None):
        chamadas.append(erro_anterior)
        resposta = respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return ia.SugestaoIa(mapeamento=resposta, confianca="alta", duvidas=["Confira a coluna de trocas."])

    monkeypatch.setattr(ia, "ia_configurada", lambda: True)
    monkeypatch.setattr(ia, "sugerir_mapeamento", sugerir)
    return chamadas, respostas


@pytest.fixture
def moda(client, db_session):
    return _cabecalho(client, db_session, "loja-ia")


def test_sugestao_da_ia_ja_chega_pronta_para_confirmar(client, moda, ia_falsa):
    chamadas, respostas = ia_falsa
    respostas.append(_certo())

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "pronto"
    assert corpo["previa"]["validacao"]["status"] == "conferido"
    assert corpo["sugestao_ia"] == {"confianca": "alta", "duvidas": ["Confira a coluna de trocas."], "erro": None}
    assert chamadas == [None]
    assert client.post(f"/importacoes/{corpo['id']}/confirmar", headers=moda).status_code == 201


def test_segunda_tentativa_recebe_o_erro_da_primeira(client, moda, ia_falsa):
    chamadas, respostas = ia_falsa
    respostas.extend([
        {**_certo(), "colunas": [{"indice": 0, "campo": "vendedor"}]},
        _certo(),
    ])

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "pronto"
    assert len(chamadas) == 2
    assert "obrigatórios" in chamadas[1]


def test_ia_fora_do_ar_cai_no_mapeamento_manual(client, moda, ia_falsa):
    _, respostas = ia_falsa
    respostas.append(ia.IaIndisponivel("Sem conexão com o serviço de IA."))

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "aguardando_mapeamento"
    assert corpo["mapeamento"] is None
    assert corpo["sugestao_ia"]["erro"] == "Sem conexão com o serviço de IA."


def test_cota_mensal_esgotada_nao_chama_a_ia(client, moda, ia_falsa, monkeypatch):
    chamadas, respostas = ia_falsa
    monkeypatch.setattr(settings, "ia_cota_mensal", 1)
    respostas.extend([ia.IaIndisponivel("x")])

    _enviar(client, moda, rel.vendedores_xlsx())
    segundo = _enviar(client, moda, rel.vendedores_xlsx(loja="OUTRA")).json()

    assert len(chamadas) == 1
    assert segundo["sugestao_ia"] is None


def test_demo_nunca_chama_a_ia(client, db_session, ia_falsa):
    chamadas, _ = ia_falsa
    demo = _cabecalho(client, db_session, "demo-moda")

    _enviar(client, demo, rel.vendedores_xlsx())

    assert chamadas == []


def test_template_conhecido_dispensa_a_ia(client, moda, ia_falsa):
    chamadas, respostas = ia_falsa
    respostas.append(_certo())
    primeiro = _enviar(client, moda, rel.vendedores_xlsx()).json()
    client.post(f"/importacoes/{primeiro['id']}/confirmar", headers=moda)

    segundo = _enviar(client, moda, rel.vendedores_xlsx(titulos_extras=1)).json()

    assert segundo["template_aplicado"] is True
    assert len(chamadas) == 1


def test_sem_ia_configurada_fluxo_manual_continua(client, moda, monkeypatch):
    monkeypatch.setattr(ia, "ia_configurada", lambda: False)

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "aguardando_mapeamento"
    assert corpo["sugestao_ia"] is None


def test_mapeamento_que_nao_le_nada_pede_correcao(client, moda, ia_falsa):
    chamadas, respostas = ia_falsa
    respostas.extend([{**_certo(), "linha_cabecalho": 14}, _certo()])

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "pronto"
    assert "nenhuma linha válida" in chamadas[1]
