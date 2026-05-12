import pytest
from contextlib import ExitStack
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pandas as pd
from fastapi.testclient import TestClient

from app.schemas.bi_schema import SkuDTO, PontoDiarioDTO, PontoHoraDTO


# --- Helpers de período -------------------------------------------------------

def _periodo_padrao() -> dict:
    return {
        "data_inicio": (date.today() - timedelta(days=30)).isoformat(),
        "data_fim": date.today().isoformat(),
    }


# --- DataFrames de mock -------------------------------------------------------

def _criar_df_vendas() -> pd.DataFrame:
    data_base = date.today() - timedelta(days=10)
    return pd.DataFrame([
        {
            "id_item": 1, "iddocumento": 100, "id_nfe": "NF001",
            "emissao": data_base, "hora": "14:30", "operacao": "V",
            "id_operacao": "VENDA", "cancelado": " ", "total_documento": 100.0,
            "tipo_devolucao": "", "grupo": "Eletronicos", "familia": "Smartphones",
            "codigo": "7891234567890", "produto": "Smartphone XYZ",
            "custo": 700.0, "venda": 999.99, "qtd_item": 1.0,
            "receita_produto": 999.99, "valor_unitario": 999.99,
        },
        {
            "id_item": 2, "iddocumento": 101, "id_nfe": "NF002",
            "emissao": data_base, "hora": "15:00", "operacao": "V",
            "id_operacao": "VENDA", "cancelado": " ", "total_documento": 200.0,
            "tipo_devolucao": "", "grupo": "Eletronicos", "familia": "Tablets",
            "codigo": "7891234567891", "produto": "Tablet ABC",
            "custo": 300.0, "venda": 499.99, "qtd_item": 2.0,
            "receita_produto": 999.98, "valor_unitario": 499.99,
        },
    ])


# --- Fixture de mock do BI ----------------------------------------------------

@pytest.fixture
def mock_bi():
    with ExitStack() as stack:
        mock_carregar = stack.enter_context(
            patch("app.api.routes.bi.carregar_fluxo")
        )
        MockRelatorio = stack.enter_context(
            patch("app.api.routes.bi.Relatorio")
        )
        MockMovimento = stack.enter_context(
            patch("app.api.routes.bi.RelatorioMovimento")
        )
        MockDiario = stack.enter_context(
            patch("app.api.routes.bi.RelatorioDiario")
        )
        MockTemporal = stack.enter_context(
            patch("app.api.routes.bi.RelatorioTemporal")
        )
        MockSku = stack.enter_context(
            patch("app.api.routes.bi.RelatorioSku")
        )

        mock_carregar.return_value = _criar_df_vendas()

        inst_rel = MagicMock()
        MockRelatorio.return_value = inst_rel
        inst_rel.kpis.return_value = MagicMock(
            model_dump=MagicMock(return_value={
                "faturamento_bruto": 2000.0,
                "faturamento_liquido": 1500.0,
                "total_trocas": 500.0,
                "qtd_tickets": 2,
                "ticket_medio": 1000.0,
                "itens_por_ticket": 1.5,
            })
        )
        inst_rel.por_dimensao.return_value = [
            {"grupo": "Eletronicos", "familia": "Smartphones", "produto": "Smartphone XYZ", "valor": 999.99},
        ]
        inst_rel.curva_abc.return_value = [
            {
                "grupo": "Eletronicos", "familia": "Smartphones", "produto": "Smartphone XYZ",
                "receita": 999.99, "participacao_pct": 50.0, "participacao_acumulada": 50.0, "curva": "A",
            },
        ]
        inst_rel.ranking.return_value = [
            {"codigo": "7891234567890", "produto": "Smartphone XYZ", "valor": 999.99},
        ]
        inst_rel.trocas_resumo.return_value = MagicMock(
            model_dump=MagicMock(return_value={
                "total_trocas": 500.0,
                "taxa_troca_pct": 25.0,
                "por_produto": [{"codigo": "7891234567890", "produto": "Smartphone XYZ", "receita": 999.99}],
            })
        )

        inst_mov = MagicMock()
        MockMovimento.return_value = inst_mov
        inst_mov.resumo.return_value = MagicMock(
            model_dump=MagicMock(return_value={
                "total": 50.0,
                "por_produto": [{"codigo": "7891234567890", "produto": "Smartphone XYZ", "receita": 50.0}],
            })
        )

        inst_diario = MagicMock()
        MockDiario.return_value = inst_diario
        inst_diario.serie_temporal.return_value = [{"data": "2026-05-01", "valor": 999.99}]
        inst_diario.serie_por_produto.return_value = [{"data": "2026-05-01", "valor": 999.99}]

        inst_temp = MagicMock()
        MockTemporal.return_value = inst_temp
        inst_temp.por_hora.return_value = [{"hora": "14", "valor": 999.99}]
        inst_temp.por_dia_semana.return_value = [{"dia_semana": "Segunda", "valor": 999.99}]

        inst_sku = MagicMock()
        MockSku.return_value = inst_sku
        inst_sku.resumo.return_value = SkuDTO(
            codigo="123456",
            produto="Smartphone XYZ",
            grupo="Eletronicos",
            familia="Smartphones",
            receita_total=999.99,
            qtd_total=1.0,
            qtd_tickets=1,
            ticket_medio=999.99,
            ranking_dias=[PontoDiarioDTO(data="2026-05-01", valor=999.99)],
            distribuicao_hora=[PontoHoraDTO(hora="14", valor=999.99)],
        )

        yield {
            "carregar_fluxo": mock_carregar,
            "relatorio": MockRelatorio,
            "movimento": MockMovimento,
            "diario": MockDiario,
            "temporal": MockTemporal,
            "sku": MockSku,
        }