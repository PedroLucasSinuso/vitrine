"""Fallback determinístico — gera resposta sem IA usando templates Jinja2."""
from app.application.intelligence._utils import utcnow
from app.schemas.intelligence_schema import IntelligenceResponse, Insight, InsightMetricas


class TemplateProvider:
    """Provider de fallback. Gera resposta estruturada sem chamar API externa."""

    def sintetizar(self, dados_macro: dict, dados_detectores: dict) -> IntelligenceResponse:
        insights: list[Insight] = []

        # ── 1. Encalhes ──
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

        # ── 2. Taxa de troca ──
        trocas = dados_detectores.get("taxa_troca", [])
        if trocas:
            top_troca = trocas[0]
            taxa_pct = top_troca.get("taxa", 0) * 100
            insights.append(Insight(
                hash=f"taxa_troca_{len(trocas)}_{int(taxa_pct*100)}",
                tipo="taxa_troca",
                impacto="alto" if taxa_pct > 20 else "medio",
                titulo=f"{len(trocas)} produtos com alta taxa de troca/devolução",
                descricao=(
                    f"{top_troca.get('nome', '?')} lidera com {taxa_pct:.1f}% de trocas "
                    f"({int(top_troca.get('qtd_trocas', 0))} de {int(top_troca.get('qtd_vendas', 0))} vendas)."
                ),
                sugestao="Verifique qualidade, embalagem ou treinamento da equipe sobre o produto.",
                metricas=InsightMetricas(
                    taxa=round(taxa_pct, 2),
                    qtd_trocas=int(top_troca.get("qtd_trocas", 0)),
                    qtd_vendas=int(top_troca.get("qtd_vendas", 0)),
                ),
            ))

        # ── 3. Sazonalidade ──
        sazonais = dados_detectores.get("sazonalidade", [])
        if sazonais:
            top_saz = sazonais[0]
            cresc_pct = top_saz.get("crescimento_qtd", 0) * 100
            insights.append(Insight(
                hash=f"sazonalidade_{len(sazonais)}_{int(cresc_pct*100)}",
                tipo="sazonalidade",
                impacto="medio",
                titulo=f"{len(sazonais)} produtos com crescimento acima de 30%",
                descricao=(
                    f"{top_saz.get('nome', '?')} cresceu {cresc_pct:.0f}% nas vendas "
                    f"({int(top_saz.get('qtd_atual', 0))} uni. vs. {int(top_saz.get('qtd_anterior', 0))} uni. no período anterior)."
                ),
                sugestao="Avalie se é demanda sazonal genuína e ajuste o estoque preventivamente.",
                metricas=None,
            ))

        # ── 4. Erosão de margem ──
        erosoes = dados_detectores.get("erosao_margem", [])
        if erosoes:
            top_erosao = erosoes[0]
            insights.append(Insight(
                hash=f"erosao_{len(erosoes)}_{int(abs(top_erosao.get('variacao_pp', 0)))}",
                tipo="margem_erosao",
                impacto="alto" if abs(top_erosao.get("variacao_pp", 0)) > 10 else "medio",
                titulo=f"{len(erosoes)} produtos com margem em queda",
                descricao=(
                    f"{top_erosao.get('nome', '?')} perdeu {abs(top_erosao.get('variacao_pp', 0)):.1f} pp de margem "
                    f"(de {top_erosao.get('margem_anterior', 0):.1f}% para {top_erosao.get('margem_atual', 0):.1f}%)."
                ),
                sugestao="Revise o preço de venda ou negocie custo com o fornecedor.",
                metricas=InsightMetricas(
                    margem_anterior=top_erosao.get("margem_anterior"),
                    margem_atual=top_erosao.get("margem_atual"),
                    variacao=top_erosao.get("variacao_pp"),
                ),
            ))

        # ── 5. Oportunidade B ──
        ops_b = dados_detectores.get("oportunidade_b", [])
        if ops_b:
            top_op = ops_b[0]
            insights.append(Insight(
                hash=f"oportunidade_b_{len(ops_b)}_{int(top_op.get('potencial_ganho_mensal', 0))}",
                tipo="oportunidade_b",
                impacto="medio",
                titulo=f"{len(ops_b)} itens classe B com potencial de crescimento",
                descricao=(
                    f"{top_op.get('nome', '?')} tem margem de {top_op.get('margem_atual', 0):.1f}% "
                    f"vs. {top_op.get('margem_media_a', 0):.1f}% da média A, "
                    f"com potencial de R$ {top_op.get('potencial_ganho_mensal', 0):,.2f}/mês."
                ),
                sugestao="Invista em exposição, marketing ou treinamento para impulsionar este produto.",
                metricas=InsightMetricas(
                    margem_b=top_op.get("margem_atual"),
                    margem_lider=top_op.get("margem_media_a"),
                    potencial_ganho_mensal=top_op.get("potencial_ganho_mensal"),
                ),
            ))

        # ── Resumo executivo ──
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
            gerado_em=utcnow(),
        )
