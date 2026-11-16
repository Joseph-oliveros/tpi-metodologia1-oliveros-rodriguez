"""Puertos de salida del dominio y adaptador en memoria para pruebas unitarias puras."""

from __future__ import annotations

from typing import Protocol

from src.domain.models import ESTADOS_ACTIVOS, Turno


class RepositorioTurnosPort(Protocol):
    """Puerto de persistencia de turnos consumido por ServicioTurnos."""

    def guardar(self, turno: Turno) -> Turno: ...

    def actualizar(self, turno: Turno) -> Turno: ...

    def obtener_por_id(self, tenant_id: str, turno_id: str) -> Turno | None: ...

    def buscar_activos_por_fecha(self, tenant_id: str, fecha: str) -> list[Turno]: ...

    def listar_por_tenant(
        self,
        tenant_id: str,
        fecha: str | None = None,
        profesional_id: str | None = None,
        sillon_id: str | None = None,
    ) -> list[Turno]: ...


class RepositorioTurnosEnMemoria:
    """Adaptador en memoria puro para ejecutar reglas de dominio sin infraestructura."""

    def __init__(self) -> None:
        self._datos: dict[tuple[str, str], Turno] = {}

    def guardar(self, turno: Turno) -> Turno:
        self._datos[(turno.tenant_id, turno.id)] = turno
        return turno

    def actualizar(self, turno: Turno) -> Turno:
        self._datos[(turno.tenant_id, turno.id)] = turno
        return turno

    def obtener_por_id(self, tenant_id: str, turno_id: str) -> Turno | None:
        return self._datos.get((tenant_id, turno_id))

    def buscar_activos_por_fecha(self, tenant_id: str, fecha: str) -> list[Turno]:
        return [
            t
            for t in self._datos.values()
            if t.tenant_id == tenant_id
            and t.fecha == fecha
            and t.estado in ESTADOS_ACTIVOS
        ]

    def listar_por_tenant(
        self,
        tenant_id: str,
        fecha: str | None = None,
        profesional_id: str | None = None,
        sillon_id: str | None = None,
    ) -> list[Turno]:
        resultado = [t for t in self._datos.values() if t.tenant_id == tenant_id]
        if fecha is not None:
            resultado = [t for t in resultado if t.fecha == fecha]
        if profesional_id is not None:
            resultado = [t for t in resultado if t.profesional.id == profesional_id]
        if sillon_id is not None:
            resultado = [t for t in resultado if t.sillon.id == sillon_id]
        return resultado
