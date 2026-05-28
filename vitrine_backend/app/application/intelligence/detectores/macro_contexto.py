"""Detector that cross-references macro-economic indicators with store KPIs."""

import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.application.intelligence.detectores.base import Detector
from app.core.interfaces.source import TransactionSource
from app.application.intelligence.macro_fetcher import fetch_todos_indicadores
from app.application.bi.factory import calcular_kpis_rapido

# ── Module-level constants (no hardcoded values in logic) ──
LIMITE_INSIGHTS = 5
LIMIAR_SELIC_ALTA = 10.0       # Selic acima deste valor é considerado alto
LIMIAR_IPCA_ALIMENTACAO = 3.0  # IPCA alimentação acima deste valor dispara alerta de ticket
LIMIAR_IGPM_ALTO = 5.0         # IGP-M acima deste valor sugere revisão de contratos
LIMIAR_DESEMPREGO_ALTO = 12.0  # Desemprego acima deste valor sugere cautela
LIMIAR_IPCA_GERAL = 4.0        # IPCA geral acima deste valor acende alerta de faturamento real


class MacroContextoDetector(Detector):
    """Gera insights macroeconômicos para contextualizar desempenho da loja."""

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        indicadores = asyncio.run(fetch_todos_indicadores(db))
        kpis = calcular_kpis_rapido(source, data_inicio, data_fim)

        # KPI do período anterior para comparação
        dias_periodo = (data_fim - data_inicio).days
        data_inicio_ant = data_inicio - timedelta(days=dias_periodo)
        data_fim_ant = data_inicio - timedelta(days=1)
        kpis_ant = calcular_kpis_rapido(source, data_inicio_ant, data_fim_ant)

        insights = []

        # Insight 1: Selic alta -> custo de capital de giro elevado
        selic = indicadores.get("selic_meta")
        if selic and selic.disponivel and selic.valor is not None and selic.valor > LIMIAR_SELIC_ALTA:
            consultado = (
                selic.consultado_em.strftime("%d/%m/%Y às %H:%M")
                if selic.consultado_em
                else "—"
            )
            insights.append({
                "tipo": "macro_selic",
                "titulo": f"Selic a {selic.valor:.2f}% — capital de giro mais caro",
                "descricao": (
                    f"A Selic está em {selic.valor:.2f}% ao ano (consultado em "
                    f"{consultado}). "
                    f"Em patamares elevados, o custo de manter estoques parados aumenta significativamente."
                ),
                "sugestao": (
                    "Priorize a redução de encalhes e negocie prazos com fornecedores "
                    "para liberar caixa. Avalie o custo real do capital de giro nas suas margens."
                ),
                "impacto": "alto",
                "chave_indicador": "selic_meta",
                "valor_indicador": selic.valor,
            })

        # Insight 2: IPCA Alimentação vs ticket médio
        ipca_ali = indicadores.get("ipca_alimentacao_12m")
        if (
            ipca_ali and ipca_ali.disponivel and ipca_ali.valor is not None
            and ipca_ali.valor > LIMIAR_IPCA_ALIMENTACAO
        ):
            if (
                kpis and kpis_ant
                and kpis.ticket_medio and kpis_ant.ticket_medio
                and kpis_ant.ticket_medio > 0
            ):
                variacao_ticket = (
                    (kpis.ticket_medio - kpis_ant.ticket_medio) / kpis_ant.ticket_medio
                ) * 100
                if variacao_ticket < ipca_ali.valor:
                    insights.append({
                        "tipo": "macro_ipca_ticket",
                        "titulo": (
                            f"Ticket médio abaixo da inflação de alimentos "
                            f"({ipca_ali.valor:.1f}%)"
                        ),
                        "descricao": (
                            f"O IPCA de Alimentação acumulou {ipca_ali.valor:.1f}% nos últimos 12 meses "
                            f"({ipca_ali.periodo_ref_rotulo or ipca_ali.periodo_ref}). "
                            f"Seu ticket médio variou apenas {variacao_ticket:.1f}% no mesmo período — "
                            f"uma perda de poder de compra de "
                            f"{ipca_ali.valor - variacao_ticket:.1f} pontos percentuais."
                        ),
                        "sugestao": (
                            "Revise a precificação dos produtos mais impactados pela inflação de insumos. "
                            "Considere upsell ou combos para elevar o ticket médio."
                        ),
                        "impacto": "alto",
                        "chave_indicador": "ipca_alimentacao_12m",
                        "valor_indicador": ipca_ali.valor,
                        "variacao_ticket": round(variacao_ticket, 2),
                    })

        # Insight 3: IGP-M alto sugere revisão de contratos
        igpm = indicadores.get("igpm_12m")
        if igpm and igpm.disponivel and igpm.valor is not None and igpm.valor > LIMIAR_IGPM_ALTO:
            insights.append({
                "tipo": "macro_igpm",
                "titulo": f"IGP-M acumula {igpm.valor:.1f}% — custos fixos sob pressão",
                "descricao": (
                    f"O IGP-M atingiu {igpm.valor:.1f}% em 12 meses "
                    f"({igpm.periodo_ref_rotulo or igpm.periodo_ref}). "
                    f"Este índice impacta diretamente aluguéis, energia e contratos de prestação de serviços."
                ),
                "sugestao": (
                    "Revise contratos de aluguel e fornecedores indexados ao IGP-M. "
                    "Avalie a possibilidade de migrar para IPCA ou índice fixo nas próximas renovações."
                ),
                "impacto": "medio",
                "chave_indicador": "igpm_12m",
                "valor_indicador": igpm.valor,
            })

        # Insight 4: Desemprego alto sugere cautela
        desemprego = indicadores.get("desemprego")
        if (
            desemprego and desemprego.disponivel
            and desemprego.valor is not None
            and desemprego.valor > LIMIAR_DESEMPREGO_ALTO
        ):
            insights.append({
                "tipo": "macro_desemprego",
                "titulo": f"Desemprego a {desemprego.valor:.1f}% — consumidor cauteloso",
                "descricao": (
                    f"A taxa de desemprego está em {desemprego.valor:.1f}% "
                    f"({desemprego.periodo_ref_rotulo or desemprego.periodo_ref}). "
                    f"Em cenários de desemprego elevado, o consumidor tende a reduzir gastos supérfluos "
                    f"e buscar substituições por marcas mais baratas."
                ),
                "sugestao": (
                    "Reforce a oferta de produtos de entrada e marcas próprias. "
                    "Avalie promoções direcionadas para manter o fluxo de clientes."
                ),
                "impacto": "medio",
                "chave_indicador": "desemprego",
                "valor_indicador": desemprego.valor,
            })

        # Insight 5: IPCA geral (visão ampla) vs faturamento
        ipca = indicadores.get("ipca_12m")
        if ipca and ipca.disponivel and ipca.valor is not None and ipca.valor > LIMIAR_IPCA_GERAL:
            if (
                kpis and kpis_ant
                and kpis.faturamento_bruto and kpis_ant.faturamento_bruto
                and kpis_ant.faturamento_bruto > 0
            ):
                variacao_fat = (
                    (kpis.faturamento_bruto - kpis_ant.faturamento_bruto)
                    / kpis_ant.faturamento_bruto
                ) * 100
                if variacao_fat < ipca.valor:
                    insights.append({
                        "tipo": "macro_ipca_geral",
                        "titulo": (
                            f"Faturamento real negativo frente ao IPCA "
                            f"({ipca.valor:.1f}%)"
                        ),
                        "descricao": (
                            f"O IPCA geral acumulou {ipca.valor:.1f}% em 12 meses "
                            f"({ipca.periodo_ref_rotulo or ipca.periodo_ref}). "
                            f"Seu faturamento nominal cresceu {variacao_fat:.1f}% — "
                            f"queda real de {ipca.valor - variacao_fat:.1f}%."
                        ),
                        "sugestao": (
                            "Analise o volume de vendas: o crescimento nominal pode estar mascarando "
                            "queda real. Acompanhe indicadores de quantidade e ticket separadamente."
                        ),
                        "impacto": "medio",
                        "chave_indicador": "ipca_12m",
                        "valor_indicador": ipca.valor,
                        "variacao_faturamento": round(variacao_fat, 2),
                    })

        return insights[:LIMITE_INSIGHTS]
