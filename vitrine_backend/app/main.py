from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import produto, cache_status
from app.api.routes import auth
from app.api.routes import admin
from app.api.routes import bi
from app.api.routes import configuracoes
from app.api.routes import inventario
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.application.etl.scheduler import iniciar_scheduler, parar_scheduler

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    intervalo = max(1, settings.cache_refresh_interval // 3600)
    iniciar_scheduler(intervalo_horas=intervalo)
    yield
    parar_scheduler()


app = FastAPI(title="Vitrine", lifespan=lifespan)

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

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")