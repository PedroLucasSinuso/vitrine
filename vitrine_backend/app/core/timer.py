import time
import logging
from contextlib import contextmanager
from collections.abc import Generator


@contextmanager
def temporizador(nome: str, logger: logging.Logger = logging.getLogger(__name__)) -> Generator[None, None, None]:
    inicio = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - inicio
        logger.info("[TIMING] %s | duracao=%.2fs", nome, elapsed)
