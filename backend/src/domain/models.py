"""Modelos de dominio para la gestión de turnos odontológicos."""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class Profesional:
    """Profesional de la salud que atiende turnos."""

    nombre: str


@dataclass(frozen=True)
class Sillon:
    """Sillón/box odontológico en el que se realiza la atención."""

    nombre: str


@dataclass(frozen=True)
class Turno:
    """Turno odontológico confirmado en un intervalo semiabierto [hora_inicio, hora_fin)."""

    profesional: Profesional
    sillon: Sillon
    fecha: str
    hora_inicio: str
    hora_fin: str
    paciente: str
    estado: str = "CONFIRMADO"
