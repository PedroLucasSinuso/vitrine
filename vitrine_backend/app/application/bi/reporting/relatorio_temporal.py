import pandas as pd
from app.application.bi.domain.vendas import Vendas
from app.application.bi.schema import COLUNAS, Metrica
from app.schemas.bi_schema import PontoHoraDTO, PontoDiaSemanaDTO

_DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta",
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo",
}


class RelatorioTemporal:
    def __init__(self, vendas: Vendas):
        self.vendas = vendas
        df_enriquecido = vendas.df.copy()
        df_enriquecido["_hora"] = (
            df_enriquecido[COLUNAS.hora]
            .astype(str)
            .str[:2]
            .str.zfill(2)
        )
        df_enriquecido["_dia_semana_num"] = df_enriquecido[COLUNAS.emissao].apply(
            lambda data: data.weekday() if hasattr(data, "weekday") else None
        )
        self._df = df_enriquecido

    def por_hora(self, metrica: Metrica) -> list[PontoHoraDTO]:
        col_metrica = metrica.value

        df_hora = (
            self._df
            .groupby("_hora")[col_metrica]
            .sum()
            .reset_index()
            .sort_values("_hora")
        )

        return [
            PontoHoraDTO(
                hora=str(row["_hora"]),
                valor=round(float(row[col_metrica]), 2),
            )
            for row in df_hora.to_dict(orient="records")
        ]

    def por_dia_semana(self, metrica: Metrica) -> list[PontoDiaSemanaDTO]:
        col_metrica = metrica.value

        df_dia = (
            self._df
            .groupby("_dia_semana_num")[col_metrica]
            .sum()
            .reset_index()
            .sort_values("_dia_semana_num")
        )

        return [
            PontoDiaSemanaDTO(
                dia_semana=_DIAS_SEMANA.get(int(row["_dia_semana_num"]), "Desconhecido"),
                valor=round(float(row[col_metrica]), 2),
            )
            for row in df_dia.to_dict(orient="records")
        ]