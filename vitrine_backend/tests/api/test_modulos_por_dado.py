from datetime import date
from decimal import Decimal as D

import pytest

from app.application.importacao.persistencia import gravar_dataset
from app.domain.models.empresa import Empresa
from tests.api.conftest import get_token
from tests.api.test_perfil_empresa import _empresa_com_usuario
from vitrine_core.datasets.tipos import Operacao, TipoDataset

ITENS_BI = {"dashboard", "receita", "ranking", "curva_abc", "trocas", "temporal", "sku", "grade"}
PERIODO = {"data_inicio": "2026-09-01", "data_fim": "2026-09-30"}


def _perfil(client, username):
    token = get_token(client, username)
    return client.get("/empresa/perfil", headers={"Authorization": f"Bearer {token}"}).json()


def _importar_itens(db_session, empresa_id):
    item = {"documento": "1", "data": date(2026, 9, 1), "operacao": Operacao.VENDA, "quantidade": D("1"), "valor": D("10")}
    gravar_dataset(db_session, empresa_id, TipoDataset.ITENS_VENDA, (date(2026, 9, 1), date(2026, 9, 30)), [item], "i.xlsx")
    db_session.commit()


def test_segmento_equipe_so_tem_os_modulos_de_equipe(client, db_session):
    _empresa_com_usuario(db_session, "so-equipe", segmento="equipe", modo="upload")

    perfil = _perfil(client, "user.so-equipe")

    assert set(perfil["modulos"]) == {"equipe", "metas", "importacao"}
    assert perfil["segmento"] == "equipe"


def test_moda_em_upload_sem_itens_nao_tem_bi_de_vendas(client, db_session):
    _empresa_com_usuario(db_session, "moda-sem", segmento="moda", modo="upload")

    modulos = set(_perfil(client, "user.moda-sem")["modulos"])

    assert not modulos & ITENS_BI
    assert {"equipe", "metas", "importacao"} <= modulos


def test_moda_em_upload_liga_o_bi_quando_entrega_itens(client, db_session):
    empresa = _empresa_com_usuario(db_session, "moda-com", segmento="moda", modo="upload")
    _importar_itens(db_session, empresa.id)

    modulos = set(_perfil(client, "user.moda-com")["modulos"])

    assert ITENS_BI <= modulos


def test_excluir_os_itens_desliga_o_bi_de_novo(client, db_session):
    from sqlalchemy import select

    from app.application.importacao.persistencia import excluir_dataset
    from app.domain.models.importacao import Dataset

    empresa = _empresa_com_usuario(db_session, "moda-del", segmento="moda", modo="upload")
    _importar_itens(db_session, empresa.id)
    excluir_dataset(db_session, db_session.scalar(select(Dataset)))
    db_session.commit()

    assert not set(_perfil(client, "user.moda-del")["modulos"]) & ITENS_BI


def test_equipe_com_itens_continua_sem_o_bi_de_vendas(client, db_session):
    empresa = _empresa_com_usuario(db_session, "eq-itens", segmento="equipe", modo="upload")
    _importar_itens(db_session, empresa.id)

    assert not set(_perfil(client, "user.eq-itens")["modulos"]) & ITENS_BI


def test_modo_legado_nao_muda_com_ou_sem_dataset(client, db_session):
    _empresa_com_usuario(db_session, "legado", segmento="supermercado", modo="legado")

    assert ITENS_BI - {"grade"} <= set(_perfil(client, "user.legado")["modulos"])


def test_grade_so_responde_quando_ha_itens(client, db_session):
    empresa = _empresa_com_usuario(db_session, "grade", segmento="moda", modo="upload", role="supervisor")
    cabecalho = {"Authorization": f"Bearer {get_token(client, 'user.grade')}"}

    antes = client.get("/bi/grade", headers=cabecalho, params=PERIODO).status_code
    _importar_itens(db_session, empresa.id)
    depois = client.get("/bi/grade", headers=cabecalho, params=PERIODO).status_code

    assert (antes, depois) == (404, 200)
