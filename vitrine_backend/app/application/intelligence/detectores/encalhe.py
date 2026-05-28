"""Detector de encalhe — produtos ativos que pararam de vender.

Evolução do detector (2026-05-28):
  ANTES:   Comparava TODOS os 12k SKUs do SQLite com vendas de 30 dias.
           SKUs mortos (sem movimentação há meses) poluíam o resultado.

  AGORA:   1. Busca TODAS as operações (venda + devolução + perda + consumo)
              dos últimos 90 dias no PostgreSQL para definir o CONJUNTO ATIVO
              (SKUs que de fato estão no mercado da loja).
           2. Busca SÓ VENDAS dos últimos 30 dias.
           3. Encalhe = produto com estoque > 1, ativo em 90 dias,
              que NÃO vendeu nos últimos 30 dias.
           4. SKUs sem nenhuma movimentação em 90 dias são ignorados
              (considerados mortos/defasados — não fazem parte do sortimento atual).
           5. dias_parado é calculado REAL (não mais hardcoded em 30).
"""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo
from app.domain.models.produto import Produto

logger = logging.getLogger(__name__)

LIMITE_ITENS = 15
DIAS_ATIVO = 90       # janela para definir "produto ativo no mercado"
DIAS_SEM_VENDA = 30   # janela para definir "parou de vender"


class EncalheDetector(Detector):
    """Identifica produtos ativos (movimentaram em 90d) que pararam de vender (30d sem venda)."""

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        # 1. Produtos do catálogo (SQLite)
        produtos = (
            db.query(Produto)
            .filter(Produto.ativo == True, Produto.estoque > 1)  # noqa: E712
            .all()
        )
        if not produtos:
            return []

        # 2. Busca TODAS as operações dos últimos 90 dias (PostgreSQL)
        periodo_90d = data_fim - timedelta(days=DIAS_ATIVO)
        transacoes_90d = source.get_items(periodo_90d, data_fim)

        # 3. Constrói conjuntos
        ativos_90d: set[str] = set()             # SKU com qq movimentação em 90d
        ultima_venda: dict[str, date] = {}        # SKU -> última data de venda
        venderam_30d: set[str] = set()            # SKU com venda nos últimos 30d
        periodo_30d = data_fim - timedelta(days=DIAS_SEM_VENDA)

        for t in transacoes_90d:
            cod = t.product_code

            # Só SALE indica que o produto está ativo no mercado.
            # LOSS (perda), CONSUMPTION (consumo interno) e RETURN (devolução
            # isolada) não significam que o produto faz parte do sortimento atual.
            if t.operation == OperationType.SALE:
                ativos_90d.add(cod)
                if cod not in ultima_venda or t.date > ultima_venda[cod]:
                    ultima_venda[cod] = t.date
                if t.date >= periodo_30d:
                    venderam_30d.add(cod)

        if not ativos_90d:
            return []

        # 4. Filtra encalhados
        encalhados = []
        for p in produtos:
            codigos_produto = {c.codigo for c in p.codigos} if p.codigos else {p.codigo_chamada}

            # Ignora SKUs sem movimentação em 90 dias (mortos/defasados)
            if not codigos_produto.intersection(ativos_90d):
                continue

            # Ignora SKUs que venderam nos últimos 30 dias
            if codigos_produto.intersection(venderam_30d):
                continue

            # Calcula dias parado real
            cod_ultima_venda = next((c for c in codigos_produto if c in ultima_venda), None)
            if cod_ultima_venda:
                dias_parado = (data_fim - ultima_venda[cod_ultima_venda]).days
            else:
                # Teve movimentação (ex: devolução) mas nenhuma venda em 90d.
                # O mínimo é 90 — pode ser mais, mas não temos o dado histórico.
                dias_parado = DIAS_ATIVO

            valor_estimado = float(p.preco_custo or 0) * float(p.estoque or 0)
            encalhados.append({
                "codigo": p.codigo_chamada,
                "nome": p.nome,
                "grupo": p.grupo,
                "estoque": float(p.estoque or 0),
                "dias_parado": dias_parado,
                "valor_estimado": round(valor_estimado, 2),
            })

        # 5. Ordena por valor estimado (decrescente)
        encalhados.sort(key=lambda x: x["valor_estimado"], reverse=True)

        # 6. Remove grupos ignorados
        ignored = get_ignored_groups(db)
        encalhados = filtrar_por_grupo(encalhados, ignored)

        return encalhados[:LIMITE_ITENS]
