from app.application.bi.domain.perdas import Perdas
from app.application.bi.domain.consumo import Consumo
from app.application.bi.schema import COLUNAS
from app.schemas.bi_schema import MovimentoDTO, ItemMovimentoDTO


class RelatorioMovimento:
    """Gera resumo de movimentos isolados (perdas ou consumo)."""
    def __init__(self, dominio: Perdas | Consumo):
        """Inicializa com o domÃ­nio de perdas ou consumo."""
        self._dominio = dominio

    def resumo(self) -> MovimentoDTO:
        """Retorna o total e breakdown por produto do movimento."""
        df = self._dominio.df
        total = float(df[COLUNAS.receita].abs().sum())

        df_por_produto = (
            df
            .groupby([COLUNAS.codigo, COLUNAS.produto])[COLUNAS.receita]
            .sum()
            .abs()
            .reset_index()
            .sort_values(COLUNAS.receita, ascending=False)
        )

        return MovimentoDTO(
            total=round(total, 2),
            por_produto=[
                ItemMovimentoDTO(
                    codigo=str(row[COLUNAS.codigo]),
                    produto=str(row[COLUNAS.produto]),
                    receita=round(float(row[COLUNAS.receita]), 2),
                )
                for row in df_por_produto.to_dict(orient="records")
            ],
        )
