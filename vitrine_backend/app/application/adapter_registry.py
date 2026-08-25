"""Registry de adapters de ERP.

Cada ERP suportado registra aqui um ``AdapterEntry`` — o conjunto de
funções que sabem construir as fontes de dados daquele ERP para uma
empresa. É isso que permite plugar um ERP novo sem tocar em ``deps.py``
nem em ``erp_factory.py``.

Por que funções e não classes: cada adapter tem necessidade de construção
diferente. O Alterdata precisa de um ``Engine`` SQLAlchemy montado a partir
da config (criptografada) daquele tenant; o adapter de demo não precisa de
nada. Registrar classes obrigaria o chamador a saber o que cada construtor
espera — que é exatamente o acoplamento que o Adapter Pattern existe para
evitar.

O registro dos adapters nativos é LAZY (ver ``_carregar_builtins``):
``app/adapters/alterdata/db.py`` importa ``config_service``, que vive em
``application`` — importar os adapters no topo deste módulo criaria ciclo.
"""

from __future__ import annotations

import logging
import threading
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy.orm import Session

from app.core.interfaces.source import ProductSource, TransactionSource

logger = logging.getLogger(__name__)


class AdapterNaoRegistradoError(LookupError):
    """ERP configurado para a empresa não corresponde a nenhum adapter."""


def _sem_efeito() -> None:
    """Hook padrão de fim de sync — adapters sem cache não fazem nada."""


@dataclass(frozen=True)
class AdapterEntry:
    """Como construir as fontes de dados de um ERP para uma empresa.

    Args:
        nome: Identificador usado na configuração ``erp_adapter``.
        criar_product_source: Fábrica de ``ProductSource`` da empresa.
        criar_transaction_source: Fábrica de ``TransactionSource`` da empresa.
        abrir_sync_source: Context manager que entrega o ``ProductSource``
            do sync e cuida do ciclo de vida de recursos caros (o Alterdata
            descarta o engine na saída; o demo não tem o que descartar).
        ao_terminar_sync: Chamado depois de um sync bem-sucedido, para o
            adapter invalidar caches próprios.
    """

    nome: str
    criar_product_source: Callable[[Session, int], ProductSource]
    criar_transaction_source: Callable[[Session, int], TransactionSource]
    abrir_sync_source: Callable[[Session, int, int], AbstractContextManager[ProductSource]]
    ao_terminar_sync: Callable[[], None] = field(default=_sem_efeito)


_REGISTRY: dict[str, AdapterEntry] = {}
_LOCK = threading.Lock()
_builtins_carregados = False


def register_adapter(entry: AdapterEntry) -> None:
    """Registra (ou substitui) o adapter de um ERP."""
    _REGISTRY[entry.nome] = entry
    logger.info("Adapter registrado | erp=%s", entry.nome)


def adapters_disponiveis() -> list[str]:
    """Nomes de ERP registrados, em ordem alfabética."""
    _carregar_builtins()
    return sorted(_REGISTRY)


def get_adapter(nome: str) -> AdapterEntry:
    """Retorna o adapter registrado sob ``nome``.

    Raises:
        AdapterNaoRegistradoError: se o nome não corresponder a nenhum
            adapter — normalmente um ``erp_adapter`` digitado errado na
            configuração da empresa.
    """
    _carregar_builtins()
    try:
        return _REGISTRY[nome]
    except KeyError:
        disponiveis = ", ".join(sorted(_REGISTRY)) or "nenhum"
        raise AdapterNaoRegistradoError(
            f"Adapter de ERP não registrado: {nome!r}. Disponíveis: {disponiveis}."
        ) from None


def _carregar_builtins() -> None:
    """Importa e registra os adapters nativos, uma única vez.

    Lazy de propósito (ver docstring do módulo): os adapters importam
    ``config_service``, que é da mesma camada deste registry.
    """
    global _builtins_carregados
    if _builtins_carregados:
        return
    with _LOCK:
        if _builtins_carregados:
            return
        from app.adapters.alterdata import ENTRY as ALTERDATA_ENTRY
        from app.adapters.demo import ENTRY as DEMO_ENTRY

        register_adapter(ALTERDATA_ENTRY)
        register_adapter(DEMO_ENTRY)
        _builtins_carregados = True
