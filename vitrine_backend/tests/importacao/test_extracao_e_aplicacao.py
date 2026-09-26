from datetime import date
from decimal import Decimal as D

import pytest

from app.application.importacao import extracao
from app.application.importacao.aplicacao import aplicar
from app.application.importacao.extracao import ArquivoInvalido, extrair
from app.application.importacao.mapeamento import ColunaMapeada, Mapeamento
from app.application.importacao.normalizacao import assinatura_linha, numero
from tests.importacao import relatorios as rel
from vitrine_core.datasets.tipos import Operacao, TipoDataset


def _mapeamento_vendedores(linha_cabecalho: int, **extra) -> Mapeamento:
    return Mapeamento(
        tipo=TipoDataset.VENDAS_VENDEDOR_PERIODO,
        linha_cabecalho=linha_cabecalho,
        colunas=[
            ColunaMapeada(indice=0, campo="vendedor"),
            ColunaMapeada(indice=1, campo="atendimentos"),
            ColunaMapeada(indice=2, campo="pecas"),
            ColunaMapeada(indice=3, campo="faturamento_bruto"),
            ColunaMapeada(indice=4, campo="trocas"),
        ],
        **extra,
    )


@pytest.mark.parametrize("gerar, formato", [(rel.vendedores_xlsx, "xlsx"), (rel.vendedores_xls, "xls")])
def test_relatorio_de_vendedores_bate_com_o_total_geral(gerar, formato):
    grade = extrair(gerar(), f"relatorio.{formato}")

    resultado = aplicar(grade, _mapeamento_vendedores(rel.linha_cabecalho_vendedores()))

    assert grade.formato == formato
    assert resultado.validacao.status == "conferido"
    assert set(resultado.validacao.campos_conferidos) == {"atendimentos", "pecas", "faturamento_bruto", "trocas"}
    assert [r["vendedor"] for r in resultado.registros] == ["MARIANA SOUZA", "CARLOS LIMA", "JULIA PEREIRA", "ANA COSTA"]
    assert sum(r["faturamento_bruto"] for r in resultado.registros) == D("25658.70")
    assert resultado.periodo == rel.PERIODO_SETEMBRO
    assert resultado.confirmavel


def test_total_adulterado_fica_divergente_e_nao_pode_confirmar():
    total_errado = ("TOTAL GERAL", 155, 390, "25.000,00", "509,90")
    grade = extrair(rel.vendedores_xlsx(total=total_errado), "r.xlsx")

    resultado = aplicar(grade, _mapeamento_vendedores(rel.linha_cabecalho_vendedores()))

    assert resultado.validacao.status == "divergente"
    assert [d.campo for d in resultado.validacao.diferencas] == ["faturamento_bruto"]
    assert not resultado.confirmavel


def test_coluna_de_dinheiro_num_campo_inteiro_descarta_as_linhas():
    mapeamento = _mapeamento_vendedores(rel.linha_cabecalho_vendedores())
    mapeamento.colunas[1] = ColunaMapeada(indice=3, campo="atendimentos")
    mapeamento.colunas[3] = ColunaMapeada(indice=1, campo="faturamento_bruto")

    resultado = aplicar(extrair(rel.vendedores_xlsx(), "r.xlsx"), mapeamento)

    cabecalho = rel.linha_cabecalho_vendedores()
    vendedores_do_centro = {cabecalho + 1, cabecalho + 2, cabecalho + 3}
    assert vendedores_do_centro <= {d.indice for d in resultado.descartadas}
    assert resultado.validacao.status == "divergente"
    assert not resultado.confirmavel


def test_diarias_csv_cp1252_com_ponto_e_virgula():
    grade = extrair(rel.diarias_csv(), "diario.csv")
    mapeamento = Mapeamento(
        tipo=TipoDataset.VENDAS_DIARIAS, linha_cabecalho=3,
        colunas=[
            ColunaMapeada(indice=0, campo="data"),
            ColunaMapeada(indice=1, campo="faturamento_bruto"),
            ColunaMapeada(indice=2, campo="atendimentos"),
            ColunaMapeada(indice=3, campo="pecas"),
        ],
    )

    resultado = aplicar(grade, mapeamento)

    assert resultado.validacao.status == "conferido"
    assert resultado.periodo == (date(2026, 9, 1), date(2026, 9, 3))
    assert grade.linhas[0][0] == "Relatório diário de vendas"


def test_contatos_sem_linha_de_total_exige_periodo_informado():
    grade = extrair(rel.contatos_csv(), "dito.csv")
    colunas = [
        ColunaMapeada(indice=0, campo="vendedor"),
        ColunaMapeada(indice=1, campo="contatos"),
        ColunaMapeada(indice=2, campo="respostas"),
        ColunaMapeada(indice=3, campo="conversoes"),
    ]

    sem_periodo = aplicar(grade, Mapeamento(tipo=TipoDataset.CONTATOS_VENDEDOR, linha_cabecalho=0, colunas=colunas, separador_decimal="."))
    com_periodo = aplicar(grade, Mapeamento(
        tipo=TipoDataset.CONTATOS_VENDEDOR, linha_cabecalho=0, colunas=colunas, separador_decimal=".",
        periodo={"inicio": "2026-09-01", "fim": "2026-09-30"},
    ))

    assert not sem_periodo.confirmavel
    assert sem_periodo.erros
    assert com_periodo.validacao.status == "sem_total"
    assert com_periodo.confirmavel
    assert com_periodo.periodo == rel.PERIODO_SETEMBRO


def test_itens_xlsx_com_datas_reais_e_trocas():
    grade = extrair(rel.itens_xlsx(), "itens.xlsx")
    mapeamento = Mapeamento(
        tipo=TipoDataset.ITENS_VENDA, linha_cabecalho=0,
        colunas=[
            ColunaMapeada(indice=0, campo="documento"),
            ColunaMapeada(indice=1, campo="data"),
            ColunaMapeada(indice=2, campo="operacao"),
            ColunaMapeada(indice=3, campo="vendedor"),
            ColunaMapeada(indice=4, campo="produto"),
            ColunaMapeada(indice=5, campo="tamanho"),
            ColunaMapeada(indice=6, campo="cor"),
            ColunaMapeada(indice=7, campo="quantidade"),
            ColunaMapeada(indice=8, campo="valor"),
        ],
    )

    resultado = aplicar(grade, mapeamento)

    assert resultado.validacao.status == "conferido"
    assert [r["operacao"] for r in resultado.registros].count(Operacao.TROCA) == 1
    assert resultado.registros[2]["tamanho"] == "40"


@pytest.mark.parametrize("com_bordas", [True, False], ids=["com-bordas", "sem-bordas"])
def test_pdf_com_tabela(com_bordas):
    grade = extrair(rel.produtos_pdf(com_bordas), "curva.pdf")
    mapeamento = Mapeamento(
        tipo=TipoDataset.VENDAS_PRODUTO_PERIODO, linha_cabecalho=0,
        colunas=[
            ColunaMapeada(indice=0, campo="produto"),
            ColunaMapeada(indice=1, campo="grupo"),
            ColunaMapeada(indice=2, campo="quantidade"),
            ColunaMapeada(indice=3, campo="receita"),
        ],
        periodo={"inicio": "2026-09-01", "fim": "2026-09-30"},
    )

    resultado = aplicar(grade, mapeamento)

    assert resultado.validacao.status == "conferido"
    assert [r["produto"] for r in resultado.registros] == ["Vestido Midi", "Calça Jeans"]


def test_assinatura_do_cabecalho_ignora_titulo_loja_e_posicao():
    a = extrair(rel.vendedores_xlsx(), "a.xlsx")
    b = extrair(rel.vendedores_xlsx(titulos_extras=2, loja="TACO BOULEVARD"), "b.xlsx")

    assinatura_a = assinatura_linha(a.linhas[rel.linha_cabecalho_vendedores()])
    assinatura_b = assinatura_linha(b.linhas[rel.linha_cabecalho_vendedores(2)])

    assert assinatura_a == assinatura_b
    assert assinatura_linha(a.linhas[0]) is None


@pytest.mark.parametrize("bruto, separador, esperado", [
    ("R$ 1.234,56", ",", D("1234.56")),
    ("(1.234,56)", ",", D("-1234.56")),
    ("1,234.56", ".", D("1234.56")),
    ("-", ",", None),
    (12.5, ",", D("12.5")),
])
def test_numero_em_formatos_brasileiros_e_americanos(bruto, separador, esperado):
    assert numero(bruto, separador) == esperado


def test_formato_nao_suportado():
    with pytest.raises(ArquivoInvalido):
        extrair(b"GIF89a....", "imagem.gif")


def test_arquivo_grande_demais(monkeypatch):
    monkeypatch.setattr(extracao, "LIMITE_BYTES", 10)
    with pytest.raises(ArquivoInvalido):
        extrair(rel.contatos_csv(), "c.csv")


def test_xlsx_que_descompacta_demais_e_recusado(monkeypatch):
    monkeypatch.setattr(extracao, "LIMITE_DESCOMPACTADO", 1000)
    with pytest.raises(ArquivoInvalido):
        extrair(rel.vendedores_xlsx(), "bomba.xlsx")


def test_pdf_sem_tabela_e_recusado():
    with pytest.raises(ArquivoInvalido):
        extrair(rel.pdf_sem_tabela(), "texto.pdf")


def test_mapeamento_sem_campo_obrigatorio_e_invalido():
    with pytest.raises(ValueError):
        Mapeamento(tipo=TipoDataset.VENDAS_VENDEDOR_PERIODO, linha_cabecalho=0,
                   colunas=[ColunaMapeada(indice=0, campo="vendedor")])
