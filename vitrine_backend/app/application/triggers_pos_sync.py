"""Triggers executados após cada sync bem-sucedido.

Atualmente:
- margem_negativa: detecta produtos com custo > preço de venda
- futuro: encalhe_severo, sync_lento

Usa TransactionSource (adapter) para consultas no PostgreSQL — sem SQL hardcoded.
"""

import json
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.application.intelligence._utils import format_brl
from app.application.notificacao_service import (
    criar_notificacao,
    resolver_notificacao,
)
from app.core.interfaces.source import TransactionSource

logger = logging.getLogger(__name__)

LIMIAR_CLASSE_A = 0.80  # 80% da receita acumulada
DIAS_ATIVO = 90          # guard clause: produto com venda em 90d é "ativo no mercado"
DIAS_ANALISE = 30        # período real de cálculo da receita


def _obter_source(db: Session) -> TransactionSource | None:
    """Cria TransactionSource a partir do engine configurado no SQLite."""
    try:
        from app.application.erp_factory import create_transaction_source
        return create_transaction_source(db)
    except Exception:
        logger.exception("Falha ao criar TransactionSource para margem negativa")
        return None


def verificar_margem_negativa(
    db_sqlite: Session,
    source: TransactionSource | None = None,
) -> None:
    """Verifica produtos com margem negativa e cria/atualiza notificação.

    Usa TransactionSource (adapter) — sem SQL hardcado.
    Se ``source`` não for fornecido, cria um a partir do engine configurado.

    Fluxo:
    1. Guard clause: produtos com venda nos últimos 90d (conjunto ativo)
    2. Receita dos últimos 30d apenas para o conjunto ativo
    3. Filtra grupos ignorados (config ``ignored_groups``)
    4. Classifica produtos A (80% receita)
    5. Cruza com dados do SQLite (preco_venda, preco_custo)
    6. Cria notificação se encontrar produtos com margem negativa
    """
    if source is None:
        source = _obter_source(db_sqlite)
    if source is None:
        logger.warning("TransactionSource indisponível — pulando verificação de margem")
        return

    hoje = date.today()
    guarda_inicio = hoje - timedelta(days=DIAS_ATIVO)
    analise_inicio = hoje - timedelta(days=DIAS_ANALISE)

    try:
        # ── 1. Guard clause: produtos ativos nos últimos 90d ────────────────
        ativos_raw = source.get_dimensao_aggregates(
            guarda_inicio, hoje, "produto", "receita",
        )
        if not ativos_raw:
            logger.info(
                "Nenhum produto ativo nos últimos %d dias — pulando", DIAS_ATIVO,
            )
            return

        codigos_ativos = {p["codigo"] for p in ativos_raw}
        logger.info(
            "Guard clause 90d: %d produtos com venda no período", len(codigos_ativos),
        )

        # ── 2. Receita dos últimos 30d (apenas ativos) ──────────────────────
        receita_raw = source.get_dimensao_aggregates(
            analise_inicio, hoje, "produto", "receita",
        )
        if not receita_raw:
            logger.info("Nenhuma receita nos últimos %d dias — pulando", DIAS_ANALISE)
            return

        # Normaliza field names do adapter → nomenclatura interna
        receita_produtos = [
            {
                "codigo_chamada": p["codigo"],
                "nome": p.get("produto", ""),
                "grupo": p.get("grupo", ""),
                "receita": float(p.get("valor", 0)),
            }
            for p in receita_raw
            if p["codigo"] in codigos_ativos
        ]

        if not receita_produtos:
            logger.info("Nenhum produto ativo com receita nos últimos %d dias — pulando", DIAS_ANALISE)
            return

        # ── 3. Filtra grupos ignorados (blacklist) ──────────────────────────
        from app.application.intelligence.filtros import get_ignored_groups
        ignored = get_ignored_groups(db_sqlite)
        if ignored:
            antes = len(receita_produtos)
            receita_produtos = [
                p for p in receita_produtos
                if p.get("grupo", "").strip().upper() not in ignored
            ]
            logger.info("Ignored groups filtrou %d → %d produtos", antes, len(receita_produtos))

        if not receita_produtos:
            logger.info("Todos os produtos foram filtrados por ignored_groups — pulando")
            return

        # ── 4. Classifica produtos A ────────────────────────────────────────
        produtos_a = _classificar_a(receita_produtos)
        if not produtos_a:
            logger.info("Nenhum produto classe A com margem negativa — pulando")
            return

        # ── 5. Cruza com margem do SQLite ───────────────────────────────────
        problematicos = _cruzar_margem_sqlite(db_sqlite, produtos_a)
        total_problematicos = len(problematicos)

        if total_problematicos == 0:
            resolvidos = resolver_notificacao(db_sqlite, "margem_negativa")
            if resolvidos > 0:
                logger.info("Margem negativa resolvida — %s notificações fechadas", resolvidos)
            return

        # ── 6. Cria notificação consolidada ─────────────────────────────────
        valor_impacto = sum(
            p["quantidade"] * (p["preco_custo"] - p["preco_venda"])
            for p in problematicos
        )
        top5 = [p["nome"] for p in problematicos[:5] if p.get("nome")]

        titulo = f"[ALERTA] {total_problematicos} produtos com margem negativa"
        mensagem = (
            f"{total_problematicos} produtos estão sendo vendidos com custo "
            f"maior que o preço. {format_brl(valor_impacto)} de impacto estimado por mês."
        )
        if top5:
            mensagem += f"\n\nPrincipais: {', '.join(top5)}"
        mensagem += (
            "\n\nIsso geralmente indica cadastro incorreto no ERP "
            "(custo de lote vs. unitário, ou preço desatualizado). "
            "Revisar cadastro dos produtos afetados."
        )

        criar_notificacao(
            db_sqlite,
            tipo="margem_negativa",
            titulo=titulo,
            mensagem=mensagem,
            dados_json={
                "total": total_problematicos,
                "valor_impacto": round(valor_impacto, 2),
                "top5": top5,
                "itens": problematicos,
            },
        )

    except Exception:
        logger.exception("Erro na verificação de margem negativa pós-sync")


def verificar_erro_sync(db_sqlite: Session, erro: str | None = None) -> None:
    """Cria notificação de erro de sync."""
    if erro:
        criar_notificacao(
            db_sqlite,
            tipo="sync_erro",
            titulo="Sync ERP falhou",
            mensagem=(
                f"O sync com o ERP falhou: {erro}\n\n"
                "Verifique a conectividade com o servidor Alterdata "
                "e tente novamente."
            ),
            dados_json={"erro": erro},
        )
    else:
        resolver_notificacao(db_sqlite, "sync_erro")


# ── Helpers internos (sem SQL, só manipulação de dados) ─────────────────────


def _classificar_a(produtos: list[dict]) -> list[dict]:
    """Filtra apenas produtos classe A (80% receita acumulada)."""
    if not produtos:
        return []
    total = sum(p["receita"] for p in produtos)
    if total == 0:
        return []
    acumulado = 0.0
    classe_a = []
    for p in sorted(produtos, key=lambda x: x["receita"], reverse=True):
        acumulado += p["receita"]
        classe_a.append(p)
        if acumulado / total >= LIMIAR_CLASSE_A:
            break
    return classe_a


def _cruzar_margem_sqlite(
    db_sqlite: Session,
    produtos_a: list[dict],
) -> list[dict]:
    """Cruza produtos A com dados de margem do SQLite.

    Retorna apenas produtos com preco_custo > preco_venda.
    """
    from app.domain.models.produto import Produto

    codigos = [p["codigo_chamada"] for p in produtos_a]
    if not codigos:
        return []

    orm_produtos = (
        db_sqlite.query(Produto)
        .filter(
            Produto.codigo_chamada.in_(codigos),
            Produto.preco_venda > 0,
        )
        .all()
    )

    produto_map = {p.codigo_chamada: p for p in orm_produtos}

    problematicos = []
    for item in produtos_a:
        cod = item["codigo_chamada"]
        orm = produto_map.get(cod)
        if orm is None:
            continue
        margem = (orm.preco_venda - orm.preco_custo) / orm.preco_venda
        if margem < 0:
            problematicos.append({
                "codigo": cod,
                "nome": orm.nome or item.get("nome", ""),
                "grupo": orm.grupo or "",
                "preco_venda": orm.preco_venda,
                "preco_custo": orm.preco_custo,
                "margem": round(margem * 100, 2),
                "quantidade": orm.estoque or 0,
                "receita": round(item["receita"], 2),
            })

    problematicos.sort(key=lambda x: x["receita"], reverse=True)
    return problematicos
