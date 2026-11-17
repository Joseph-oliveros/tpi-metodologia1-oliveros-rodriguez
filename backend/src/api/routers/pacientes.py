"""Router REST multi-tenant para gestión de pacientes sintéticos."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from src.api.dependencies import ServicioCatalogoDep, TenantIdDep
from src.api.exception_handlers import RecursoNoEncontradoError
from src.api.schemas import ErrorResponse, PacienteCreateRequest, PacienteResponse

router = APIRouter(
    prefix="/api/v1/pacientes",
    tags=["Pacientes"],
    responses={
        422: {
            "description": "Error de validación en entrada o header X-Tenant-ID",
        }
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un paciente en el tenant",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Ya existe un paciente con ese DNI en el tenant",
        }
    },
)
def crear_paciente(
    payload: PacienteCreateRequest,
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> PacienteResponse:
    """Registra un paciente sintético delegando la unicidad al dominio."""
    paciente = catalogo.crear_paciente(
        tenant_id=tenant_id,
        nombre=payload.nombre,
        dni=payload.dni,
        telefono=payload.telefono,
    )
    return PacienteResponse.from_domain(paciente)


@router.get(
    "",
    summary="Listar pacientes del tenant con filtros opcionales",
)
def listar_pacientes(
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
    dni: Annotated[
        str | None,
        Query(description="Filtrar por DNI exacto"),
    ] = None,
    nombre: Annotated[
        str | None,
        Query(description="Filtrar por coincidencia parcial de nombre"),
    ] = None,
) -> list[PacienteResponse]:
    """Devuelve los pacientes del tenant filtrados por DNI y/o nombre."""
    pacientes = catalogo.listar_pacientes(
        tenant_id=tenant_id, dni=dni, nombre=nombre
    )
    return [PacienteResponse.from_domain(p) for p in pacientes]


@router.get(
    "/{paciente_id}",
    summary="Obtener un paciente por ID dentro del tenant",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Paciente inexistente en el tenant",
        }
    },
)
def obtener_paciente(
    paciente_id: Annotated[str, Path(min_length=1, examples=["pac-1"])],
    tenant_id: TenantIdDep,
    catalogo: ServicioCatalogoDep,
) -> PacienteResponse:
    """Consulta un paciente específico perteneciente al tenant."""
    paciente = catalogo.obtener_paciente(tenant_id, paciente_id)
    if paciente is None:
        raise RecursoNoEncontradoError(
            "paciente",
            f"Paciente '{paciente_id}' no encontrado en el tenant",
        )
    return PacienteResponse.from_domain(paciente)
