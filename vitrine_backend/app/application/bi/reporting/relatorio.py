from app.application.bi.domain.vendas import Vendas
from app.application.bi.domain.trocas import Trocas
from app.application.bi.schema import COLUNAS, Dimensao, Metrica
from app.schemas.bi_schema import (
    KpisDTO,
    KpisComparativoDTO,
    VariacaoKpi,
    ItemDimensaoDTO,
    ItemCurvaAbcDTO,
    ItemRankingDTO,
    ItemMovimentoDTO,
    TrocasDTO,
)
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


def _calcular_variacao(atual: float, anterior: float | None) -> float | None:
    if anterior is None or anterior == 0:
        return None
    return round((atual - anterior) / anterior * 100, 2)


def comparar_kpis(kpis_atual: KpisDTO, kpis_anterior: KpisDTO | None, dados_parciais_ate: str | None = None) -> KpisComparativoDTO:
    ant = kpis_anterior
    return KpisComparativoDTO(
        faturamento_bruto=VariacaoKpi(
            atual=kpis_atual.faturamento_bruto,
            anterior=ant.faturamento_bruto if ant else None,
            variacao_pct=_calcular_variacao(kpis_atual.faturamento_bruto, ant.faturamento_bruto if ant else None),
        ),
        faturamento_liquido=VariacaoKpi(
            atual=kpis_atual.faturamento_liquido,
            anterior=ant.faturamento_liquido if ant else None,
            variacao_pct=_calcular_variacao(kpis_atual.faturamento_liquido, ant.faturamento_liquido if ant else None),
        ),
        total_trocas=VariacaoKpi(
            atual=kpis_atual.total_trocas,
            anterior=ant.total_trocas if ant else None,
            variacao_pct=_calcular_variacao(kpis_atual.total_trocas, ant.total_trocas if ant else None),
        ),
        qtd_tickets=VariacaoKpi(
            atual=float(kpis_atual.qtd_tickets),
            anterior=float(ant.qtd_tickets) if ant else None,
            variacao_pct=_calcular_variacao(float(kpis_atual.qtd_tickets), float(ant.qtd_tickets) if ant else None),
        ),
        ticket_medio=VariacaoKpi(
            atual=kpis_atual.ticket_medio,
            anterior=ant.ticket_medio if ant else None,
            variacao_pct=_calcular_variacao(kpis_atual.ticket_medio, ant.ticket_medio if ant else None),
        ),
        itens_por_ticket=VariacaoKpi(
            atual=kpis_atual.itens_por_ticket,
            anterior=ant.itens_por_ticket if ant else None,
            variacao_pct=_calcular_variacao(kpis_atual.itens_por_ticket, ant.itens_por_ticket if ant else None),
        ),
        dados_parciais_ate=dados_parciais_ate,
    )


class Relatorio:
    """Gera relatórios de vendas e trocas com KPIs e análises por dimensão."""
    def __init__(
        self,
        vendas: Vendas,
        trocas: Trocas,
    ):
        """Inicializa com os domínios de vendas e trocas."""
        self.vendas = vendas
        self.trocas = trocas

    def kpis(self) -> KpisDTO:
        """Calcula os KPIs principais: faturamento, trocas, tickets e médias."""
        with temporizador("BI Relatorio.kpis", logger):
            df_vendas = self.vendas.df
            df_trocas = self.trocas.df

            faturamento_bruto = df_vendas[COLUNAS.receita].sum()
            total_trocas = df_trocas[COLUNAS.receita].abs().sum()
            faturamento_liquido = faturamento_bruto - total_trocas

            tickets = df_vendas.groupby(COLUNAS.id_documento)[COLUNAS.total_documento].first()
            qtd_tickets = len(tickets)
            ticket_medio = float(tickets.mean()) if qtd_tickets > 0 else 0.0
            itens_por_ticket = (
                float(df_vendas.groupby(COLUNAS.id_documento)[COLUNAS.qtd_item].sum().mean())
                if qtd_tickets > 0 else 0.0
            )

            resultado = KpisDTO(
                faturamento_bruto=round(float(faturamento_bruto), 2),
                faturamento_liquido=round(float(faturamento_liquido), 2),
                total_trocas=round(float(total_trocas), 2),
                qtd_tickets=qtd_tickets,
                ticket_medio=round(ticket_medio, 2),
                itens_por_ticket=round(itens_por_ticket, 2),
            )
        logger.info("BI Relatorio.kpis | faturamento=%.2f tickets=%s", resultado.faturamento_bruto, resultado.qtd_tickets)
        return resultado

    def por_dimensao(self, dimensao: Dimensao, metrica: Metrica) -> list[ItemDimensaoDTO]:
        """Retorna a receita ou quantidade agregada por dimensão (produto, grupo, família)."""
        with temporizador("BI Relatorio.por_dimensao", logger):
            colunas_grupo = dimensao.colunas()
            col_metrica = metrica.value

            if dimensao == Dimensao.PRODUTO:
                colunas_grupo = colunas_grupo + [COLUNAS.codigo]

            df_agrupado = (
                self.vendas.df
                .groupby(colunas_grupo)[col_metrica]
                .sum()
                .reset_index()
                .sort_values(col_metrica, ascending=False)
            )

            resultado = [
                ItemDimensaoDTO(
                    codigo=str(row.get(COLUNAS.codigo, "")),
                    grupo=row.get(COLUNAS.grupo, ""),
                    familia=row.get(COLUNAS.familia),
                    produto=row.get(COLUNAS.produto),
                    valor=round(float(row[col_metrica]), 2),
                )
                for row in df_agrupado.to_dict(orient="records")
            ]
        logger.info("BI Relatorio.por_dimensao | dimensao=%s metrica=%s rows=%s",
                     dimensao.value, metrica.value, len(resultado))
        return resultado

    def curva_abc(self, dimensao: Dimensao) -> list[ItemCurvaAbcDTO]:
        """Gera a curva ABC baseada na receita, classificando produtos em A, B ou C."""
        with temporizador("BI Relatorio.curva_abc", logger):
            colunas_grupo = dimensao.colunas()

            if dimensao == Dimensao.PRODUTO:
                colunas_grupo = colunas_grupo + [COLUNAS.codigo]

            df_agrupado = (
                self.vendas.df
                .groupby(colunas_grupo)[COLUNAS.receita]
                .sum()
                .reset_index()
                .sort_values(COLUNAS.receita, ascending=False)
            )

            total = df_agrupado[COLUNAS.receita].sum()
            df_agrupado["participacao_pct"] = (df_agrupado[COLUNAS.receita] / total * 100).round(2)
            df_agrupado["participacao_acumulada"] = df_agrupado["participacao_pct"].cumsum().round(2)
            df_agrupado["curva"] = df_agrupado["participacao_acumulada"].apply(
                lambda acumulado: "A" if acumulado <= 80 else ("B" if acumulado <= 95 else "C")
            )

            resultado = [
                ItemCurvaAbcDTO(
                    codigo=str(row.get(COLUNAS.codigo, "")),
                    grupo=row.get(COLUNAS.grupo, ""),
                    familia=row.get(COLUNAS.familia),
                    produto=row.get(COLUNAS.produto),
                    receita=round(float(row[COLUNAS.receita]), 2),
                    participacao_pct=row["participacao_pct"],
                    participacao_acumulada=row["participacao_acumulada"],
                    curva=row["curva"],
                )
                for row in df_agrupado.to_dict(orient="records")
            ]
        logger.info("BI Relatorio.curva_abc | dimensao=%s rows=%s", dimensao.value, len(resultado))
        return resultado

    def ranking(self, metrica: Metrica, top: int = 10) -> list[ItemRankingDTO]:
        """Retorna o ranking dos top produtos por métrica (receita ou quantidade)."""
        with temporizador("BI Relatorio.ranking", logger):
            col_metrica = metrica.value

            df_ranking = (
                self.vendas.df
                .groupby([COLUNAS.codigo, COLUNAS.produto])[col_metrica]
                .sum()
                .reset_index()
                .sort_values(col_metrica, ascending=False)
                .head(top)
            )

            resultado = [
                ItemRankingDTO(
                    codigo=str(row[COLUNAS.codigo]),
                    produto=str(row[COLUNAS.produto]),
                    valor=round(float(row[col_metrica]), 2),
                )
                for row in df_ranking.to_dict(orient="records")
            ]
        logger.info("BI Relatorio.ranking | top=%s metrica=%s rows=%s", top, metrica.value, len(resultado))
        return resultado

    def trocas_resumo(self) -> TrocasDTO:
        """Retorna o resumo de trocas com taxa de troca e breakdown por produto."""
        with temporizador("BI Relatorio.trocas_resumo", logger):
            df_trocas = self.trocas.df
            df_vendas = self.vendas.df

            total_trocas = float(df_trocas[COLUNAS.receita].abs().sum())
            faturamento_bruto = float(df_vendas[COLUNAS.receita].sum())
            taxa_troca = (total_trocas / faturamento_bruto * 100) if faturamento_bruto > 0 else 0.0

            df_por_produto = (
                df_trocas
                .groupby([COLUNAS.codigo, COLUNAS.produto])[COLUNAS.receita]
                .sum()
                .abs()
                .reset_index()
                .sort_values(COLUNAS.receita, ascending=False)
            )

            resultado = TrocasDTO(
                total_trocas=round(total_trocas, 2),
                taxa_troca_pct=round(taxa_troca, 2),
                por_produto=[
                    ItemMovimentoDTO(
                        codigo=str(row[COLUNAS.codigo]),
                        produto=str(row[COLUNAS.produto]),
                        receita=round(float(row[COLUNAS.receita]), 2),
                    )
                    for row in df_por_produto.to_dict(orient="records")
                ],
            )
        logger.info("BI Relatorio.trocas_resumo | total_trocas=%.2f taxa=%.2f%% itens=%s",
                     resultado.total_trocas, resultado.taxa_troca_pct, len(resultado.por_produto))
        return resultado