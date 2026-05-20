from app.core.models.transaction import OperationType


class CodigoOperacao:
    """Códigos de operação específicos do Alterdata.
    ÚNICO lugar do sistema que conhece esses valores."""
    PERDA = "0RR000000E"
    CONSUMO_INTERNO = "0103430GOE"


CANCELED_MARKER = "*"

OPERATION_MAP: dict[tuple[str, str | None], OperationType] = {
    ("V", None):                            OperationType.SALE,
    ("V", ""):                              OperationType.SALE,
    ("E", "T"):                             OperationType.RETURN,
    ("E", "D"):                             OperationType.RETURN,
    ("S", CodigoOperacao.PERDA):            OperationType.LOSS,
    ("S", CodigoOperacao.CONSUMO_INTERNO):  OperationType.CONSUMPTION,
}
