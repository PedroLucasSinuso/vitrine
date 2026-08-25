import logging
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.api.routes import produto, cache_status
from app.api.routes import auth
from app.api.routes import admin
from app.api.routes import bi
from app.api.routes import configuracoes
from app.api.routes import inventario
from app.api.routes import whatsapp
from app.api.routes import email as email_routes
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.application.scheduler import iniciar_scheduler, parar_scheduler
from app.application.scheduler_manager import (
    init_scheduler_manager,
    reagendar_etl,
)
from app.application.notifications.scheduler_notifications import (
    iniciar_scheduler_notificacoes,
    ler_config_etl_interval,
)
from app.application.sync_service import run_sync_scheduled
from app.infrastructure.db.bootstrap import init_db, acquire_scheduler_lock

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Scheduler lock: apenas um worker por vez agenda jobs.
    # Evita execução duplicada de sync/notificações com --workers N.
    scheduler = None
    if acquire_scheduler_lock():
        scheduler = iniciar_scheduler()
        init_scheduler_manager(scheduler)

        # Um job de ETL por empresa ativa, cada um com seu próprio
        # intervalo configurado (ver app/application/scheduler_manager.py).
        from app.infrastructure.db.session import SqliteSession
        from app.domain.models.empresa import Empresa
        with SqliteSession() as _session:
            _empresa_ids = [
                e.id for e in
                _session.query(Empresa).filter(Empresa.status == "ativa").all()
            ]
        for _empresa_id in _empresa_ids:
            etl_min = ler_config_etl_interval(_empresa_id)
            reagendar_etl(
                _empresa_id, etl_min,
                lambda eid=_empresa_id: run_sync_scheduled(empresa_id=eid),
            )

        iniciar_scheduler_notificacoes(scheduler)

        # Limpeza periódica do tenant de demonstração, quando existe um.
        # O reset também acontece na entrada (ver demo_guard); este job
        # cobre a demo que ficou suja e ninguém mais visitou.
        from app.application.demo_guard import agendar_reset_periodico
        from app.application.demo_provisioner import empresa_demo
        with SqliteSession() as _session:
            _tem_demo = empresa_demo(_session) is not None
        if _tem_demo:
            agendar_reset_periodico(scheduler)
    else:
        logger.warning("Scheduler lock não adquirido — jobs não serão agendados neste worker")

    yield
    if scheduler:
        parar_scheduler()


app = FastAPI(title="Vitrine", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produto.router)
app.include_router(cache_status.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(bi.router)
app.include_router(configuracoes.router)
app.include_router(inventario.router)
app.include_router(whatsapp.router)
app.include_router(email_routes.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
