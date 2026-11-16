"""Esquemas Pydantic v2 para validación de entrada y serialización de salida."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.models import Turno

AccionEstadoTurno = Literal["confirmar", "cancelar", "completar"]


class HealthResponse(BaseModel):
    """Respuesta del endpoint de estado de salud."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["turnos-odontologia-api"])


class ErrorResponse(BaseModel):
    """Contrato uniforme para errores de dominio y recursos inexistentes."""

    detail: str = Field(
        examples=["El profesional Dr. Ejemplo ya tiene un turno en ese horario"]
    )
    codigo: str = Field(examples=["SOLAPAMIENTO_PROFESIONAL"])
    recurso: str | None = Field(default=None, examples=["profesional"])


class TurnoCreateRequest(BaseModel):
    """Solicitud HTTP para registrar un turno odontológico."""

    paciente_id: str = Field(min_length=1, examples=["pac-1"])
    profesional_id: str = Field(min_length=1, examples=["prof-1"])
    sillon_id: str = Field(min_length=1, examples=["sil-1"])
    fecha: datetime.date = Field(examples=["2026-11-20"])
    hora_inicio: str = Field(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        examples=["11:00"],
    )
    hora_fin: str = Field(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        examples=["11:30"],
    )

    @field_validator("paciente_id", "profesional_id", "sillon_id")
    @classmethod
    def validar_identificador_no_vacio(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El identificador no puede estar vacío")
        return limpio

    @model_validator(mode="after")
    def validar_intervalo_positivo(self) -> TurnoCreateRequest:
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self


class TurnoEstadoRequest(BaseModel):
    """Solicitud HTTP para ejecutar una transición sobre un turno."""

    accion: AccionEstadoTurno = Field(examples=["cancelar"])


class TurnoResponse(BaseModel):
    """Representación HTTP pública de un turno odontológico."""

    id: str = Field(examples=["turno-1"])
    tenant_id: str = Field(examples=["demo-tenant"])
    paciente_id: str = Field(examples=["pac-1"])
    paciente_nombre: str = Field(examples=["Paciente Ficticio"])
    profesional_id: str = Field(examples=["prof-1"])
    profesional_nombre: str = Field(examples=["Dr. Ejemplo"])
    sillon_id: str = Field(examples=["sil-1"])
    sillon_nombre: str = Field(examples=["Sillón 1"])
    fecha: str = Field(examples=["2026-11-20"])
    hora_inicio: str = Field(examples=["11:00"])
    hora_fin: str = Field(examples=["11:30"])
    estado: str = Field(examples=["CONFIRMADO"])

    @classmethod
    def from_domain(cls, turno: Turno) -> TurnoResponse:
        """Mapea una entidad de dominio Turno al DTO de salida."""
        return cls(
            id=turno.id,
            tenant_id=turno.tenant_id,
            paciente_id=turno.paciente_id,
            paciente_nombre=turno.paciente,
            profesional_id=turno.profesional.id,
            profesional_nombre=turno.profesional.nombre,
            sillon_id=turno.sillon.id,
            sillon_nombre=turno.sillon.nombre,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            hora_fin=turno.hora_fin,
            estado=turno.estado,
        )
