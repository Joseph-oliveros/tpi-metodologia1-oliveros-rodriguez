"""Router REST para la gestión de turnos odontológicos."""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from src.api.dependencies import ContextoTurnosDep, TenantIdDep
from src.api.exception_handlers import RecursoNoEncontradoError
from src.api.schemas import (
    ErrorResponse,
    TurnoCreateRequest,
    TurnoEstadoRequest,
    TurnoResponse,
)

router = APIRouter(
    prefix="/api/v1/turnos",
    tags=["Turnos"],
    responses={
        422: {
            "description": "Error de validación en entrada o header X-Tenant-ID",
        }
    },
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un turno odontológico",
    responses={
        404: {"model": ErrorResponse, "description": "Recurso inexistente en el tenant"},
        409: {
            "model": ErrorResponse,
            "description": "Conflicto de horario en profesional o sillón",
        },
    },
)
def crear_turno(
    payload: TurnoCreateRequest,
    tenant_id: TenantIdDep,
    ctx: ContextoTurnosDep,
) -> TurnoResponse:
    """Registra un turno delegando la doble validación al servicio de dominio."""
    paciente = ctx.repo_pacientes.obtener_por_id(tenant_id, payload.paciente_id)
    if paciente is None:
        raise RecursoNoEncontradoError(
            "paciente",
            f"Paciente '{payload.paciente_id}' no encontrado en el tenant",
        )

    profesional = ctx.repo_profs.obtener_por_id(tenant_id, payload.profesional_id)
    if profesional is None:
        raise RecursoNoEncontradoError(
            "profesional",
            f"Profesional '{payload.profesional_id}' no encontrado en el tenant",
        )

    sillon = ctx.repo_sillones.obtener_por_id(tenant_id, payload.sillon_id)
    if sillon is None:
        raise RecursoNoEncontradoError(
            "sillon",
            f"Sillón '{payload.sillon_id}' no encontrado en el tenant",
        )

    turno = ctx.servicio.agendar_turno(
        paciente=paciente.nombre,
        fecha=payload.fecha.isoformat(),
        hora_inicio=payload.hora_inicio,
        hora_fin=payload.hora_fin,
        profesional=profesional,
        sillon=sillon,
        tenant_id=tenant_id,
        paciente_id=paciente.id,
    )
    return TurnoResponse.from_domain(turno)


@router.get(
    "",
    summary="Listar turnos del tenant con filtros opcionales",
)
def listar_turnos(
    tenant_id: TenantIdDep,
    ctx: ContextoTurnosDep,
    fecha: Annotated[
        datetime.date | None,
        Query(description="Filtrar por fecha YYYY-MM-DD"),
    ] = None,
    profesional_id: Annotated[
        str | None,
        Query(description="Filtrar por ID de profesional"),
    ] = None,
    sillon_id: Annotated[
        str | None,
        Query(description="Filtrar por ID de sillón"),
    ] = None,
) -> list[TurnoResponse]:
    """Devuelve los turnos del tenant filtrados por fecha, profesional y/o sillón."""
    turnos = ctx.servicio.listar_turnos(
        tenant_id=tenant_id,
        fecha=fecha.isoformat() if fecha is not None else None,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
    )
    return [TurnoResponse.from_domain(t) for t in turnos]


@router.patch(
    "/{turno_id}/estado",
    summary="Cambiar estado de un turno (confirmar, cancelar o completar)",
    responses={
        404: {"model": ErrorResponse, "description": "Turno inexistente en el tenant"},
        409: {
            "model": ErrorResponse,
            "description": "Transición de estado no permitida",
        },
    },
)
def cambiar_estado_turno(
    turno_id: Annotated[str, Path(min_length=1, examples=["turno-1"])],
    payload: TurnoEstadoRequest,
    tenant_id: TenantIdDep,
    ctx: ContextoTurnosDep,
) -> TurnoResponse:
    """Ejecuta una transición válida sobre el ciclo de vida del turno."""
    turno = ctx.servicio.obtener_turno(tenant_id, turno_id)
    if turno is None:
        raise RecursoNoEncontradoError(
            "turno",
            f"Turno '{turno_id}' no encontrado en el tenant",
        )

    acciones = {
        "confirmar": ctx.servicio.confirmar,
        "cancelar": ctx.servicio.cancelar,
        "completar": ctx.servicio.completar,
    }
    turno_actualizado = acciones[payload.accion](turno)
    return TurnoResponse.from_domain(turno_actualizado)
