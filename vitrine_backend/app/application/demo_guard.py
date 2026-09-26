"""Guard do modo de demonstração.

A demo é pública e o visitante entra como admin — pode abrir sessão de
inventário, editar configuração, mexer no catálogo. Nada disso pode
sobreviver para o próximo visitante, então o reset não é tarefa de
operação (um cron no VPS): é parte do produto.

São duas camadas, porque uma só não cobre:

- **Na entrada**, quando o último reset passou do cooldown. É o que
  garante que ninguém herde a bagunça do anterior. O cooldown evita
  resetar a cada clique quando várias pessoas entram ao mesmo tempo —
  sem ele, dois recrutadores simultâneos derrubariam a sessão um do
  outro a cada request.
- **Periódica**, para a demo não ficar suja indefinidamente quando
  ninguém entra depois de alguém ter mexido.

O relógio do último reset vive no processo, não no banco: com mais de um
worker cada um reseta por conta, o que no pior caso limpa mais vezes do
que o necessário — nunca menos. Errar para o lado de limpar demais é o
lado certo aqui.
"""

import logging
import threading
import time

from app.application.demo_provisioner import (
    SLUG_DEMO,
    DemoError,
    resetar_demo,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

JOB_ID_RESET_DEMO = "reset_demo"

_lock = threading.Lock()
_ultimo_reset: float | None = None
_ultimos_por_slug: dict[str, float] = {}


def _ultimo(slug: str) -> float | None:
    return _ultimo_reset if slug == SLUG_DEMO else _ultimos_por_slug.get(slug)


def _marcar(slug: str, momento: float) -> None:
    global _ultimo_reset
    if slug == SLUG_DEMO:
        _ultimo_reset = momento
    else:
        _ultimos_por_slug[slug] = momento


def _cooldown_segundos() -> float:
    return max(settings.demo_reset_cooldown_minutes, 0) * 60


def marcar_resetado(momento: float | None = None, slug: str = SLUG_DEMO) -> None:
    """Registra que a demo acabou de ser resetada por outro caminho.

    O ``provisionar-demo`` deixa o tenant no estado inicial; sem isto o
    primeiro visitante dispararia um reset redundante.
    """
    with _lock:
        _marcar(slug, time.monotonic() if momento is None else momento)


def resetar_se_necessario(slug: str = SLUG_DEMO) -> bool:
    """Reseta a demo se ela não estiver fresca. Devolve se resetou.

    Silencia ``DemoError``: a entrada na demo não pode falhar porque o
    reset falhou — pior um visitante ver dado sujo do que uma tela de
    erro. A falha vai para o log.
    """
    with _lock:
        agora = time.monotonic()
        ultimo = _ultimo(slug)
        if ultimo is not None and (agora - ultimo) < _cooldown_segundos():
            return False
        # Marca antes de resetar: se outro request chegar enquanto este
        # ainda está limpando, ele vê a demo como fresca e segue direto,
        # em vez de enfileirar um segundo reset no mesmo lock.
        _marcar(slug, agora)

    try:
        resetar_demo(slug)
        return True
    except DemoError as exc:
        logger.warning("Reset da demo falhou, seguindo com os dados atuais | %s", exc)
        return False


def _reset_periodico(slug: str) -> None:
    try:
        resetar_demo(slug)
        marcar_resetado(slug=slug)
        logger.info("Demo resetada pelo job periódico | slug=%s", slug)
    except DemoError as exc:
        logger.warning("Job periódico de reset da demo falhou | %s", exc)


def agendar_reset_periodico(scheduler, slug: str = SLUG_DEMO) -> None:
    """Agenda a limpeza periódica da demo.

    Não faz nada se o intervalo for <= 0, que é como se desliga a camada
    periódica sem desligar o reset na entrada.
    """
    minutos = settings.demo_reset_interval_minutes
    if minutos <= 0:
        logger.info("Reset periódico da demo desligado (intervalo=%s)", minutos)
        return

    scheduler.add_job(
        lambda: _reset_periodico(slug),
        trigger="interval",
        minutes=minutos,
        id=JOB_ID_RESET_DEMO if slug == SLUG_DEMO else f"{JOB_ID_RESET_DEMO}:{slug}",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Reset periódico da demo agendado | a cada %d min", minutos)
