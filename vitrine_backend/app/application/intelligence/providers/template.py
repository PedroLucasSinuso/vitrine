"""Fallback determinístico — gera resposta sem IA usando templates Jinja2."""
from datetime import datetime, timezone
from app.schemas.intelligence_schema import IntelligenceResponse, Insight, InsightMetricas


class TemplateProvider:
    """Provider de fallback. Gera resposta estruturada sem chamar API externa."""

    def sintetizar(self, dados_macro: dict, dados_detectores: dict) -> IntelligenceResponse:
        insights: list[Insight] = []

        # Encalhes
        encalhes = dados_detectores.get("encalhes", [])
        if encalhes:
            total = len(encalhes)
            valor_total = sum(e.get("valor_estimado", 0) for e in encalhes)
            top = encalhes[:3]
            nomes = ", ".join(e.get("nome", "?") for e in top)
            insights.append(Insight(
                hash=f"encalhe_{total}_{int(valor_total)}",
                tipo="encalhe",
                impacto="alto" if valor_total > 10000 else "medio",
                titulo=f"Revise {total} produtos sem venda há mais de 30 dias",
                descricao=f"{nomes} lideram o valor encalhado, totalizando R$ {valor_total:,.2f} em estoque parado.",
                sugestao="Considere promoção de queima de estoque ou devolução ao fornecedor.",
                metricas=InsightMetricas(
                    total_encalhados=total,
                    valor_total_encalhado=round(valor_total, 2),
                ),
            ))

        # Resumo executivo
        linhas = []
        if dados_macro.get("faturamento"):
            linhas.append(f"Faturamento de R$ {dados_macro['faturamento']:,.2f} no período.")
        if insights:
            linhas.append(f"Foram identificados {len(insights)} oportunidades de melhoria.")
        resumo = " ".join(linhas) or "Nenhum insight relevante identificado no período."

        return IntelligenceResponse(
            resumo_executivo=resumo,
            insights=insights,
            fonte="deterministico",
            gerado_em=datetime.now(timezone.utc),
        )
