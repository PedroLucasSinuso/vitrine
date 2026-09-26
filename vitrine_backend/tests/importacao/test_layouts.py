import pytest

from app.application.importacao.aplicacao import aplicar
from app.application.importacao.extracao import detectar_formato, extrair
from tests.importacao import layouts

LAYOUTS = layouts.todos()


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda l: l.nome)
def test_layout_de_erp_diferente_le_confere_e_fecha_o_total(layout):
    grade = extrair(layout.conteudo, layout.arquivo)

    resultado = aplicar(grade, layout.mapeamento)

    assert resultado.erros == []
    assert resultado.validacao.status == ("conferido" if layout.tem_total else "sem_total")
    assert {r["vendedor"] for r in resultado.registros} == layout.vendedores_esperados
    assert sum(r["faturamento_bruto"] for r in resultado.registros) == layout.bruto_esperado
    assert resultado.confirmavel
    assert resultado.periodo == layouts.SETEMBRO


@pytest.mark.parametrize("layout, formato", [
    (layouts.html_disfarcado_de_xls(), "html"),
    (layouts.csv_utf16_tab_decimal_ponto(), "csv"),
    (layouts.xls_legado(), "xls"),
    (layouts.csv_cp1252_com_codigo(), "csv"),
], ids=["html", "utf16", "xls", "cp1252"])
def test_formato_e_detectado_pelo_conteudo_e_nao_pela_extensao(layout, formato):
    assert detectar_formato(layout.conteudo, layout.arquivo) == formato


def test_total_alterado_em_qualquer_layout_e_pego():
    layout = layouts.html_disfarcado_de_xls()
    adulterado = layout.conteudo.replace(b"R$ 18.801,25", b"R$ 1,00")

    resultado = aplicar(extrair(adulterado, layout.arquivo), layout.mapeamento)

    assert adulterado != layout.conteudo
    assert resultado.validacao.status == "divergente"
    assert not resultado.confirmavel


def test_csv_com_linha_sep_do_excel_ignora_a_dica():
    conteudo = "sep=;\r\nVendedor;Tickets;Peças;Valor;Trocas\r\nANA;2;3;100,00;0,00\r\n".encode("utf-8")

    grade = extrair(conteudo, "x.csv")

    assert grade.linhas[0][0] == "Vendedor"


def test_html_sem_tabela_e_recusado():
    from app.application.importacao.extracao import ArquivoInvalido

    with pytest.raises(ArquivoInvalido):
        extrair(b"<html><body><p>nada aqui</p></body></html>", "x.xls")
