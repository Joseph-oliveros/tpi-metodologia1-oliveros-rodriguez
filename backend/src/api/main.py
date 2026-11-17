"""Factoría de aplicación FastAPI (Composition Root)."""

from __future__ import annotations

from fastapi import FastAPI

from src.api.exception_handlers import register_exception_handlers
from src.api.routers.health import router as health_router
from src.api.routers.pacientes import router as pacientes_router
from src.api.routers.profesionales import router as profesionales_router
from src.api.routers.sillones import router as sillones_router
from src.api.routers.turnos import router as turnos_router
from src.infrastructure.config import get_settings
from src.infrastructure.db import init_database


def create_app(database_path: str | None = None) -> FastAPI:
    """Crea y configura la aplicación FastAPI desacoplada del dominio."""
    settings = get_settings()
    resolved_db = database_path if database_path is not None else settings.sqlite_path
    memory_conn = init_database(resolved_db)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "API REST multi-tenant para gestión de turnos odontológicos con doble "
            "validación simultánea de profesional y sillón bajo intervalos semiabiertos [inicio, fin)."
        ),
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.database_path = resolved_db
    app.state.memory_conn = memory_conn

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(profesionales_router)
    app.include_router(sillones_router)
    app.include_router(pacientes_router)
    app.include_router(turnos_router)
    return app


app = create_app()
