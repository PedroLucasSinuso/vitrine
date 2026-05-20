from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
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

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = iniciar_scheduler()
    init_scheduler_manager(scheduler)

    etl_min = ler_config_etl_interval()
    reagendar_etl(etl_min, run_sync_scheduled)

    iniciar_scheduler_notificacoes(scheduler)
    yield
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
