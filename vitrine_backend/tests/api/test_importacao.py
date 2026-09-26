import pytest

from app.application.utils.security import hash_password
from app.core.config import settings
from app.domain.models.empresa import Empresa
from app.domain.models.importacao import DsVendaVendedorPeriodo
from app.domain.models.usuario import Usuario
from tests.api.conftest import get_token
from tests.importacao import relatorios as rel

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture(autouse=True)
def pasta_de_importacao(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "importacao_dir", str(tmp_path / "importacoes"))


def _cabecalho(client, db_session, slug, segmento="moda", modo="legado", role="supervisor"):
    empresa = Empresa(nome=slug, slug=slug, status="ativa", segmento=segmento, modo=modo)
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Usuario(
        username=f"{role}.{slug}", nome_exibicao=slug, role=role,
        hashed_password=hash_password("senha123"), empresa_id=empresa.id,
    ))
    db_session.commit()
    return {"Authorization": f"Bearer {get_token(client, f'{role}.{slug}')}"}


def _enviar(client, cabecalho, conteudo, nome="vendas.xlsx"):
    return client.post("/importacoes", headers=cabecalho, files={"arquivo": (nome, conteudo, XLSX)})


def _mapeamento(linha_cabecalho):
    return {
        "tipo": "vendas_vendedor_periodo",
        "linha_cabecalho": linha_cabecalho,
        "colunas": [
            {"indice": 0, "campo": "vendedor"},
            {"indice": 1, "campo": "atendimentos"},
            {"indice": 2, "campo": "pecas"},
            {"indice": 3, "campo": "faturamento_bruto"},
            {"indice": 4, "campo": "trocas"},
        ],
    }


@pytest.fixture
def moda(client, db_session):
    return _cabecalho(client, db_session, "loja-moda")


def test_fluxo_completo_do_mapeamento_manual_ate_a_equipe(client, moda):
    enviado = _enviar(client, moda, rel.vendedores_xlsx())
    assert enviado.status_code == 201
    corpo = enviado.json()
    assert corpo["status"] == "aguardando_mapeamento"
    assert corpo["template_aplicado"] is False
    assert corpo["grade"][0][0] == "RELATÓRIO DE VENDAS POR VENDEDOR"

    mapeado = client.put(
        f"/importacoes/{corpo['id']}/mapeamento", headers=moda,
        json=_mapeamento(rel.linha_cabecalho_vendedores()),
    ).json()
    assert mapeado["status"] == "pronto"
    assert mapeado["previa"]["validacao"]["status"] == "conferido"
    assert mapeado["previa"]["periodo"] == {"inicio": "2026-09-01", "fim": "2026-09-30"}
    assert mapeado["previa"]["total_registros"] == 4

    confirmado = client.post(f"/importacoes/{corpo['id']}/confirmar", headers=moda)
    assert confirmado.status_code == 201
    assert confirmado.json()["linhas"] == 4

    equipe = client.get("/bi/equipe", headers=moda, params={"data_inicio": "2026-09-01", "data_fim": "2026-09-30"}).json()
    assert [v["vendedor"] for v in equipe["vendedores"]] == ["MARIANA SOUZA", "JULIA PEREIRA", "CARLOS LIMA", "ANA COSTA"]
    assert equipe["loja"]["faturamento_bruto"] == 25658.70
    assert {i["indicador"] for i in equipe["indisponivel"]} == {"serie_diaria", "mix_categoria", "conversao_contatos"}


def test_segundo_relatorio_com_mesmo_layout_usa_o_template(client, moda, db_session):
    primeiro = _enviar(client, moda, rel.vendedores_xlsx()).json()
    client.put(f"/importacoes/{primeiro['id']}/mapeamento", headers=moda, json=_mapeamento(rel.linha_cabecalho_vendedores()))
    client.post(f"/importacoes/{primeiro['id']}/confirmar", headers=moda)

    outra_loja = _cabecalho(client, db_session, "outra-loja")
    segundo = _enviar(client, outra_loja, rel.vendedores_xlsx(titulos_extras=2, loja="TACO BOULEVARD")).json()

    assert segundo["template_aplicado"] is True
    assert segundo["status"] == "pronto"
    assert segundo["mapeamento"]["linha_cabecalho"] == rel.linha_cabecalho_vendedores(2)
    assert segundo["previa"]["validacao"]["status"] == "conferido"


def test_total_divergente_nao_confirma(client, moda):
    corpo = _enviar(client, moda, rel.vendedores_xlsx(total=("TOTAL GERAL", 155, 390, "1,00", "509,90"))).json()
    mapeado = client.put(f"/importacoes/{corpo['id']}/mapeamento", headers=moda, json=_mapeamento(rel.linha_cabecalho_vendedores())).json()

    assert mapeado["status"] == "divergente"
    assert client.post(f"/importacoes/{corpo['id']}/confirmar", headers=moda).status_code == 409


def test_mapeamento_invalido_retorna_422(client, moda):
    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()
    invalido = {"tipo": "vendas_vendedor_periodo", "linha_cabecalho": 5, "colunas": [{"indice": 0, "campo": "vendedor"}]}

    assert client.put(f"/importacoes/{corpo['id']}/mapeamento", headers=moda, json=invalido).status_code == 422


def test_arquivo_invalido_retorna_400(client, moda):
    assert _enviar(client, moda, b"GIF89a", nome="foto.gif").status_code == 400


def test_outra_empresa_nao_ve_a_importacao(client, moda, db_session):
    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()
    intrusa = _cabecalho(client, db_session, "intrusa")

    assert client.get(f"/importacoes/{corpo['id']}", headers=intrusa).status_code == 404
    assert client.post(f"/importacoes/{corpo['id']}/confirmar", headers=intrusa).status_code == 404


def test_excluir_dataset_apaga_as_linhas(client, moda, db_session):
    corpo = _enviar(client, moda, rel.vendedores_xlsx()).json()
    client.put(f"/importacoes/{corpo['id']}/mapeamento", headers=moda, json=_mapeamento(rel.linha_cabecalho_vendedores()))
    dataset = client.post(f"/importacoes/{corpo['id']}/confirmar", headers=moda).json()

    assert client.delete(f"/datasets/{dataset['id']}", headers=moda).status_code == 204
    assert client.get("/datasets", headers=moda).json() == []
    assert db_session.query(DsVendaVendedorPeriodo).count() == 0


def test_mesmo_arquivo_de_novo_avisa_duplicado(client, moda):
    conteudo = rel.vendedores_xlsx()
    primeiro = _enviar(client, moda, conteudo).json()
    client.put(f"/importacoes/{primeiro['id']}/mapeamento", headers=moda, json=_mapeamento(rel.linha_cabecalho_vendedores()))
    client.post(f"/importacoes/{primeiro['id']}/confirmar", headers=moda)

    segundo = _enviar(client, moda, conteudo).json()

    assert segundo["duplicado_de"] == primeiro["id"]


def test_supermercado_legado_nao_tem_importacao_mas_no_modo_upload_tem(client, db_session):
    legado = _cabecalho(client, db_session, "mercado", segmento="supermercado")
    upload = _cabecalho(client, db_session, "mercado-upload", segmento="supermercado", modo="upload")

    assert client.get("/importacoes", headers=legado).status_code == 404
    assert client.get("/importacoes", headers=upload).status_code == 200


def test_operador_nao_importa(client, db_session):
    operador = _cabecalho(client, db_session, "moda-op", role="operador")

    assert client.get("/importacoes", headers=operador).status_code == 403


def test_campos_por_tipo(client, moda):
    campos = client.get("/importacoes/campos", headers=moda).json()

    obrigatorios = {c["campo"] for c in campos["vendas_vendedor_periodo"] if c["obrigatorio"]}
    assert obrigatorios == {"vendedor", "faturamento_bruto", "atendimentos"}
