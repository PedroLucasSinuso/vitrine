import io
from datetime import date
from decimal import Decimal

from app.application.importacao.mapeamento import ColunaMapeada, Mapeamento
from vitrine_core.datasets.tipos import TipoDataset

LINHA_CABECALHO_EXEMPLO = 5
NOMES_DOS_MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
                   "agosto", "setembro", "outubro", "novembro", "dezembro")


def mapeamento_do_exemplo() -> Mapeamento:
    return Mapeamento(
        tipo=TipoDataset.VENDAS_VENDEDOR_PERIODO,
        linha_cabecalho=LINHA_CABECALHO_EXEMPLO,
        colunas=[
            ColunaMapeada(indice=0, campo="vendedor"),
            ColunaMapeada(indice=1, campo="atendimentos"),
            ColunaMapeada(indice=2, campo="pecas"),
            ColunaMapeada(indice=3, campo="faturamento_bruto"),
            ColunaMapeada(indice=4, campo="trocas"),
        ],
    )


def _formatar(valor: Decimal) -> str:
    inteiro, centavos = f"{valor:.2f}".split(".")
    return f"{int(inteiro):,}".replace(",", ".") + "," + centavos


def nome_do_arquivo(inicio: date) -> str:
    return f"vendas-por-vendedor-{NOMES_DOS_MESES[inicio.month - 1]}.xlsx"


def relatorio_por_vendedor(
    loja: str, inicio: date, fim: date, hoje: date, linhas: list[tuple[str, int, Decimal, Decimal, Decimal]]
) -> bytes:
    from openpyxl import Workbook

    livro = Workbook()
    planilha = livro.active
    planilha.title = "Relatorio"
    planilha.append(["RELATÓRIO DE VENDAS POR VENDEDOR"])
    planilha.append([f"Loja: {loja}"])
    planilha.append([f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"])
    planilha.append([])
    planilha.append([None, "Vendas", None, None, None])
    planilha.append(["Vendedor", "Qtd Tickets", "Qtd Peças", "Valor (R$)", "Trocas (R$)"])
    planilha.merge_cells(start_row=5, start_column=2, end_row=5, end_column=4)
    total_atendimentos, total_pecas, total_bruto, total_trocas = 0, Decimal(0), Decimal(0), Decimal(0)
    for nome, atendimentos, pecas, bruto, trocas in linhas:
        planilha.append([nome, atendimentos, int(pecas), f"R$ {_formatar(bruto)}", _formatar(trocas)])
        total_atendimentos += atendimentos
        total_pecas += pecas
        total_bruto += bruto
        total_trocas += trocas
    planilha.append(["TOTAL GERAL", total_atendimentos, int(total_pecas), _formatar(total_bruto), _formatar(total_trocas)])
    planilha.append([])
    planilha.append([f"Emitido em {hoje:%d/%m/%Y} por gerente.loja"])
    saida = io.BytesIO()
    livro.save(saida)
    return saida.getvalue()
