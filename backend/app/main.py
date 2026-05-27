from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .core.config import settings
from .core.database import lifespan
from .api.v1.router import api_router
from .exceptions.handlers import register_exception_handlers
from .middleware.audit import AuditMiddleware

# Configure Loguru
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API do sistema educacional gamificado LabQuiz ETEC — "
        "Jogo de Identificação de Materiais e Sistemas de Laboratório para o 1º ano do Ensino Médio Técnico em Química."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging middleware
app.add_middleware(AuditMiddleware)

# Exception handlers
register_exception_handlers(app)

# Routes
app.include_router(api_router)


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.ENV,
    }
