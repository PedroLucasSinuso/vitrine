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
from app.api.routes import macro
from app.api.routes import notificacoes
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
from app.infrastructure.db.bootstrap import (
    init_db, acquire_scheduler_lock, release_scheduler_lock, heartbeat_scheduler_lock,
)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Re-apply logging config after uvicorn's own logging setup.
    # Without this, uvicorn's configure_logging() (called in the reload
    # subprocess via _subprocess.subprocess_started) can overwrite our
    # module-level dictConfig, causing console output to disappear.
    setup_logging()
    init_db()

    # Scheduler lock via SQLite: singleton row na tabela scheduler_lock.
    # Auto-expira se heartbeat parar por mais de 10 min.
    scheduler = None
    if acquire_scheduler_lock():
        scheduler = iniciar_scheduler()
        init_scheduler_manager(scheduler)

        # Heartbeat a cada 5 min — mantém lock ativo
        scheduler.add_job(
            heartbeat_scheduler_lock,
            "interval",
            minutes=5,
            id="scheduler_heartbeat",
            name="Scheduler lock heartbeat",
            replace_existing=True,
        )

        etl_min = ler_config_etl_interval()
        reagendar_etl(etl_min, run_sync_scheduled)

        iniciar_scheduler_notificacoes(scheduler)
    else:
        logger.warning("Scheduler lock não adquirido — jobs não serão agendados neste worker")

    yield
    if scheduler:
        parar_scheduler()
        release_scheduler_lock()


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
app.include_router(macro.router)
app.include_router(notificacoes.router)

if settings.intelligence_enabled:
    from app.api.routes import intelligence as intelligence_router
    app.include_router(intelligence_router.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
