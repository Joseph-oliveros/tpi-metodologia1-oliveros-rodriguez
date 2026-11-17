"""Router REST multi-tenant para gestión de sillones/boxes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from src.api.dependencies import ServicioCatalogoDep, TenantIdDep
from src.api.exception_handlers import RecursoNoEncontradoError
from src.api.schemas import ErrorResponse, SillonCreateRequest, SillonResponse

router = APIRouter(
    prefix="/api/v1/sillones",
    tags=["Sillones"],
    responses={
        422: {
            "description": "Error de validación en entrada o header X-Tenant-ID",
        }
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un sillón/box en el tenant",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Ya existe un sillón con ese nombre en el tenant",
        }
    },
)
def crear_sillon(
    payload: SillonCreateRequest,
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> SillonResponse:
    """Registra un sillón/box delegando las validaciones al dominio."""
    sillon = catalogo.crear_sillon(
        tenant_id=tenant_id,
        nombre=payload.nombre,
        equipamiento=payload.equipamiento,
        activo=payload.activo,
    )
    return SillonResponse.from_domain(sillon)


@router.get(
    "",
    summary="Listar sillones/boxes del tenant",
)
def listar_sillones(
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
    solo_activos: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo (true/false)"),
    ] = None,
) -> list[SillonResponse]:
    """Devuelve los sillones registrados del tenant solicitante."""
    sillones = catalogo.listar_sillones(
        tenant_id=tenant_id, solo_activos=solo_activos
    )
    return [SillonResponse.from_domain(s) for s in sillones]


@router.get(
    "/{sillon_id}",
    summary="Obtener un sillón/box por ID dentro del tenant",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Sillón inexistente en el tenant",
        }
    },
)
def obtener_sillon(
    sillon_id: Annotated[str, Path(min_length=1, examples=["sil-1"])],
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> SillonResponse:
    """Consulta un sillón específico perteneciente al tenant."""
    sillon = catalogo.obtener_sillon(tenant_id, sillon_id)
    if sillon is None:
        raise RecursoNoEncontradoError(
            "sillon",
            f"Sillón '{sillon_id}' no encontrado en el tenant",
        )
    return SillonResponse.from_domain(sillon)
