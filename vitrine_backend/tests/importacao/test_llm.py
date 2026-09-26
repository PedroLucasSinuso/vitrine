import json

import httpx
import pytest

from app.application.importacao import ia
from app.application.importacao.aplicacao import aplicar
from app.application.importacao.extracao import extrair
from app.application.importacao.llm import fabrica
from app.application.importacao.llm.anthropic_provedor import AnthropicProvedor
from app.application.importacao.llm.erros import IaIndisponivel, RespostaInvalida
from app.application.importacao.llm.openai_compativel import (
    OpenAiCompativelProvedor,
    esquecer_modos_aprendidos,
)
from app.application.importacao.mapeamento import Mapeamento
from tests.importacao import relatorios as rel

MISTRAL = "https://api.mistral.ai/v1"
ESQUEMA = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"], "additionalProperties": False}


@pytest.fixture(autouse=True)
def esquecer():
    esquecer_modos_aprendidos()
    yield
    esquecer_modos_aprendidos()


def _http(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _resposta(conteudo, motivo="stop"):
    return httpx.Response(200, json={"choices": [{"message": {"content": conteudo}, "finish_reason": motivo}]})


def _provedor(handler, modo="auto", modelo="open-mistral-nemo", chave="segredo", base=MISTRAL):
    return OpenAiCompativelProvedor(modelo=modelo, base_url=base, api_key=chave, modo=modo, cliente_http=_http(handler))


def test_pedido_usa_o_endpoint_compativel_com_bearer_e_json_schema():
    vistos = []

    def handler(requisicao):
        vistos.append((str(requisicao.url), requisicao.headers, json.loads(requisicao.content)))
        return _resposta('{"a": "x"}')

    texto = _provedor(handler).gerar_json("SISTEMA", "USUARIO", ESQUEMA)

    url, cabecalhos, corpo = vistos[0]
    assert texto == '{"a": "x"}'
    assert url == "https://api.mistral.ai/v1/chat/completions"
    assert cabecalhos["authorization"] == "Bearer segredo"
    assert corpo["model"] == "open-mistral-nemo"
    assert corpo["temperature"] == 0
    assert [m["role"] for m in corpo["messages"]] == ["system", "user"]
    assert corpo["messages"][1]["content"] == "USUARIO"
    assert corpo["response_format"]["type"] == "json_schema"
    assert corpo["response_format"]["json_schema"]["schema"] == ESQUEMA


def test_sem_chave_nao_manda_authorization_para_servidor_local():
    vistos = []

    def handler(requisicao):
        vistos.append(requisicao.headers)
        return _resposta("{}")

    _provedor(handler, chave="", base="http://localhost:11434/v1/").gerar_json("s", "u", ESQUEMA)

    assert "authorization" not in vistos[0]


def test_cai_de_json_schema_para_json_object_e_embute_o_schema_no_prompt():
    formatos = []

    def handler(requisicao):
        corpo = json.loads(requisicao.content)
        formatos.append(corpo.get("response_format", {}).get("type"))
        if corpo["response_format"]["type"] == "json_schema":
            return httpx.Response(400, json={"message": "response_format json_schema não suportado"})
        assert "JSON Schema" in corpo["messages"][0]["content"]
        assert '"additionalProperties"' in corpo["messages"][0]["content"]
        return _resposta('{"a": "ok"}')

    assert _provedor(handler).gerar_json("SISTEMA", "u", ESQUEMA) == '{"a": "ok"}'
    assert formatos == ["json_schema", "json_object"]


def test_ultimo_recurso_e_o_prompt_puro_sem_response_format():
    formatos = []

    def handler(requisicao):
        corpo = json.loads(requisicao.content)
        formatos.append(corpo.get("response_format", {}).get("type"))
        return _resposta("{}") if "response_format" not in corpo else httpx.Response(422, json={})

    _provedor(handler).gerar_json("s", "u", ESQUEMA)

    assert formatos == ["json_schema", "json_object", None]


def test_lembra_o_modo_que_funcionou_e_nao_repete_as_tentativas():
    chamadas = []

    def handler(requisicao):
        corpo = json.loads(requisicao.content)
        chamadas.append(corpo.get("response_format", {}).get("type"))
        return httpx.Response(400) if corpo["response_format"]["type"] == "json_schema" else _resposta("{}")

    provedor = _provedor(handler)
    provedor.gerar_json("s", "u", ESQUEMA)
    provedor.gerar_json("s", "u", ESQUEMA)

    assert chamadas == ["json_schema", "json_object", "json_object"]


def test_modo_fixo_nao_tenta_os_outros():
    chamadas = []

    def handler(requisicao):
        chamadas.append(1)
        return httpx.Response(400)

    with pytest.raises(IaIndisponivel):
        _provedor(handler, modo="json_schema").gerar_json("s", "u", ESQUEMA)

    assert len(chamadas) == 1


def test_todos_os_modos_recusados_vira_ia_indisponivel():
    with pytest.raises(IaIndisponivel, match="modelo e o endereço"):
        _provedor(lambda r: httpx.Response(400)).gerar_json("s", "u", ESQUEMA)


@pytest.mark.parametrize("status, trecho", [
    (401, "credencial"), (403, "credencial"), (429, "ocupado"), (500, "indisponível"), (404, "recusou"),
])
def test_erros_http_viram_mensagens_claras_sem_vazar_a_chave(status, trecho):
    with pytest.raises(IaIndisponivel, match=trecho) as erro:
        _provedor(lambda r: httpx.Response(status, text="detalhe interno")).gerar_json("s", "u", ESQUEMA)

    assert "segredo" not in str(erro.value)


def test_queda_de_rede_vira_ia_indisponivel():
    def handler(requisicao):
        raise httpx.ConnectError("sem rota", request=requisicao)

    with pytest.raises(IaIndisponivel, match="Sem conexão"):
        _provedor(handler).gerar_json("s", "u", ESQUEMA)


def test_resposta_cortada_ou_filtrada_nao_e_aceita():
    with pytest.raises(IaIndisponivel, match="incompleta"):
        _provedor(lambda r: _resposta('{"a":', "length")).gerar_json("s", "u", ESQUEMA)
    with pytest.raises(IaIndisponivel):
        _provedor(lambda r: _resposta("x", "content_filter")).gerar_json("s", "u", ESQUEMA)


@pytest.mark.parametrize("corpo", [{}, {"choices": []}, {"choices": [{"message": {}}]}, {"choices": [{"message": {"content": "  "}}]}])
def test_formato_inesperado_ou_vazio_e_resposta_invalida(corpo):
    with pytest.raises(RespostaInvalida):
        _provedor(lambda r: httpx.Response(200, json=corpo)).gerar_json("s", "u", ESQUEMA)


def test_conteudo_em_partes_e_concatenado():
    partes = [{"type": "text", "text": '{"a":'}, {"type": "text", "text": ' "x"}'}]

    assert _provedor(lambda r: _resposta(partes)).gerar_json("s", "u", ESQUEMA) == '{"a": "x"}'


RESPOSTA_DESCUIDADA_DE_MODELO_PEQUENO = """Claro! Aqui está o mapeamento:
```json
{
  "tipo": "vendas_vendedor_periodo",
  "linha_cabecalho": "5",
  "colunas": [
    {"indice": "0", "campo": "vendedor"},
    {"indice": 1, "campo": "atendimentos"},
    {"indice": 2, "campo": "pecas"},
    {"indice": 3, "campo": "faturamento_bruto"},
    {"indice": 4, "campo": "trocas"}
  ],
  "ignorar_linhas_com": "Total",
  "separador_decimal": ",",
  "formato_data": "DD/MM/YYYY",
  "periodo_inicio": null,
  "periodo_fim": null,
  "confianca": "Média",
  "duvidas": null
}
```
Espero ter ajudado!"""


def test_resposta_descuidada_de_modelo_pequeno_e_aceita_e_fecha_o_total():
    grade = extrair(rel.vendedores_xlsx(), "r.xlsx")
    provedor = _provedor(lambda r: _resposta(RESPOSTA_DESCUIDADA_DE_MODELO_PEQUENO))

    sugestao = ia.sugerir_mapeamento(grade, provedor=provedor)
    resultado = aplicar(grade, Mapeamento(**sugestao.mapeamento))

    assert sugestao.confianca == "media"
    assert sugestao.mapeamento["linha_cabecalho"] == 5
    assert sugestao.mapeamento["formato_data"] == "dd/mm/aaaa"
    assert sugestao.duvidas == []
    assert resultado.validacao.status == "conferido"
    assert resultado.periodo == rel.PERIODO_SETEMBRO
    assert resultado.confirmavel


@pytest.mark.parametrize("texto", ["não sei responder", "{quebrado", '{"tipo": "vendas_vendedor_periodo"}', "[1, 2]"])
def test_resposta_que_nao_e_um_mapeamento_e_invalida(texto):
    grade = extrair(rel.vendedores_xlsx(), "r.xlsx")

    with pytest.raises(RespostaInvalida):
        ia.sugerir_mapeamento(grade, provedor=_provedor(lambda r: _resposta(texto)))


def test_mensagem_ao_modelo_numera_colunas_e_traz_exemplo_sem_vazar_nomes():
    vistos = []

    def handler(requisicao):
        vistos.append(json.loads(requisicao.content))
        return _resposta(RESPOSTA_DESCUIDADA_DE_MODELO_PEQUENO)

    ia.sugerir_mapeamento(extrair(rel.vendedores_xlsx(), "r.xlsx"), provedor=_provedor(handler))

    corpo = vistos[0]
    usuario = corpo["messages"][1]["content"]
    assert "c0=Vendedor | c1=Qtd Tickets" in usuario
    assert "MARIANA SOUZA" not in usuario
    assert "Exemplo" in corpo["messages"][0]["content"]
    assert '"linha_cabecalho": 2' in corpo["messages"][0]["content"]


@pytest.fixture
def configuracao(monkeypatch):
    def definir(**valores):
        base = dict(ia_importacao_habilitada=True, ia_provedor="anthropic", ia_modelo="", ia_api_key="", ia_base_url="",
                    anthropic_api_key="", ia_modo_json="auto", ia_timeout_segundos=90)
        for chave, valor in {**base, **valores}.items():
            monkeypatch.setattr(fabrica.settings, chave, valor)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    return definir


def test_anthropic_e_o_padrao_e_usa_o_modelo_padrao(configuracao):
    configuracao(anthropic_api_key="k")

    provedor = fabrica.criar_provedor()

    assert fabrica.configurado()
    assert isinstance(provedor, AnthropicProvedor)
    assert (provedor.nome, provedor.modelo) == ("anthropic", "claude-opus-5")
    assert fabrica.modelo_efetivo() == "claude-opus-5"


def test_anthropic_aceita_a_chave_generica(configuracao):
    configuracao(ia_api_key="generica")

    assert fabrica.configurado()


def test_mistral_por_openai_compativel(configuracao):
    configuracao(ia_provedor="openai", ia_base_url=MISTRAL, ia_api_key="k", ia_modelo="open-mistral-nemo")

    provedor = fabrica.criar_provedor()

    assert fabrica.configurado()
    assert isinstance(provedor, OpenAiCompativelProvedor)
    assert (provedor.nome, provedor.modelo) == ("openai", "open-mistral-nemo")
    assert provedor._url == "https://api.mistral.ai/v1/chat/completions"


def test_openai_so_com_chave_usa_o_endereco_da_openai(configuracao):
    configuracao(ia_provedor="OpenAI", ia_api_key="k", ia_modelo="gpt-4o-mini")

    assert fabrica.criar_provedor()._url == "https://api.openai.com/v1/chat/completions"


def test_servidor_local_sem_chave(configuracao):
    configuracao(ia_provedor="openai", ia_base_url="http://localhost:11434/v1", ia_modelo="mistral-nemo")

    assert fabrica.configurado()


@pytest.mark.parametrize("valores", [
    {"ia_provedor": "openai", "ia_api_key": "k"},
    {"ia_provedor": "openai", "ia_modelo": "m"},
    {"ia_provedor": "gemini", "ia_api_key": "k", "ia_modelo": "m"},
    {"ia_importacao_habilitada": False, "anthropic_api_key": "k"},
    {},
], ids=["sem-modelo", "sem-endereco-nem-chave", "provedor-desconhecido", "desligada", "anthropic-sem-chave"])
def test_configuracao_incompleta_deixa_a_ia_desligada(configuracao, valores):
    configuracao(**valores)

    assert not fabrica.configurado()
    if valores.get("ia_provedor") in ("openai", "gemini"):
        with pytest.raises(IaIndisponivel):
            fabrica.criar_provedor()


def test_marcadores_do_modelo_somam_aos_padroes_e_nao_os_substituem():
    grade = extrair(rel.vendedores_xlsx(), "r.xlsx")
    resposta = json.loads(EXEMPLO_MINIMO)

    sugestao = ia.sugerir_mapeamento(grade, provedor=_provedor(lambda r: _resposta(json.dumps({**resposta, "ignorar_linhas_com": ["Emitido"]}))))

    assert {"Emitido", "subtotal", "total"} <= set(sugestao.mapeamento["ignorar_linhas_com"])


EXEMPLO_MINIMO = json.dumps({
    "tipo": "vendas_vendedor_periodo", "linha_cabecalho": 5,
    "colunas": [{"indice": 0, "campo": "vendedor"}, {"indice": 1, "campo": "atendimentos"}, {"indice": 3, "campo": "faturamento_bruto"}],
})
