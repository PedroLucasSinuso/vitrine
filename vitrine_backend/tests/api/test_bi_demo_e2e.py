"""Ponta a ponta do modo demonstração.

Percorre as rotas de BI com o adapter de demo ligado e exige que nenhuma
volte vazia ou zerada. É o teste que responde, de forma executável, à
pergunta que motivou o adapter: "quem abrir a demo vê todas as telas
cheias?".

Vai de propósito pelo caminho real (deps → erp_factory → registry → demo),
sem substituir dependência: substituir a fonte aqui testaria o mock, não a
demonstração.
"""

from datetime import date, timedelta

import pytest

from app.api import deps
from app.application.config_cache import invalidate_cache
from app.domain.models.configuracao import Configuracao


@pytest.fixture
def cliente_demo(client, db_session, empresa_padrao, token_supervisor):
    """Aponta a empresa de teste para o adapter de demo."""
    db_session.add(
        Configuracao(empresa_id=empresa_padrao.id, chave="erp_adapter", valor="demo")
    )
    db_session.commit()
    # Ambos os caches são globais e sem expiração — sem limpar, o adapter e
    # a configuração de outro teste vazariam para este.
    invalidate_cache()
    deps.limpar_cache_adapters()
    yield client, {"Authorization": f"Bearer {token_supervisor}"}
    invalidate_cache()
    deps.limpar_cache_adapters()


@pytest.fixture
def periodo():
    fim = date.today()
    inicio = fim - timedelta(days=89)
    return {"data_inicio": inicio.isoformat(), "data_fim": fim.isoformat()}


def _get(cliente_demo, url, periodo, **extra):
    client, headers = cliente_demo
    resp = client.get(url, params={**periodo, **extra}, headers=headers)
    assert resp.status_code == 200, f"{url} -> {resp.status_code} {resp.text[:200]}"
    return resp.json()


class TestIndicadores:
    def test_kpis_nao_vem_zerados(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/kpis", periodo)
        assert dados["faturamento_bruto"] > 0
        assert dados["qtd_tickets"] > 0
        # Zero aqui denuncia document_total inconsistente entre as linhas.
        assert dados["ticket_medio"] > 0
        assert dados["itens_por_ticket"] > 0

    def test_comparativo_tem_o_periodo_anterior(self, cliente_demo, periodo):
        """Sem histórico de um ano atrás, cada indicador vem sem comparação."""
        dados = _get(cliente_demo, "/bi/kpis/comparativo", periodo)
        for indicador in ("faturamento_bruto", "qtd_tickets", "ticket_medio"):
            assert dados[indicador]["atual"] > 0
            assert dados[indicador]["anterior"] is not None, indicador
            assert dados[indicador]["variacao_pct"] is not None


class TestDimensoes:
    @pytest.mark.parametrize("dimensao", ["produto", "grupo", "familia"])
    def test_receita_por_dimensao(self, cliente_demo, periodo, dimensao):
        dados = _get(cliente_demo, "/bi/receita", periodo, dimensao=dimensao)
        assert len(dados) > 1, f"dimensão {dimensao} agrupou tudo numa linha só"
        assert all(i["valor"] > 0 for i in dados)

    def test_quantidade_por_grupo(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/quantidade", periodo, dimensao="grupo")
        assert len(dados) > 1

    def test_curva_abc_tem_as_tres_classes(self, cliente_demo, periodo):
        """Com receita mal distribuída a curva degenera numa classe só."""
        dados = _get(cliente_demo, "/bi/curva-abc", periodo, dimensao="produto")
        classes = {i["curva"] for i in dados}
        assert classes == {"A", "B", "C"}
        assert sum(1 for i in dados if i["curva"] == "A") >= 5

    def test_ranking_preenchido(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/ranking", periodo, top=10)
        assert len(dados) == 10
        valores = [i["valor"] for i in dados]
        assert valores == sorted(valores, reverse=True)


class TestMovimentos:
    def test_trocas(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/trocas", periodo)
        assert dados["total_trocas"] > 0
        assert dados["por_produto"]

    @pytest.mark.parametrize("rota", ["/bi/perdas", "/bi/consumo"])
    def test_perdas_e_consumo(self, cliente_demo, periodo, rota):
        """Ambos descartam movimento sem documento comprobatório."""
        dados = _get(cliente_demo, rota, periodo)
        assert dados["total"] > 0
        assert dados["por_produto"]


class TestSeries:
    def test_serie_diaria(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/diario", periodo)
        assert len(dados) > 30
        assert any(p["valor"] > 0 for p in dados)

    def test_comparativo_diario_tem_referencia(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/diario/comparativo", periodo)
        assert dados["valor_offset"] is not None

    def test_distribuicao_por_hora(self, cliente_demo, periodo):
        """Horário nulo viraria um balde chamado 'No'."""
        dados = _get(cliente_demo, "/bi/temporal/hora", periodo)
        assert len(dados) >= 8
        horas = {p["hora"] for p in dados}
        assert all(h.isdigit() for h in horas), horas
        assert all(7 <= int(h) <= 21 for h in horas), horas  # horário da loja

    def test_distribuicao_por_dia_da_semana(self, cliente_demo, periodo):
        dados = _get(cliente_demo, "/bi/temporal/dia-semana", periodo)
        assert len(dados) == 7


class TestProduto:
    def test_analise_de_sku(self, cliente_demo, periodo):
        """404 aqui significa que o produto não vendeu no período."""
        from app.adapters.demo.catalog import CATALOGO

        client, headers = cliente_demo
        # O primeiro do catálogo é popular o bastante para vender sempre.
        codigo = CATALOGO[0].internal_code
        resp = client.get(
            "/bi/sku", params={**periodo, "codigo": codigo}, headers=headers
        )
        assert resp.status_code == 200, resp.text[:200]
        assert resp.json()["receita_total"] > 0


class TestExportacao:
    @pytest.mark.parametrize(
        "relatorio", ["kpis", "receita", "curva-abc", "ranking", "trocas", "diario"]
    )
    def test_exporta_excel(self, cliente_demo, periodo, relatorio):
        client, headers = cliente_demo
        resp = client.get(
            "/bi/exportar/excel",
            params={**periodo, "relatorio": relatorio},
            headers=headers,
        )
        assert resp.status_code == 200, f"{relatorio}: {resp.text[:200]}"
        assert resp.content[:2] == b"PK"  # assinatura de xlsx
