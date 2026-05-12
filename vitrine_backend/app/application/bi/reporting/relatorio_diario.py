from app.application.bi.domain.vendas import Vendas
from app.application.bi.schema import COLUNAS, Metrica
from app.schemas.bi_schema import PontoDiarioDTO


class RelatorioDiario:
    def __init__(self, vendas: Vendas):
        self.vendas = vendas

    def serie_temporal(self, metrica: Metrica) -> list[PontoDiarioDTO]:
        col_metrica = metrica.value

        df_serie = (
            self.vendas.df
            .groupby(COLUNAS.emissao)[col_metrica]
            .sum()
            .reset_index()
            .sort_values(COLUNAS.emissao)
        )

        return [
            PontoDiarioDTO(
                data=str(row[COLUNAS.emissao]),
                valor=round(float(row[col_metrica]), 2),
            )
            for row in df_serie.to_dict(orient="records")
        ]

    def serie_por_produto(self, codigo: str, metrica: Metrica) -> list[PontoDiarioDTO]:
        col_metrica = metrica.value

        df_produto = self.vendas.df[self.vendas.df[COLUNAS.codigo] == codigo]
        if df_produto.empty:
            return []

        df_serie = (
            df_produto
            .groupby(COLUNAS.emissao)[col_metrica]
            .sum()
            .reset_index()
            .sort_values(COLUNAS.emissao)
        )

        return [
            PontoDiarioDTO(
                data=str(row[COLUNAS.emissao]),
                valor=round(float(row[col_metrica]), 2),
            )
            for row in df_serie.to_dict(orient="records")
        ]