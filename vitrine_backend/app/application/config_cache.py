"""Cache TTL para configurações — isolado para evitar acoplamento no config_service.py.

Thread-safe via ``threading.Lock``. TTL de 30s evita leitura excessiva
do banco sem os problemas de invalidação manual entre workers.
"""

import threading
from datetime import datetime, timezone

logger = __import__("logging").getLogger(__name__)

# Cache leve com TTL (segundos) — evita ler do banco a cada chamada,
# mas sem os problemas de invalidação manual entre workers.
# Thread lock protege contra race condition em _cache.clear() + _cache[]
_cache: dict[str, tuple[str, float]] = {}
_cache_lock: threading.Lock = threading.Lock()
CACHE_TTL = 30


def get_from_cache(chave: str, now: float | None = None) -> str | None:
    """Retorna valor do cache se válido (dentro do TTL).

    Args:
        chave: Nome da chave.
        now: Timestamp atual (opcional, calculado internamente se omitido).

    Returns:
        Valor em cache ou ``None`` se não encontrado ou expirado.
    """
    if now is None:
        now = datetime.now(timezone.utc).timestamp()
    with _cache_lock:
        cached = _cache.get(chave)
        if cached is not None and (now - cached[1]) < CACHE_TTL:
            return cached[0]
    return None


def set_in_cache(chave: str, valor: str, now: float | None = None) -> None:
    """Armazena valor no cache com timestamp atual.

    Args:
        chave: Nome da chave.
        valor: Valor a ser armazenado.
        now: Timestamp atual (opcional).
    """
    if now is None:
        now = datetime.now(timezone.utc).timestamp()
    with _cache_lock:
        _cache[chave] = (valor, now)


def invalidate_cache() -> None:
    """Limpa todo o cache interno. Thread-safe."""
    with _cache_lock:
        _cache.clear()
