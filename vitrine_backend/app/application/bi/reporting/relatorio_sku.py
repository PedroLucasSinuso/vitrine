from app.application.bi.domain.vendas import Vendas
from app.application.bi.schema import COLUNAS
from app.schemas.bi_schema import SkuDTO, PontoDiarioDTO, PontoHoraDTO


class RelatorioSku:
    def __init__(self, vendas: Vendas, codigo: str):
        self.codigo = codigo
        self._df = vendas.df[vendas.df[COLUNAS.codigo] == codigo].copy()

    def resumo(self) -> SkuDTO | None:
        if self._df.empty:
            return None

        receita_total = float(self._df[COLUNAS.receita].sum())
        qtd_total = float(self._df[COLUNAS.qtd_item].sum())
        qtd_tickets = self._df[COLUNAS.id_documento].nunique()
        ticket_medio = receita_total / qtd_tickets if qtd_tickets > 0 else 0.0

        df_ranking_dias = (
            self._df
            .groupby(COLUNAS.emissao)[COLUNAS.receita]
            .sum()
            .reset_index()
            .sort_values(COLUNAS.receita, ascending=False)
            .head(10)
        )

        self._df["_hora"] = (
            self._df[COLUNAS.hora]
            .astype(str)
            .str[:2]
            .str.zfill(2)
        )
        df_por_hora = (
            self._df
            .groupby("_hora")[COLUNAS.receita]
            .sum()
            .reset_index()
            .sort_values("_hora")
        )

        info_produto = self._df[[
            COLUNAS.codigo, COLUNAS.produto, COLUNAS.grupo, COLUNAS.familia
        ]].iloc[0]

        return SkuDTO(
            codigo=str(info_produto[COLUNAS.codigo]),
            produto=str(info_produto[COLUNAS.produto]),
            grupo=str(info_produto[COLUNAS.grupo]),
            familia=str(info_produto[COLUNAS.familia]),
            receita_total=round(receita_total, 2),
            qtd_total=round(qtd_total, 2),
            qtd_tickets=qtd_tickets,
            ticket_medio=round(ticket_medio, 2),
            ranking_dias=[
                PontoDiarioDTO(
                    data=str(row[COLUNAS.emissao]),
                    valor=round(float(row[COLUNAS.receita]), 2),
                )
                for row in df_ranking_dias.to_dict(orient="records")
            ],
            distribuicao_hora=[
                PontoHoraDTO(
                    hora=str(row["_hora"]),
                    valor=round(float(row[COLUNAS.receita]), 2),
                )
                for row in df_por_hora.to_dict(orient="records")
            ],
        )