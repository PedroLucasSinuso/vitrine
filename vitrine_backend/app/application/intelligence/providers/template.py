"""Fallback determinístico — gera resposta sem IA usando templates Jinja2."""
from app.application.intelligence._utils import utcnow
from app.schemas.intelligence_schema import (
    IntelligenceResponse,
    Insight,
    InsightMetricas,
    ProdutoInsight,
)

MAX_PRODUTOS_POR_INSIGHT = 10


def _mapear_produtos(items: list[dict], tipo: str) -> list[ProdutoInsight]:
    """Mapeia resultados de detectores para ProdutoInsight."""
    mapeados = []
    for item in items[:MAX_PRODUTOS_POR_INSIGHT]:
        base = {
            "codigo": item.get("codigo", ""),
            "nome": item.get("nome", ""),
            "grupo": item.get("grupo"),
            "estoque": item.get("estoque"),
        }
        if tipo == "encalhe":
            base.update({
                "dias_parado": item.get("dias_parado"),
                "valor_estimado": item.get("valor_estimado"),
            })
        elif tipo == "taxa_troca":
            base.update({
                "taxa_troca": item.get("taxa"),
                "qtd_trocas": item.get("qtd_trocas"),
                "qtd_vendas": item.get("qtd_vendas"),
            })
        elif tipo == "sazonalidade":
            base.update({
                "crescimento_qtd": item.get("crescimento_qtd"),
                "qtd_anterior": item.get("qtd_anterior"),
                "qtd_atual": item.get("qtd_atual"),
                "valor_atual": item.get("valor_atual"),
            })
        elif tipo == "erosao_margem":
            base.update({
                "margem_anterior": item.get("margem_anterior"),
                "margem_atual": item.get("margem_atual"),
                "variacao_pp": item.get("variacao_pp"),
                "preco_medio_anterior": item.get("preco_medio_anterior"),
                "preco_medio_atual": item.get("preco_medio_atual"),
            })
        elif tipo == "oportunidade_b":
            base.update({
                "receita": item.get("receita"),
                "participacao": item.get("participacao"),
                "margem_b": item.get("margem_atual"),
                "margem_lider": item.get("margem_media_a"),
                "upside_margem": item.get("upside_margem"),
                "potencial_ganho_mensal": item.get("potencial_ganho_mensal"),
            })
        mapeados.append(ProdutoInsight(**base))
    return mapeados


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
            titulo = f"Revise {total} produtos sem venda há mais de 30 dias"
            insights.append(Insight(
                hash=f"encalhe_{total}_{int(valor_total)}_{hash(titulo)}",
                tipo="encalhe",
                impacto="alto" if valor_total > 10000 else "medio",
                titulo=titulo,
                descricao=f"{nomes} lideram o valor encalhado, totalizando R$ {valor_total:,.2f} em estoque parado.",
                sugestao="Considere promoção de queima de estoque ou devolução ao fornecedor.",
                metricas=InsightMetricas(
                    total_encalhados=total,
                    valor_total_encalhado=round(valor_total, 2),
                ),
                produtos=_mapear_produtos(encalhes, "encalhe"),
            ))

        # ── 2. Taxa de troca ──
        trocas = dados_detectores.get("taxa_troca", [])
        if trocas:
            top_troca = trocas[0]
            taxa_pct = top_troca.get("taxa", 0) * 100
            titulo_troca = f"{len(trocas)} produtos com alta taxa de troca/devolução"
            insights.append(Insight(
                hash=f"taxa_troca_{len(trocas)}_{int(taxa_pct*100)}_{hash(titulo_troca)}",
                tipo="taxa_troca",
                impacto="alto" if taxa_pct > 20 else "medio",
                titulo=titulo_troca,
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
                produtos=_mapear_produtos(trocas, "taxa_troca"),
            ))

        # ── 3. Sazonalidade ──
        sazonais = dados_detectores.get("sazonalidade", [])
        if sazonais:
            top_saz = sazonais[0]
            cresc_pct = top_saz.get("crescimento_qtd", 0) * 100
            titulo_saz = f"{len(sazonais)} produtos com crescimento acima de 30%"
            insights.append(Insight(
                hash=f"sazonalidade_{len(sazonais)}_{int(cresc_pct*100)}_{hash(titulo_saz)}",
                tipo="sazonalidade",
                impacto="medio",
                titulo=titulo_saz,
                descricao=(
                    f"{top_saz.get('nome', '?')} cresceu {cresc_pct:.0f}% nas vendas "
                    f"({int(top_saz.get('qtd_atual', 0))} uni. vs. {int(top_saz.get('qtd_anterior', 0))} uni. no período anterior)."
                ),
                sugestao="Avalie se é demanda sazonal genuína e ajuste o estoque preventivamente.",
                metricas=None,
                produtos=_mapear_produtos(sazonais, "sazonalidade"),
            ))

        # ── 4. Erosão de margem ──
        erosoes = dados_detectores.get("erosao_margem", [])
        if erosoes:
            top_erosao = erosoes[0]
            titulo_erosao = f"{len(erosoes)} produtos com margem em queda"
            insights.append(Insight(
                hash=f"erosao_{len(erosoes)}_{int(abs(top_erosao.get('variacao_pp', 0)))}_{hash(titulo_erosao)}",
                tipo="margem_erosao",
                impacto="alto" if abs(top_erosao.get("variacao_pp", 0)) > 10 else "medio",
                titulo=titulo_erosao,
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
                produtos=_mapear_produtos(erosoes, "erosao_margem"),
            ))

        # ── 5. Oportunidade B ──
        ops_b = dados_detectores.get("oportunidade_b", [])
        if ops_b:
            top_op = ops_b[0]
            titulo_opb = f"{len(ops_b)} itens classe B com potencial de crescimento"
            insights.append(Insight(
                hash=f"oportunidade_b_{len(ops_b)}_{int(top_op.get('potencial_ganho_mensal', 0))}_{hash(titulo_opb)}",
                tipo="oportunidade_b",
                impacto="medio",
                titulo=titulo_opb,
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
                produtos=_mapear_produtos(ops_b, "oportunidade_b"),
            ))

        # ── 6. Macro Contexto ──
        macro_items = dados_detectores.get("macro_contexto", [])
        for item in macro_items:
            tipo = item.get("tipo", "macro_contexto")
            titulo = item.get("titulo", "")
            hash_val = f"{tipo}_{hash(titulo)}"
            metricas = InsightMetricas(
                valor_indicador=item.get("valor_indicador"),
                variacao_ticket=item.get("variacao_ticket"),
                variacao_faturamento=item.get("variacao_faturamento"),
                chave_indicador=item.get("chave_indicador"),
            )
            insights.append(Insight(
                hash=hash_val,
                tipo="macro_contexto",
                impacto=item.get("impacto", "medio"),
                confianca="alta",
                titulo=titulo,
                descricao=item.get("descricao", ""),
                sugestao=item.get("sugestao", ""),
                metricas=metricas,
                produtos=[],
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
