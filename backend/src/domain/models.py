"""Modelos de dominio para la gestión de turnos odontológicos."""

import uuid
from dataclasses import dataclass, field

# Constantes canónicas de estados del turno (RN-03)
ESTADO_PENDIENTE = "PENDIENTE"
ESTADO_CONFIRMADO = "CONFIRMADO"
ESTADO_CANCELADO = "CANCELADO"
ESTADO_COMPLETADO = "COMPLETADO"

# Conjuntos de clasificación de estados
ESTADOS_ACTIVOS = {ESTADO_PENDIENTE, ESTADO_CONFIRMADO}
ESTADOS_FINALES = {ESTADO_CANCELADO, ESTADO_COMPLETADO}

# Matriz de transiciones permitidas según el ciclo de vida (RN-03)
TRANSICIONES_PERMITIDAS: dict[str, set[str]] = {
    ESTADO_PENDIENTE: {ESTADO_CONFIRMADO, ESTADO_CANCELADO},
    ESTADO_CONFIRMADO: {ESTADO_COMPLETADO, ESTADO_CANCELADO},
    ESTADO_CANCELADO: set(),
    ESTADO_COMPLETADO: set(),
}


def _generar_id() -> str:
    """Genera un identificador único sintético."""
    return uuid.uuid4().hex[:12]


@dataclass(frozen=True)
class Tenant:
    """Clínica o consultorio aislado dentro del SaaS (D-01, RN-05)."""

    nombre: str
    id: str = field(default_factory=_generar_id, compare=False)


@dataclass(frozen=True)
class Paciente:
    """Paciente que recibe la atención odontológica."""

    nombre: str
    dni: str = ""
    id: str = field(default_factory=_generar_id, compare=False)
    tenant_id: str = "tenant-default"
    telefono: str = ""


@dataclass(frozen=True)
class Profesional:
    """Profesional de la salud que atiende turnos."""

    nombre: str
    id: str = field(default_factory=_generar_id, compare=False)
    tenant_id: str = "tenant-default"
    activo: bool = True
    matricula: str = ""
    especialidad: str = ""


@dataclass(frozen=True)
class Sillon:
    """Sillón/box odontológico en el que se realiza la atención."""

    nombre: str
    id: str = field(default_factory=_generar_id, compare=False)
    tenant_id: str = "tenant-default"
    activo: bool = True
    equipamiento: str = ""


@dataclass(frozen=True)
class Turno:
    """Turno odontológico en un intervalo semiabierto [hora_inicio, hora_fin)."""

    profesional: Profesional
    sillon: Sillon
    fecha: str
    hora_inicio: str
    hora_fin: str
    paciente: str
    estado: str = "CONFIRMADO"
    id: str = field(default_factory=_generar_id, compare=False)
    tenant_id: str = "tenant-default"
    paciente_id: str = field(default="", compare=False)
