"""Tests for the MacroContextoDetector.

Pattern: mock asyncio.run and calcular_kpis_rapido
to test each branch of insight generation.
"""
from datetime import date, datetime
from unittest.mock import patch, MagicMock
from app.application.intelligence.detectores.macro_contexto import (
    MacroContextoDetector,
    LIMITE_INSIGHTS,
)
from app.core.models.macro import MacroIndicator


def _make_indicador(
    chave: str, valor: float | None, disponivel: bool = True
) -> MacroIndicator:
    return MacroIndicator(
        chave=chave,
        rotulo=chave,
        valor=valor,
        disponivel=disponivel,
        unidade="%",
        periodo_ref="2026-04",
        periodo_ref_rotulo="Abr/2026",
        consultado_em=datetime(2026, 5, 27, 10, 0, 0),
        mensagem=None,
        tipo_fonte="bc_sgs",
    )


def _make_kpis(faturamento=100000.0, ticket_medio=50.0) -> MagicMock:
    k = MagicMock()
    k.faturamento_bruto = faturamento
    k.faturamento_liquido = faturamento * 0.9
    k.ticket_medio = ticket_medio
    k.qtd_tickets = int(faturamento / ticket_medio) if ticket_medio else 0
    k.total_trocas = 0.0
    k.itens_por_ticket = 2.5
    return k


class TestMacroContextoDetector:
    def setup_method(self):
        self.detector = MacroContextoDetector()
        self.hoje = date(2026, 5, 27)
        self.inicio = date(2026, 5, 1)
        self.fim = date(2026, 5, 27)
        self.patch_run = patch(
            "app.application.intelligence.detectores.macro_contexto.asyncio.run"
        )
        self.patch_kpis = patch(
            "app.application.intelligence.detectores.macro_contexto.calcular_kpis_rapido"
        )

    def _run(self, indicadores: dict, kpis=None, kpis_ant=None) -> list[dict]:
        """Helper to run the detector with mocked dependencies."""
        mock_run = self.patch_run.start()
        mock_run.return_value = indicadores
        mock_kpis = self.patch_kpis.start()
        # First call -> kpis, second -> kpis_ant
        mock_kpis.side_effect = [kpis, kpis_ant]
        try:
            source = MagicMock()
            return self.detector.detectar(
                MagicMock(), source, self.inicio, self.fim
            )
        finally:
            self.patch_run.stop()
            self.patch_kpis.stop()

    # ── Selic ──

    def test_selic_alta_gera_insight(self):
        """Selic acima de 10% deve gerar insight de capital de giro."""
        indicadores = {
            "selic_meta": _make_indicador("selic_meta", 14.75),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_selic" in tipos
        selic_insight = next(r for r in resultados if r["tipo"] == "macro_selic")
        assert selic_insight["valor_indicador"] == 14.75
        assert selic_insight["impacto"] == "alto"

    def test_selic_baixa_sem_insight(self):
        """Selic abaixo do limiar não deve gerar insight."""
        indicadores = {
            "selic_meta": _make_indicador("selic_meta", 5.0),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_selic" not in tipos

    # ── IPCA Alimentação vs Ticket ──

    def test_ipca_alto_ticket_baixo_gera_insight(self):
        """IPCA Alimentação alto com ticket crescendo abaixo deve gerar insight."""
        indicadores = {
            "ipca_alimentacao_12m": _make_indicador("ipca_alimentacao_12m", 8.5),
        }
        # ticket_medio anterior = 50, atual = 51.50 -> variação de 3%
        kpis = _make_kpis(ticket_medio=51.50)
        kpis_ant = _make_kpis(ticket_medio=50.0)
        resultados = self._run(indicadores, kpis=kpis, kpis_ant=kpis_ant)
        tipos = [r["tipo"] for r in resultados]
        assert "macro_ipca_ticket" in tipos

    def test_ipca_alto_mas_ticket_acompanha_sem_insight(self):
        """IPCA alto mas ticket crescendo acima não deve gerar insight."""
        indicadores = {
            "ipca_alimentacao_12m": _make_indicador("ipca_alimentacao_12m", 8.5),
        }
        # ticket_medio anterior = 50, atual = 54.50 -> variação de 9% > 8.5%
        kpis = _make_kpis(ticket_medio=54.50)
        kpis_ant = _make_kpis(ticket_medio=50.0)
        resultados = self._run(indicadores, kpis=kpis, kpis_ant=kpis_ant)
        tipos = [r["tipo"] for r in resultados]
        assert "macro_ipca_ticket" not in tipos

    def test_ipca_alto_mas_sem_kpis_ant_sem_insight(self):
        """Sem KPI do período anterior, não deve gerar insight de ticket."""
        indicadores = {
            "ipca_alimentacao_12m": _make_indicador("ipca_alimentacao_12m", 8.5),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=None)
        tipos = [r["tipo"] for r in resultados]
        assert "macro_ipca_ticket" not in tipos

    # ── IGP-M ──

    def test_igpm_alto_gera_insight(self):
        """IGP-M acima de 5% deve gerar insight de revisão de contratos."""
        indicadores = {
            "igpm_12m": _make_indicador("igpm_12m", 9.2),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_igpm" in tipos

    def test_igpm_baixo_sem_insight(self):
        """IGP-M abaixo do limiar não deve gerar insight."""
        indicadores = {
            "igpm_12m": _make_indicador("igpm_12m", 3.1),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_igpm" not in tipos

    # ── Desemprego ──

    def test_desemprego_alto_gera_insight(self):
        """Desemprego acima de 12% deve gerar insight de cautela."""
        indicadores = {
            "desemprego": _make_indicador("desemprego", 13.5),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_desemprego" in tipos

    def test_desemprego_baixo_sem_insight(self):
        """Desemprego abaixo do limiar não deve gerar insight."""
        indicadores = {
            "desemprego": _make_indicador("desemprego", 8.2),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_desemprego" not in tipos

    # ── IPCA Geral vs Faturamento ──

    def test_ipca_geral_alto_fat_baixo_gera_insight(self):
        """IPCA geral alto com faturamento crescendo abaixo deve gerar insight."""
        indicadores = {
            "ipca_12m": _make_indicador("ipca_12m", 5.5),
        }
        # faturamento anterior = 100000, atual = 103000 -> variação de 3% < 5.5%
        kpis = _make_kpis(faturamento=103000.0)
        kpis_ant = _make_kpis(faturamento=100000.0)
        resultados = self._run(indicadores, kpis=kpis, kpis_ant=kpis_ant)
        tipos = [r["tipo"] for r in resultados]
        assert "macro_ipca_geral" in tipos

    def test_ipca_geral_mas_fat_acompanha_sem_insight(self):
        """IPCA geral alto mas faturamento crescendo acima não gera insight."""
        indicadores = {
            "ipca_12m": _make_indicador("ipca_12m", 5.5),
        }
        # faturamento variou 8% > 5.5%
        kpis = _make_kpis(faturamento=108000.0)
        kpis_ant = _make_kpis(faturamento=100000.0)
        resultados = self._run(indicadores, kpis=kpis, kpis_ant=kpis_ant)
        tipos = [r["tipo"] for r in resultados]
        assert "macro_ipca_geral" not in tipos

    # ── Indicador indisponível ──

    def test_indicador_indisponivel_sem_insight(self):
        """Indicador com disponivel=False não deve gerar insight."""
        selic = _make_indicador("selic_meta", 14.75, disponivel=False)
        indicadores = {"selic_meta": selic}
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_selic" not in tipos

    def test_indicador_valor_none_sem_insight(self):
        """Indicador com valor=None não deve gerar insight."""
        selic = _make_indicador("selic_meta", None, disponivel=True)
        indicadores = {"selic_meta": selic}
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        tipos = [r["tipo"] for r in resultados]
        assert "macro_selic" not in tipos

    # ── Vazio / sem indicadores ──

    def test_todos_indisponiveis_retorna_vazio(self):
        """Quando todos indicadores têm disponivel=False, retorna lista vazia."""
        indicadores = {
            "selic_meta": _make_indicador("selic_meta", 14.75, disponivel=False),
            "ipca_alimentacao_12m": _make_indicador("ipca_alimentacao_12m", 8.5, disponivel=False),
            "igpm_12m": _make_indicador("igpm_12m", 9.2, disponivel=False),
            "desemprego": _make_indicador("desemprego", 13.5, disponivel=False),
            "ipca_12m": _make_indicador("ipca_12m", 5.5, disponivel=False),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        assert resultados == []

    def test_sem_indicadores_retorna_vazio(self):
        """Dict vazio de indicadores retorna lista vazia."""
        resultados = self._run({}, kpis=_make_kpis(), kpis_ant=_make_kpis())
        assert resultados == []

    # ── Limite de insights ──

    def test_limite_maximo_insights(self):
        """Quando todos os indicadores disparam, deve respeitar LIMITE_INSIGHTS."""
        indicadores = {
            "selic_meta": _make_indicador("selic_meta", 14.75),
            "ipca_alimentacao_12m": _make_indicador("ipca_alimentacao_12m", 8.5),
            "igpm_12m": _make_indicador("igpm_12m", 9.2),
            "desemprego": _make_indicador("desemprego", 13.5),
            "ipca_12m": _make_indicador("ipca_12m", 5.5),
        }
        # ticket cresce 3% (abaixo de 8.5%) e faturamento cresce 3% (abaixo de 5.5%)
        kpis = _make_kpis(faturamento=103000.0, ticket_medio=51.50)
        kpis_ant = _make_kpis(faturamento=100000.0, ticket_medio=50.0)
        resultados = self._run(indicadores, kpis=kpis, kpis_ant=kpis_ant)
        assert len(resultados) <= LIMITE_INSIGHTS

    # ── Dados do insight ──

    def test_insight_possui_campos_obrigatorios(self):
        """Cada insight deve conter os campos esperados pelo template provider."""
        indicadores = {
            "selic_meta": _make_indicador("selic_meta", 14.75),
        }
        resultados = self._run(indicadores, kpis=_make_kpis(), kpis_ant=_make_kpis())
        assert len(resultados) >= 1
        item = resultados[0]
        campos = {"tipo", "titulo", "descricao", "sugestao", "impacto",
                  "chave_indicador", "valor_indicador"}
        assert campos.issubset(item.keys()), f"Missing fields: {campos - set(item.keys())}"
        assert item["impacto"] in ("alto", "medio", "baixo")
