"""Router REST multi-tenant para gestión de profesionales."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from src.api.dependencies import ServicioCatalogoDep, TenantIdDep
from src.api.exception_handlers import RecursoNoEncontradoError
from src.api.schemas import (
    ErrorResponse,
    ProfesionalCreateRequest,
    ProfesionalResponse,
)

router = APIRouter(
    prefix="/api/v1/profesionales",
    tags=["Profesionales"],
    responses={
        422: {
            "description": "Error de validación en entrada o header X-Tenant-ID",
        }
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un profesional en el tenant",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Profesional duplicado por matrícula o nombre en el tenant",
        }
    },
)
def crear_profesional(
    payload: ProfesionalCreateRequest,
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> ProfesionalResponse:
    """Registra un profesional sintético delegando las validaciones al dominio."""
    profesional = catalogo.crear_profesional(
        tenant_id=tenant_id,
        nombre=payload.nombre,
        matricula=payload.matricula,
        especialidad=payload.especialidad,
        activo=payload.activo,
    )
    return ProfesionalResponse.from_domain(profesional)


@router.get(
    "",
    summary="Listar profesionales del tenant",
)
def listar_profesionales(
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
    solo_activos: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo (true/false)"),
    ] = None,
) -> list[ProfesionalResponse]:
    """Devuelve los profesionales registrados del tenant solicitante."""
    profesionales = catalogo.listar_profesionales(
        tenant_id=tenant_id, solo_activos=solo_activos
    )
    return [ProfesionalResponse.from_domain(p) for p in profesionales]


@router.get(
    "/{profesional_id}",
    summary="Obtener un profesional por ID dentro del tenant",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Profesional inexistente en el tenant",
        }
    },
)
def obtener_profesional(
    profesional_id: Annotated[str, Path(min_length=1, examples=["prof-1"])],
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> ProfesionalResponse:
    """Consulta un profesional específico perteneciente al tenant."""
    profesional = catalogo.obtener_profesional(tenant_id, profesional_id)
    if profesional is None:
        raise RecursoNoEncontradoError(
            "profesional",
            f"Profesional '{profesional_id}' no encontrado en el tenant",
        )
    return ProfesionalResponse.from_domain(profesional)
