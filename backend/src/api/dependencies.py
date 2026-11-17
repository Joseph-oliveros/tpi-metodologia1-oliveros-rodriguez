"""Dependencias FastAPI tipadas para tenant y composición de servicios."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from src.domain.services import ServicioCatalogo, ServicioTurnos
from src.infrastructure.db import crear_repositorios, db_session
from src.persistence.repositories import (
    RepositorioPacientes,
    RepositorioProfesionales,
    RepositorioSillones,
)


@dataclass(frozen=True)
class ContextoTurnos:
    """Agrupa servicio de dominio y repositorios de catálogo por petición."""

    servicio: ServicioTurnos
    repo_profs: RepositorioProfesionales
    repo_sillones: RepositorioSillones
    repo_pacientes: RepositorioPacientes


def obtener_tenant_id(
    x_tenant_id: Annotated[
        str,
        Header(
            alias="X-Tenant-ID",
            description="Identificador de la clínica/consultorio (ej. demo-tenant)",
            examples=["demo-tenant"],
        ),
    ],
) -> str:
    """Resuelve y valida el tenant_id desde el header HTTP de la petición."""
    tenant_id = x_tenant_id.strip()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El header X-Tenant-ID no puede estar vacío",
        )
    return tenant_id


def obtener_db_path(request: Request) -> str:
    """Obtiene la ruta SQLite configurada en la instancia de FastAPI."""
    return str(request.app.state.database_path)


def obtener_contexto_turnos(
    request: Request,
    db_path: Annotated[str, Depends(obtener_db_path)],
) -> Generator[ContextoTurnos, None, None]:
    """Abre sesión SQLite por petición (o reutiliza conexión ':memory:') y ensambla repositorios."""
    memory_conn = getattr(request.app.state, "memory_conn", None)
    if memory_conn is not None:
        repo_turnos, repo_profs, repo_sillones, repo_pacientes = crear_repositorios(
            memory_conn
        )
        yield ContextoTurnos(
            servicio=ServicioTurnos(repositorio_turnos=repo_turnos),
            repo_profs=repo_profs,
            repo_sillones=repo_sillones,
            repo_pacientes=repo_pacientes,
        )
        return

    with db_session(db_path) as conn:
        repo_turnos, repo_profs, repo_sillones, repo_pacientes = crear_repositorios(
            conn
        )
        yield ContextoTurnos(
            servicio=ServicioTurnos(repositorio_turnos=repo_turnos),
            repo_profs=repo_profs,
            repo_sillones=repo_sillones,
            repo_pacientes=repo_pacientes,
        )


def obtener_servicio_catalogo(
    ctx: Annotated[ContextoTurnos, Depends(obtener_contexto_turnos)],
) -> ServicioCatalogo:
    """Ensambla el servicio de dominio de catálogo reutilizando la sesión de la petición."""
    return ServicioCatalogo(
        repo_profesionales=ctx.repo_profs,
        repo_sillones=ctx.repo_sillones,
        repo_pacientes=ctx.repo_pacientes,
    )


TenantIdDep = Annotated[str, Depends(obtener_tenant_id)]
ContextoTurnosDep = Annotated[ContextoTurnos, Depends(obtener_contexto_turnos)]
ServicioCatalogoDep = Annotated[ServicioCatalogo, Depends(obtener_servicio_catalogo)]
