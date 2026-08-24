"""Testes do adapter de demonstração.

O foco é nas invariantes que o BI exige: quebrar qualquer uma delas deixa
uma tela vazia ou um indicador zerado, e isso é difícil de perceber olhando
só o adapter.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.adapters.demo.catalog import CATALOGO
from app.adapters.demo.ean import gerar_ean13
from app.adapters.demo.generator import gerar_dia
from app.adapters.demo.product_source import DemoProductSource
from app.adapters.demo.transaction_source import DemoTransactionSource
from app.core.models.transaction import OperationType
from app.domain.value_objects.codigo import Codigo


@pytest.fixture
def periodo():
    fim = date.today() - timedelta(days=1)  # evita o dia parcial
    return fim - timedelta(days=29), fim


class TestCatalogo:
    def test_codigos_internos_sao_plu_validos(self):
        assert all(Codigo(s.internal_code).tipo == "PLU6" for s in CATALOGO)

    def test_barcodes_sao_ean13_validos(self):
        """Código inválido faz a busca por produto responder 400."""
        assert all(Codigo(b).tipo == "EAN13" for s in CATALOGO for b in s.barcodes)

    def test_codigos_sao_unicos(self):
        assert len({s.internal_code for s in CATALOGO}) == len(CATALOGO)
        assert len({b for s in CATALOGO for b in s.barcodes}) == len(CATALOGO)

    def test_preco_acima_do_custo(self):
        assert all(s.preco_base > s.custo_base for s in CATALOGO)

    def test_tem_variedade_de_grupos_e_familias(self):
        """Sem variedade, receita por grupo/família vira uma linha só."""
        assert len({s.grupo for s in CATALOGO}) >= 8
        assert len({s.familia for s in CATALOGO}) >= 15
        assert all(s.grupo and s.familia for s in CATALOGO)


class TestEan:
    def test_digito_verificador_confere(self):
        assert all(Codigo(gerar_ean13(i)).tipo == "EAN13" for i in range(1, 500))


class TestDeterminismo:
    def test_mesmo_dia_gera_os_mesmos_itens(self):
        dia = date(2026, 3, 14)
        assert gerar_dia(dia) == gerar_dia(dia)

    def test_independe_do_intervalo_pedido(self, periodo):
        """Obrigatório para o comparativo ano-a-ano fechar: os dois lados da
        comparação são pedidos em intervalos diferentes."""
        inicio, fim = periodo
        meio = inicio + timedelta(days=10)

        inteiro = DemoTransactionSource().get_items(inicio, fim)
        partido = DemoTransactionSource().get_items(inicio, meio) + \
            DemoTransactionSource().get_items(meio + timedelta(days=1), fim)

        assert inteiro == partido

    def test_instancias_diferentes_concordam(self, periodo):
        a = DemoTransactionSource().get_items(*periodo)
        b = DemoTransactionSource().get_items(*periodo)
        assert a == b


class TestInvariantesDoBi:
    def test_document_total_e_igual_em_todas_as_linhas_do_documento(self, periodo):
        """O ticket médio sai de groupby(documento).first() — total divergente
        entre linhas do mesmo documento zera ou distorce o indicador."""
        totais = defaultdict(set)
        for item in DemoTransactionSource().get_items(*periodo):
            totais[item.document_id].add(item.document_total)
        assert all(len(v) == 1 for v in totais.values())

    def test_document_total_bate_com_a_soma_das_linhas(self, periodo):
        linhas = defaultdict(Decimal)
        totais = {}
        for item in DemoTransactionSource().get_items(*periodo):
            linhas[item.document_id] += item.line_total
            totais[item.document_id] = item.document_total
        for doc, soma in linhas.items():
            assert abs(soma - totais[doc]) <= Decimal("0.02"), doc

    def test_document_id_nao_colide_entre_dias(self, periodo):
        """IDs repetidos entre dias fundem tickets numa série de vários dias."""
        _, fim = periodo
        a = {i.document_id for i in gerar_dia(fim)}
        b = {i.document_id for i in gerar_dia(fim - timedelta(days=1))}
        assert not (a & b)

    def test_todo_item_tem_horario(self, periodo):
        """A análise por hora usa o horário como rótulo do balde; nulo vira
        um balde de lixo chamado 'No'."""
        assert all(i.time is not None for i in DemoTransactionSource().get_items(*periodo))

    def test_todo_item_tem_operacao_e_categorias(self, periodo):
        for item in DemoTransactionSource().get_items(*periodo):
            assert item.operation is not None  # sem operação, domínio ignora
            assert item.group_name and item.family_name
            assert item.product_name

    def test_product_code_e_aceito_pelo_value_object(self, periodo):
        codigos = {i.product_code for i in DemoTransactionSource().get_items(*periodo)}
        assert all(Codigo(c).valor == c for c in codigos)

    def test_gera_as_quatro_operacoes(self, periodo):
        ops = {i.operation for i in DemoTransactionSource().get_items(*periodo)}
        assert ops == set(OperationType)

    def test_perdas_e_consumo_tem_documento_comprobatorio(self, periodo):
        """Os domínios de Perdas e Consumo descartam movimento sem documento —
        sem nenhum documentado, as duas telas ficam vazias."""
        itens = DemoTransactionSource().get_items(*periodo)
        for operacao in (OperationType.LOSS, OperationType.CONSUMPTION):
            docs = [i for i in itens if i.operation is operacao]
            assert docs, f"nenhum item de {operacao}"
            assert any(i.external_document_id is not None for i in docs)

    def test_existem_vendas_canceladas(self, periodo):
        itens = DemoTransactionSource().get_items(*periodo)
        assert any(i.is_canceled for i in itens)
        assert not all(i.is_canceled for i in itens)


class TestJanelaEDiaParcial:
    def test_fora_da_janela_devolve_vazio_sem_erro(self):
        """O comparativo pede datas de um ano atrás; exceção derrubaria a tela."""
        antigo = date.today() - timedelta(days=5000)
        assert DemoTransactionSource().get_items(antigo, antigo) == []

    def test_intervalo_invertido_devolve_vazio(self):
        hoje = date.today()
        assert DemoTransactionSource().get_items(hoje, hoje - timedelta(days=5)) == []

    def test_dia_de_hoje_e_truncado_na_hora_atual(self):
        """A série diária e a análise por hora não filtram sozinhas — sem o
        corte na fonte, hoje apareceria com movimento de dia inteiro."""
        hoje = date.today()
        itens = DemoTransactionSource().get_items(hoje, hoje)
        hora_atual = datetime.now().hour
        assert all(i.time.hour <= hora_atual for i in itens)

    def test_futuro_nao_tem_dados(self):
        amanha = date.today() + timedelta(days=1)
        assert DemoTransactionSource().get_items(amanha, amanha + timedelta(days=5)) == []


class TestKpiAggregates:
    def test_nao_implementa_atalho_de_agregados(self):
        """Herdar None mantém indicadores e gráficos no mesmo caminho de
        dados. Um atalho aqui faria o número do topo divergir do gráfico."""
        hoje = date.today()
        assert DemoTransactionSource().get_kpi_aggregates(hoje, hoje) is None


class TestProductSource:
    def test_devolve_o_catalogo_inteiro(self):
        assert len(DemoProductSource().get_all_products()) == len(CATALOGO)

    def test_produtos_tem_dados_utilizaveis(self):
        for p in DemoProductSource().get_all_products():
            assert Codigo(p.internal_code).tipo == "PLU6"
            assert p.name and p.group and p.family
            assert p.sale_price > 0 and p.cost_price > 0
            assert p.sale_price > p.cost_price

    def test_codigo_interno_e_pesquisavel(self):
        """A consulta de produto resolve o código pela tabela de códigos, não
        por codigo_chamada — sem o PLU ali, buscar por código interno dá 404."""
        for produto in DemoProductSource().get_all_products():
            assert produto.internal_code in produto.barcodes

    def test_preco_bate_com_o_usado_nas_transacoes(self):
        """Tabela de preços e receita do BI precisam contar a mesma história."""
        from app.adapters.demo.pricing import preco_no_dia

        hoje = date.today()
        precos = {p.internal_code: p.sale_price for p in DemoProductSource().get_all_products()}
        for sku in CATALOGO[:20]:
            assert precos[sku.internal_code] == preco_no_dia(sku, hoje)
