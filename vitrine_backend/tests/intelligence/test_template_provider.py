"""Tests for the deterministic template provider (fallback)."""
from app.application.intelligence.providers.template import TemplateProvider


class TestTemplateProvider:
    def setup_method(self):
        self.provider = TemplateProvider()

    def test_sem_dados_retorna_resumo_vazio(self):
        """Sem dados macro nem detectores, retorna resumo informando que não há insights."""
        resultado = self.provider.sintetizar({}, {})
        assert resultado.resumo_executivo == "Nenhum insight relevante identificado no período."
        assert resultado.insights == []
        assert resultado.fonte == "deterministico"

    def test_com_encalhe_gera_insight(self):
        """Detector de encalhe populado deve gerar insight correspondente."""
        dados_macro = {"faturamento": 100000.0}
        dados_detectores = {
            "encalhes": [
                {"nome": "Produto A", "valor_estimado": 5000.0, "estoque": 10},
                {"nome": "Produto B", "valor_estimado": 3000.0, "estoque": 5},
            ]
        }
        resultado = self.provider.sintetizar(dados_macro, dados_detectores)
        assert len(resultado.insights) == 1
        insight = resultado.insights[0]
        assert insight.tipo == "encalhe"
        assert insight.metricas is not None
        assert insight.metricas.total_encalhados == 2
        assert insight.metricas.valor_total_encalhado == 8000.0
        assert "Produto A" in insight.descricao
        assert "Produto B" in insight.descricao

    def test_encalhe_alto_impacto_por_valor(self):
        """Valor total > 10k deve classificar como alto impacto."""
        dados_detectores = {
            "encalhes": [
                {"nome": "Carro", "valor_estimado": 15000.0, "estoque": 1},
            ]
        }
        resultado = self.provider.sintetizar({"faturamento": 50000.0}, dados_detectores)
        assert resultado.insights[0].impacto == "alto"

    def test_encalhe_medio_impacto(self):
        """Valor total < 10k deve classificar como médio impacto."""
        dados_detectores = {
            "encalhes": [
                {"nome": "Caneta", "valor_estimado": 500.0, "estoque": 10},
            ]
        }
        resultado = self.provider.sintetizar({"faturamento": 50000.0}, dados_detectores)
        assert resultado.insights[0].impacto == "medio"

    def test_macro_sem_faturamento_nao_exibe_no_resumo(self):
        """Se faturamento for 0 ou None, resumo não menciona faturamento."""
        resultado = self.provider.sintetizar({"faturamento": 0}, {})
        assert "Faturamento" not in resultado.resumo_executivo
