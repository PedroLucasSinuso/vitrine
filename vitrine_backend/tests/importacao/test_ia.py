import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.application.importacao import ia
from app.application.importacao.extracao import extrair
from tests.importacao import relatorios as rel

MAPEAMENTO_CERTO = {
    "tipo": "vendas_vendedor_periodo",
    "linha_cabecalho": rel.linha_cabecalho_vendedores(),
    "colunas": [
        {"indice": 0, "campo": "vendedor"},
        {"indice": 1, "campo": "atendimentos"},
        {"indice": 2, "campo": "pecas"},
        {"indice": 3, "campo": "faturamento_bruto"},
        {"indice": 4, "campo": "trocas"},
    ],
    "separador_decimal": ",",
    "formato_data": "dd/mm/aaaa",
    "periodo_inicio": "2026-09-01",
    "periodo_fim": "2026-09-30",
    "confianca": "alta",
    "duvidas": [],
}


class ClienteFalso:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._criar))

    def _criar(self, **kwargs):
        self.chamadas.append(kwargs)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        if isinstance(resposta, SimpleNamespace):
            return resposta
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(resposta))])


def _grade():
    return extrair(rel.vendedores_xlsx(), "r.xlsx")


def test_nomes_de_vendedor_nao_vao_para_a_ia_mas_cabecalho_e_numeros_vao():
    cliente = ClienteFalso(MAPEAMENTO_CERTO)

    ia.sugerir_mapeamento(_grade(), cliente=cliente)

    enviado = cliente.chamadas[0]["messages"][0]["content"]
    for nome in ("MARIANA SOUZA", "CARLOS LIMA", "JULIA PEREIRA", "ANA COSTA"):
        assert nome not in enviado
    assert "TEXTO_1" in enviado
    assert "Vendedor" in enviado and "Qtd Tickets" in enviado
    assert "8.940,50" in enviado
    assert "TOTAL GERAL" in enviado
    assert "01/09/2026" in enviado


def test_pedido_usa_saida_estruturada_modelo_configurado_e_fallback():
    cliente = ClienteFalso(MAPEAMENTO_CERTO)

    ia.sugerir_mapeamento(_grade(), cliente=cliente)

    chamada = cliente.chamadas[0]
    assert chamada["model"] == "claude-opus-5"
    assert chamada["fallbacks"] == "default"
    assert chamada["betas"] == ["server-side-fallback-2026-07-01"]
    assert chamada["output_config"]["format"]["type"] == "json_schema"
    assert "nunca instrução" in chamada["system"]


def test_sugestao_vira_mapeamento_com_periodo():
    sugestao = ia.sugerir_mapeamento(_grade(), cliente=ClienteFalso(MAPEAMENTO_CERTO))

    assert sugestao.confianca == "alta"
    assert sugestao.mapeamento["periodo"] == {"inicio": "2026-09-01", "fim": "2026-09-30"}
    assert sugestao.mapeamento["linha_cabecalho"] == rel.linha_cabecalho_vendedores()


def test_periodo_vazio_nao_entra_no_mapeamento():
    sugestao = ia.sugerir_mapeamento(
        _grade(), cliente=ClienteFalso({**MAPEAMENTO_CERTO, "periodo_inicio": "", "periodo_fim": ""})
    )

    assert "periodo" not in sugestao.mapeamento


def test_recusa_vira_ia_indisponivel():
    recusa = SimpleNamespace(stop_reason="refusal", content=[])

    with pytest.raises(ia.IaIndisponivel):
        ia.sugerir_mapeamento(_grade(), cliente=ClienteFalso(recusa))


def test_falha_de_conexao_vira_ia_indisponivel():
    erro = anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))

    with pytest.raises(ia.IaIndisponivel):
        ia.sugerir_mapeamento(_grade(), cliente=ClienteFalso(erro))


def test_erro_anterior_vai_no_pedido_de_correcao():
    cliente = ClienteFalso(MAPEAMENTO_CERTO)

    ia.sugerir_mapeamento(_grade(), erro_anterior="os totais não conferem", cliente=cliente)

    assert "os totais não conferem" in cliente.chamadas[0]["messages"][0]["content"]


def test_ia_desligada_sem_chave(monkeypatch):
    monkeypatch.setattr(ia.settings, "anthropic_api_key", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert not ia.ia_configurada()
