import pytest

from app.application.importacao import ia
from app.core.config import settings
from tests.api.test_importacao import _cabecalho, _enviar
from tests.api.test_importacao_ia import _certo
from tests.importacao import relatorios as rel


@pytest.fixture(autouse=True)
def pasta_de_importacao(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "importacao_dir", str(tmp_path / "importacoes"))
    monkeypatch.setattr(ia, "ia_configurada", lambda: True)


@pytest.fixture
def moda(client, db_session):
    return _cabecalho(client, db_session, "loja-llm")


def _sequencia(monkeypatch, *respostas):
    chamadas = []
    fila = list(respostas)

    def sugerir(grade, erro_anterior=None, cliente=None, provedor=None):
        chamadas.append(erro_anterior)
        resposta = fila.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return ia.SugestaoIa(mapeamento=resposta, confianca="alta")

    monkeypatch.setattr(ia, "sugerir_mapeamento", sugerir)
    return chamadas


def test_resposta_invalida_gera_nova_tentativa_com_o_motivo(client, moda, monkeypatch):
    chamadas = _sequencia(monkeypatch, ia.RespostaInvalida("a resposta não é um JSON válido"), _certo())

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "pronto"
    assert chamadas == [None, "a resposta não é um JSON válido"]


def test_duas_respostas_invalidas_avisam_e_caem_no_manual(client, moda, monkeypatch):
    _sequencia(monkeypatch, ia.RespostaInvalida("um"), ia.RespostaInvalida("dois"))

    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()

    assert corpo["status"] == "aguardando_mapeamento"
    assert corpo["mapeamento"] is None
    assert corpo["sugestao_ia"]["erro"] == "A IA não conseguiu sugerir um mapeamento válido."
