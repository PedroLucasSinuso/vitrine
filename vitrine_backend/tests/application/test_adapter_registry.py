"""Testes do registry de adapters de ERP.

O registry existia antes mas era decorativo: guardava classes que ninguém
instanciava, enquanto a construção real era fixa no Alterdata. Estes testes
travam o comportamento novo — o ERP configurado é quem decide.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.application import erp_factory
from app.application.adapter_registry import (
    AdapterEntry,
    AdapterNaoRegistradoError,
    adapters_disponiveis,
    get_adapter,
    register_adapter,
)
from app.core.interfaces.source import ProductSource, TransactionSource


class _FakeProductSource(ProductSource):
    def get_all_products(self):
        return []


class _FakeTransactionSource(TransactionSource):
    def get_items(self, start, end):
        return []


@pytest.fixture
def adapter_fake():
    """Registra um adapter de teste e o remove depois."""
    from app.application import adapter_registry

    @contextmanager
    def _abrir(db, empresa_id, pool_size=1):
        yield _FakeProductSource()

    entry = AdapterEntry(
        nome="fake",
        criar_product_source=lambda db, eid: _FakeProductSource(),
        criar_transaction_source=lambda db, eid: _FakeTransactionSource(),
        abrir_sync_source=_abrir,
    )
    register_adapter(entry)
    yield entry
    adapter_registry._REGISTRY.pop("fake", None)


class TestRegistry:
    def test_adapters_nativos_estao_registrados(self):
        assert {"alterdata", "demo"} <= set(adapters_disponiveis())

    def test_adapter_desconhecido_erra_com_mensagem_util(self):
        with pytest.raises(AdapterNaoRegistradoError) as exc:
            get_adapter("nao-existe")
        assert "nao-existe" in str(exc.value)
        assert "alterdata" in str(exc.value)  # lista as opções válidas

    def test_registro_novo_fica_disponivel(self, adapter_fake):
        assert get_adapter("fake") is adapter_fake


class TestSelecaoPorConfiguracao:
    def test_usa_o_adapter_configurado_na_empresa(self, adapter_fake):
        with patch.object(erp_factory, "nome_adapter", return_value="fake"):
            source = erp_factory.create_transaction_source(MagicMock(), 1)
        assert isinstance(source, _FakeTransactionSource)

    def test_alterdata_continua_sendo_o_padrao(self):
        """Empresa sem 'erp_adapter' configurado não muda de comportamento."""
        db = MagicMock()
        with patch("app.application.config_service.get", return_value="alterdata") as get:
            assert erp_factory.nome_adapter(db, 1) == "alterdata"
        assert get.call_args.args[3] == "alterdata"  # o default passado

    def test_demo_dispensa_conexao_externa(self):
        """O adapter de demo ignora sessão e empresa — não há ERP por trás."""
        with patch.object(erp_factory, "nome_adapter", return_value="demo"):
            source = erp_factory.create_transaction_source(None, 999)
        from app.adapters.demo.transaction_source import DemoTransactionSource

        assert isinstance(source, DemoTransactionSource)


class TestSync:
    def test_descarta_recursos_mesmo_quando_o_sync_falha(self, adapter_fake):
        """O ciclo de vida do engine é do adapter; uma falha no meio do sync
        não pode deixar conexão pendurada."""
        saiu = []

        @contextmanager
        def _abrir(db, empresa_id, pool_size=1):
            try:
                yield _FakeProductSource()
            finally:
                saiu.append(True)

        entry = AdapterEntry(
            nome="fake",
            criar_product_source=adapter_fake.criar_product_source,
            criar_transaction_source=adapter_fake.criar_transaction_source,
            abrir_sync_source=_abrir,
        )
        register_adapter(entry)

        with patch.object(erp_factory, "nome_adapter", return_value="fake"), \
             patch("app.application.sync_service.SyncService") as service:
            service.return_value.sync.side_effect = RuntimeError("falhou")
            with pytest.raises(RuntimeError):
                erp_factory.run_sync_common(MagicMock(), 1)

        assert saiu == [True]

    def test_avisa_o_adapter_quando_o_sync_termina(self, adapter_fake):
        """É assim que o Alterdata invalida o próprio cache de transações."""
        avisado = []

        @contextmanager
        def _abrir(db, empresa_id, pool_size=1):
            yield _FakeProductSource()

        register_adapter(
            AdapterEntry(
                nome="fake",
                criar_product_source=adapter_fake.criar_product_source,
                criar_transaction_source=adapter_fake.criar_transaction_source,
                abrir_sync_source=_abrir,
                ao_terminar_sync=lambda: avisado.append(True),
            )
        )

        with patch.object(erp_factory, "nome_adapter", return_value="fake"), \
             patch("app.application.sync_service.SyncService"):
            erp_factory.run_sync_common(MagicMock(), 1)

        assert avisado == [True]
