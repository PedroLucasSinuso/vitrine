"""Detector de encalhe — produtos sem venda nos últimos 30+ dias."""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo
from app.domain.models.produto import Produto

logger = logging.getLogger(__name__)

LIMITE_DIAS_PARADO = 30
LIMITE_ITENS = 15


class EncalheDetector(Detector):
    """Identifica produtos com estoque > 0 e sem venda nos últimos N dias."""

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        # 1. Busca todos os produtos ativos com estoque
        produtos = (
            db.query(Produto)
            .filter(Produto.ativo == True, Produto.estoque > 0)  # noqa: E712
            .all()
        )

        if not produtos:
            return []

        # 2. Busca transações do período para verificar quais produtos venderam
        periodo_inicio = data_fim - timedelta(days=LIMITE_DIAS_PARADO)
        transacoes = source.get_items(periodo_inicio, data_fim)

        # 3. Identifica códigos que venderam
        codigos_venderam: set[str] = set()
        codigo_para_codigo_chamada: dict[str, str] = {}

        for t in transacoes:
            cod = t.product_code
            codigos_venderam.add(cod)
            # Mapeia código para codigo_chamada (se disponível)
            if hasattr(t, "internal_code") and t.internal_code:
                codigo_para_codigo_chamada[cod] = t.internal_code

        # 4. Filtra produtos sem venda
        encalhados = []
        for p in produtos:
            # Verifica se algum código do produto está nas vendas
            codigos_produto = {c.codigo for c in p.codigos} if p.codigos else {p.codigo_chamada}
            if not codigos_produto.intersection(codigos_venderam):
                valor_estimado = float(p.preco_custo or 0) * float(p.estoque or 0)
                encalhados.append({
                    "codigo": p.codigo_chamada,
                    "nome": p.nome,
                    "grupo": p.grupo,
                    "estoque": float(p.estoque or 0),
                    "dias_parado": LIMITE_DIAS_PARADO,  # estimativa conservadora
                    "valor_estimado": round(valor_estimado, 2),
                })

        # 5. Ordena por valor estimado (decrescente) e limita
        encalhados.sort(key=lambda x: x["valor_estimado"], reverse=True)

        # 6. Remove grupos ignorados (USO PESSOAL, LOJA, etc)
        ignored = get_ignored_groups(db)
        encalhados = filtrar_por_grupo(encalhados, ignored)

        return encalhados[:LIMITE_ITENS]
