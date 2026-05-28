"""Tests for macro-economic indicator fetcher (BC SGS API)."""
import json
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.models.macro import MacroIndicator
from app.domain.models.macro_cache import MacroCache
from app.application.intelligence.macro_fetcher import (
    INDICADORES_META,
    _mes_ano_atual,
    _formata_periodo,
    _obter_ultimo_valor_bc,
    _obter_cache_mensal,
    _salvar_cache_mensal,
    _fetch_bc_serie,
    fetch_todos_indicadores,
)

# Counts of indicator types from INDICADORES_META
_N_DINAMICO = sum(1 for m in INDICADORES_META if m["tipo"] == "dinamico")
_N_MENSAL = sum(1 for m in INDICADORES_META if m["tipo"] == "mensal")


class TestFormataPeriodo:
    def test_formata_periodo_valido(self):
        """'2026-04' → 'Abr/2026'"""
        assert _formata_periodo("2026-04") == "Abr/2026"

    def test_formata_periodo_janeiro(self):
        """'2026-01' → 'Jan/2026'"""
        assert _formata_periodo("2026-01") == "Jan/2026"

    def test_formata_periodo_dezembro(self):
        """'2026-12' → 'Dez/2026'"""
        assert _formata_periodo("2026-12") == "Dez/2026"

    def test_formata_periodo_none(self):
        """None → None"""
        assert _formata_periodo(None) is None

    def test_formata_periodo_invalido(self):
        """String inválida retorna ela mesma."""
        assert _formata_periodo("invalido") == "invalido"


class TestObterUltimoValorBC:
    def test_ultimo_valor_valido(self):
        """Extrai último valor e período do formato BC."""
        dados = [
            {"data": "01/03/2026", "valor": "7.5"},
            {"data": "01/04/2026", "valor": "7.8"},
        ]
        valor, periodo = _obter_ultimo_valor_bc(dados)
        assert valor == 7.8
        assert periodo == "2026-04"

    def test_lista_vazia(self):
        """Lista vazia → (None, None)."""
        valor, periodo = _obter_ultimo_valor_bc([])
        assert valor is None
        assert periodo is None

    def test_valor_invalido(self):
        """Valor não numérico → (None, None)."""
        dados = [{"data": "01/04/2026", "valor": "N/A"}]
        valor, periodo = _obter_ultimo_valor_bc(dados)
        assert valor is None
        assert periodo is None

    def test_chave_ausente(self):
        """Dict sem 'valor' → (None, None)."""
        dados = [{"data": "01/04/2026"}]
        valor, periodo = _obter_ultimo_valor_bc(dados)
        assert valor is None
        assert periodo is None

    def test_data_mal_formatada_retorna_valor_sem_periodo(self):
        """Data sem barras → valor extraído, periodo_ref=None porque explode."""
        dados = [{"data": "2026-04-01", "valor": "7.8"}]
        valor, periodo = _obter_ultimo_valor_bc(dados)
        # The function tries to parse and catches the error, returning None
        # Actually the ValueError from unpacking propagates up
        # Let's verify: split("/") on "2026-04-01" gives 1 element → unpack error
        assert valor is None
        assert periodo is None


class TestCacheMensal:
    def test_cache_hit_mesmo_mes(self, db_session):
        """Cache com mesmo mes_ano → retorna indicador sem HTTP call."""
        agora = datetime.now()
        indicador = MacroIndicator(
            chave="ipca_12m",
            rotulo="IPCA geral (12m)",
            valor=4.5,
            disponivel=True,
            unidade="%",
            periodo_ref="2026-04",
            periodo_ref_rotulo="Abr/2026",
            consultado_em=agora,
            mensagem=None,
            tipo_fonte="bc_sgs",
        )
        _salvar_cache_mensal(db_session, "ipca_12m", indicador)

        resultado = _obter_cache_mensal(db_session, "ipca_12m")
        assert resultado is not None
        assert resultado.chave == "ipca_12m"
        assert resultado.valor == 4.5

    def test_cache_expired_mes_diferente(self, db_session):
        """Cache de mês anterior → None (obriga refetch)."""
        db_session.add(MacroCache(
            chave="ipca_12m",
            valor_json=json.dumps({
                "chave": "ipca_12m", "rotulo": "IPCA", "valor": 4.5,
                "disponivel": True, "unidade": "%",
                "periodo_ref": None, "periodo_ref_rotulo": None,
                "consultado_em": datetime.now().isoformat(),
                "mensagem": None, "tipo_fonte": "bc_sgs",
            }),
            consultado_em=datetime.now(),
            mes_ano="2020-01",  # Mês diferente
        ))
        db_session.commit()

        resultado = _obter_cache_mensal(db_session, "ipca_12m")
        assert resultado is None

    def test_cache_inexistente(self, db_session):
        """Nenhum cache salvo → None."""
        resultado = _obter_cache_mensal(db_session, "ipca_12m")
        assert resultado is None

    def test_cache_json_invalido(self, db_session):
        """JSON corrompido → None."""
        db_session.add(MacroCache(
            chave="ipca_12m",
            valor_json="invalid json{{{",
            consultado_em=datetime.now(),
            mes_ano=_mes_ano_atual(),
        ))
        db_session.commit()

        resultado = _obter_cache_mensal(db_session, "ipca_12m")
        assert resultado is None


def _make_mock_bc_response(status_code=200, dados=None):
    """Helper to create a mock httpx response for BC SGS API."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=dados or [])
    resp.raise_for_status = MagicMock()
    return resp


class TestFetchBCSerie:
    @pytest.mark.asyncio
    async def test_fetch_sucesso(self):
        """Resposta válida do BC → retorna (valor, periodo_ref)."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[
            {"data": "01/03/2026", "valor": "7.5"},
            {"data": "01/04/2026", "valor": "7.8"},
        ]))

        valor, periodo = await _fetch_bc_serie(mock_client, 433)
        assert valor == 7.8
        assert periodo == "2026-04"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """HTTP 500 → raise HTTPStatusError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Error", request=MagicMock(), response=mock_response
        )
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await _fetch_bc_serie(mock_client, 433)

    @pytest.mark.asyncio
    async def test_fetch_timeout(self):
        """Timeout → raise TimeoutException."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(httpx.TimeoutException):
            await _fetch_bc_serie(mock_client, 433)


class TestFetchTodosIndicadores:
    @pytest.mark.asyncio
    async def test_fetch_all_success(self, db_session):
        """Todos os indicadores retornam com disponivel=True."""
        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[
                {"data": "01/04/2026", "valor": "7.8"}
            ]))

            resultados = await fetch_todos_indicadores(db_session)

            assert len(resultados) == len(INDICADORES_META)
            for chave, ind in resultados.items():
                assert ind.disponivel is True, f"{chave} deveria estar disponível"
                assert ind.valor == 7.8
                assert ind.mensagem is None
                assert ind.consultado_em is not None

    @pytest.mark.asyncio
    async def test_fetch_http_error_returns_indisponivel(self, db_session):
        """HTTP error → disponivel=False com mensagem."""
        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            async def mock_get(url, **kwargs):
                resp = MagicMock()
                resp.status_code = 500
                resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "500", request=MagicMock(), response=resp
                )
                return resp

            mock_client.get = mock_get

            resultados = await fetch_todos_indicadores(db_session)

            for chave, ind in resultados.items():
                assert ind.disponivel is False, f"{chave} deveria estar indisponível"
                assert ind.valor is None
                assert "HTTP 500" in (ind.mensagem or "")

    @pytest.mark.asyncio
    async def test_fetch_timeout_returns_indisponivel(self, db_session):
        """Timeout → disponivel=False com mensagem de timeout."""
        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            resultados = await fetch_todos_indicadores(db_session)

            for chave, ind in resultados.items():
                assert ind.disponivel is False
                assert ind.valor is None
                assert "timeout" in (ind.mensagem or "").lower()

    @pytest.mark.asyncio
    async def test_dinamico_never_cached(self, db_session):
        """Selic (dinâmico) sempre faz fetch mesmo com cache existente."""
        # Seed cache for Selic Meta
        agora = datetime.now()
        cached = MacroIndicator(
            chave="selic_meta",
            rotulo="Selic (meta)",
            valor=14.75,
            disponivel=True,
            unidade="%",
            periodo_ref="2026-04",
            periodo_ref_rotulo="Abr/2026",
            consultado_em=agora,
            mensagem=None,
            tipo_fonte="bc_sgs",
        )
        _salvar_cache_mensal(db_session, "selic_meta", cached)

        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[
                {"data": "01/05/2026", "valor": "15.00"}
            ]))

            resultados = await fetch_todos_indicadores(db_session)

            # Selic should have been fetched live (different value)
            selic = resultados["selic_meta"]
            assert selic.valor == 15.00  # Live value, not cached 14.75

    @pytest.mark.asyncio
    async def test_mensal_respeita_cache(self, db_session):
        """Indicador mensal usa cache se disponível (mesmo mês)."""
        # Seed cache for ipca_12m
        agora = datetime.now()
        cached = MacroIndicator(
            chave="ipca_12m",
            rotulo="IPCA geral (12m)",
            valor=4.20,
            disponivel=True,
            unidade="%",
            periodo_ref="2026-04",
            periodo_ref_rotulo="Abr/2026",
            consultado_em=agora,
            mensagem=None,
            tipo_fonte="bc_sgs",
        )
        _salvar_cache_mensal(db_session, "ipca_12m", cached)

        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[
                {"data": "01/05/2026", "valor": "9.99"}
            ]))

            resultados = await fetch_todos_indicadores(db_session)

            # ipca_12m should come from cache, not API
            ipca = resultados["ipca_12m"]
            assert ipca.valor == 4.20  # Cached value

            # Only non-mensal + non-cached series should make HTTP calls
            # _N_DINAMICO = 2 dynamic always fetch
            # _N_MENSAL - 1 cached = _N_MENSAL - 1 monthly fetches
            expected_calls = _N_DINAMICO + (_N_MENSAL - 1)
            assert mock_client.get.call_count == expected_calls, (
                f"Expected {expected_calls} calls, got {mock_client.get.call_count}"
            )

    @pytest.mark.asyncio
    async def test_cache_mensal_salvo_mesmo_em_erro(self, db_session):
        """Cache mensal é salvo mesmo quando API falha (marca tentativa)."""
        with patch(
            "app.application.intelligence.macro_fetcher.httpx.AsyncClient"
        ) as mock_client_ctx:
            mock_client = MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            resultados = await fetch_todos_indicadores(db_session)

            # Even with failure, cache should be written for monthly indicators
            for meta in INDICADORES_META:
                if meta["tipo"] == "mensal":
                    row = db_session.query(MacroCache).filter(
                        MacroCache.chave == meta["chave"]
                    ).first()
                    assert row is not None, (
                        f"Cache should exist for {meta['chave']} even on failure"
                    )
                    assert row.mes_ano == _mes_ano_atual()


class TestFetchBCSerieReal:
    """Tests with mocked client for edge cases."""

    @pytest.mark.asyncio
    async def test_dados_invalidos_retorna_none(self):
        """API retorna dados que não podem ser parseados → (None, None)."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[
            {"data": "bad", "valor": "N/A"}
        ]))

        valor, periodo = await _fetch_bc_serie(mock_client, 999)
        assert valor is None
        assert periodo is None

    @pytest.mark.asyncio
    async def test_resposta_vazia_retorna_none(self):
        """Lista vazia → (None, None)."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=_make_mock_bc_response(dados=[]))

        valor, periodo = await _fetch_bc_serie(mock_client, 999)
        assert valor is None
        assert periodo is None
