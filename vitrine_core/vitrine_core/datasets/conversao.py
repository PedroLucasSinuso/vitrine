from vitrine_core.datasets.tipos import ItemVenda, Operacao
from vitrine_core.models.transaction import OperationType, TransactionItem

_OPERACOES = {OperationType.SALE: Operacao.VENDA, OperationType.RETURN: Operacao.TROCA}


def itens_de_transacoes(transacoes: list[TransactionItem]) -> list[ItemVenda]:
    return [
        ItemVenda(
            documento=t.document_id,
            data=t.date,
            operacao=_OPERACOES[t.operation],
            quantidade=abs(t.quantity),
            valor=abs(t.line_total),
            produto=t.product_name,
            codigo_produto=t.product_code,
            grupo=t.group_name,
            familia=t.family_name,
        )
        for t in transacoes
        if not t.is_canceled and t.operation in _OPERACOES
    ]
