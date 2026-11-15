"""Pruebas de los 3 escenarios Gherkin: creación de turnos sin solapamientos.

Todos los datos son sintéticos (regla de privacidad de AGENTS.md).
"""

import pytest

from src.domain.exceptions import (
    SolapamientoProfesionalError,
    SolapamientoSillonError,
    TransicionInvalidaError,
)
from src.domain.models import (
    ESTADO_CANCELADO,
    ESTADO_COMPLETADO,
    ESTADO_CONFIRMADO,
    ESTADO_PENDIENTE,
    ESTADOS_ACTIVOS,
    ESTADOS_FINALES,
    TRANSICIONES_PERMITIDAS,
    Profesional,
    Sillon,
    Turno,
)
from src.domain.services import ServicioTurnos


# ---------------------------------------------------------------------------
# Task 1: modelos de dominio
# ---------------------------------------------------------------------------


def test_modelos_dominio_disponibles() -> None:
    """Task 1: los modelos de dominio existen y se pueden instanciar."""
    profesional = Profesional(nombre="Dr. Pérez")
    sillon = Sillon(nombre="Sillón 1")
    turno = Turno(
        profesional=profesional,
        sillon=sillon,
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente A",
    )
    assert turno.profesional.nombre == "Dr. Pérez"
    assert turno.sillon.nombre == "Sillón 1"
    assert turno.estado == "CONFIRMADO"


def test_constantes_y_matriz_de_estados() -> None:
    """Task 1.2: constantes de estado, grupos de activos/finales y matriz de transiciones."""
    assert ESTADO_PENDIENTE == "PENDIENTE"
    assert ESTADO_CONFIRMADO == "CONFIRMADO"
    assert ESTADO_CANCELADO == "CANCELADO"
    assert ESTADO_COMPLETADO == "COMPLETADO"

    assert ESTADOS_ACTIVOS == {"PENDIENTE", "CONFIRMADO"}
    assert ESTADOS_FINALES == {"CANCELADO", "COMPLETADO"}

    assert TRANSICIONES_PERMITIDAS[ESTADO_PENDIENTE] == {"CONFIRMADO", "CANCELADO"}
    assert TRANSICIONES_PERMITIDAS[ESTADO_CONFIRMADO] == {"COMPLETADO", "CANCELADO"}
    assert TRANSICIONES_PERMITIDAS[ESTADO_CANCELADO] == set()
    assert TRANSICIONES_PERMITIDAS[ESTADO_COMPLETADO] == set()


# ---------------------------------------------------------------------------
# Task 2: excepciones de dominio
# ---------------------------------------------------------------------------


def test_excepciones_de_dominio_son_excepciones() -> None:
    """Task 2: las excepciones de solapamiento son excepciones de dominio explícitas."""
    assert issubclass(SolapamientoProfesionalError, Exception)
    assert issubclass(SolapamientoSillonError, Exception)
    assert issubclass(SolapamientoProfesionalError, SolapamientoSillonError) is False


def test_transicion_invalida_error_es_excepcion_de_dominio() -> None:
    """Task 1.1: TransicionInvalidaError hereda de Exception y tiene mensaje explícito."""
    assert issubclass(TransicionInvalidaError, Exception)
    err = TransicionInvalidaError("Transición no permitida")
    assert str(err) == "Transición no permitida"


# ---------------------------------------------------------------------------
# Escenario 1 (Gherkin): Creación exitosa de turno sin conflicto (Camino Feliz)
# ---------------------------------------------------------------------------


def test_escenario_1_creacion_exitosa_sin_conflicto() -> None:
    """El turno se registra con éxito y queda con estado CONFIRMADO."""
    servicio = ServicioTurnos()
    turno = servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    assert turno.estado == "CONFIRMADO"
    assert turno.paciente == "Paciente A"
    assert servicio.turnos_registrados() == [turno]


# ---------------------------------------------------------------------------
# Escenario 2 (Gherkin): Rechazo por conflicto de agenda (Error de Negocio)
# ---------------------------------------------------------------------------


def test_escenario_2_rechazo_por_conflicto_de_profesional() -> None:
    """Un solapamiento del profesional lanza SolapamientoProfesionalError aunque cambie el sillón."""
    servicio = ServicioTurnos()
    servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    with pytest.raises(SolapamientoProfesionalError):
        servicio.agendar_turno(
            paciente="Paciente B",
            fecha="2026-11-01",
            hora_inicio="10:15",
            hora_fin="10:45",
            profesional=Profesional(nombre="Dr. Pérez"),
            sillon=Sillon(nombre="Sillón 2"),
        )


# ---------------------------------------------------------------------------
# Escenario 3 (Gherkin): Turnos contiguos en el límite exacto (Caso de Borde)
# ---------------------------------------------------------------------------


def test_escenario_3_turnos_contiguos_no_son_solapamiento() -> None:
    """a_fin == b_inicio NO es solapamiento: la reserva se permite."""
    servicio = ServicioTurnos()
    servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    turno_2 = servicio.agendar_turno(
        paciente="Paciente B",
        fecha="2026-11-01",
        hora_inicio="10:30",
        hora_fin="11:00",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    assert turno_2.estado == "CONFIRMADO"
    assert len(servicio.turnos_registrados()) == 2


# ---------------------------------------------------------------------------
# Triangulación: doble validación de recurso (AGENTS.md regla 2)
# ---------------------------------------------------------------------------


def test_triangulacion_conflicto_de_sillon_lanza_solapamiento_sillon() -> None:
    """El sillón ocupado por OTRO profesional lanza SolapamientoSillonError."""
    servicio = ServicioTurnos()
    servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    with pytest.raises(SolapamientoSillonError):
        servicio.agendar_turno(
            paciente="Paciente B",
            fecha="2026-11-01",
            hora_inicio="10:15",
            hora_fin="10:45",
            profesional=Profesional(nombre="Dr. Ejemplo"),
            sillon=Sillon(nombre="Sillón 1"),
        )


def test_triangulacion_solape_invertido_es_conflicto() -> None:
    """Un turno nuevo que termina DESPUÉS de iniciar el existente: solapa."""
    servicio = ServicioTurnos()
    servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:15",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    with pytest.raises(SolapamientoProfesionalError):
        servicio.agendar_turno(
            paciente="Paciente B",
            fecha="2026-11-01",
            hora_inicio="10:00",
            hora_fin="10:20",
            profesional=Profesional(nombre="Dr. Pérez"),
            sillon=Sillon(nombre="Sillón 2"),
        )


def test_triangulacion_fechas_diferentes_no_conflictan() -> None:
    """El mismo horario en otra fecha no genera solapamiento."""
    servicio = ServicioTurnos()
    servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    turno_2 = servicio.agendar_turno(
        paciente="Paciente B",
        fecha="2026-11-02",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    assert turno_2.estado == "CONFIRMADO"


# ---------------------------------------------------------------------------
# C-01: Ciclo de vida y transiciones de estado
# ---------------------------------------------------------------------------


def test_confirmar_turno_pendiente_exitoso() -> None:
    """Task 2.1: confirmar un turno en estado PENDIENTE pasa a CONFIRMADO."""
    servicio = ServicioTurnos()
    turno_pendiente = Turno(
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente Ficticio",
        estado=ESTADO_PENDIENTE,
    )
    servicio._turnos.append(turno_pendiente)

    turno_confirmado = servicio.confirmar(turno_pendiente)

    assert turno_confirmado.estado == ESTADO_CONFIRMADO
    assert turno_confirmado in servicio.turnos_registrados()
    assert turno_pendiente not in servicio.turnos_registrados()


def test_confirmar_turno_desde_estado_invalido_lanza_error() -> None:
    """Task 2.1: confirmar un turno ya CONFIRMADO o CANCELADO lanza TransicionInvalidaError."""
    servicio = ServicioTurnos()
    turno_confirmado = servicio.agendar_turno(
        paciente="Paciente Ficticio",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    with pytest.raises(TransicionInvalidaError):
        servicio.confirmar(turno_confirmado)


def test_cancelar_turno_confirmado_exitoso() -> None:
    """Task 2.2: cancelar un turno en CONFIRMADO pasa a CANCELADO."""
    servicio = ServicioTurnos()
    turno = servicio.agendar_turno(
        paciente="Paciente Ficticio",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    assert turno.estado == ESTADO_CONFIRMADO

    turno_cancelado = servicio.cancelar(turno)

    assert turno_cancelado.estado == ESTADO_CANCELADO
    assert turno_cancelado in servicio.turnos_registrados()


def test_cancelar_turno_pendiente_exitoso() -> None:
    """Task 2.2: cancelar un turno en PENDIENTE pasa a CANCELADO."""
    servicio = ServicioTurnos()
    turno_pendiente = Turno(
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente Ficticio",
        estado=ESTADO_PENDIENTE,
    )
    servicio._turnos.append(turno_pendiente)

    turno_cancelado = servicio.cancelar(turno_pendiente)

    assert turno_cancelado.estado == ESTADO_CANCELADO


def test_cancelar_turno_ya_cancelado_lanza_error() -> None:
    """Task 2.2: cancelar un turno que ya está CANCELADO lanza TransicionInvalidaError."""
    servicio = ServicioTurnos()
    turno = servicio.agendar_turno(
        paciente="Paciente Ficticio",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    turno_cancelado = servicio.cancelar(turno)
    with pytest.raises(TransicionInvalidaError):
        servicio.cancelar(turno_cancelado)


def test_completar_turno_confirmado_exitoso() -> None:
    """Task 2.3: completar un turno en CONFIRMADO pasa a COMPLETADO."""
    servicio = ServicioTurnos()
    turno = servicio.agendar_turno(
        paciente="Paciente Ficticio",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    turno_completado = servicio.completar(turno)

    assert turno_completado.estado == ESTADO_COMPLETADO
    assert turno_completado in servicio.turnos_registrados()


def test_completar_turno_desde_estado_invalido_lanza_error() -> None:
    """Task 2.3: completar un turno en PENDIENTE o ya COMPLETADO lanza TransicionInvalidaError."""
    servicio = ServicioTurnos()
    turno_pendiente = Turno(
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente Ficticio",
        estado=ESTADO_PENDIENTE,
    )
    servicio._turnos.append(turno_pendiente)

    with pytest.raises(TransicionInvalidaError):
        servicio.completar(turno_pendiente)


# ---------------------------------------------------------------------------
# C-01: Liberación de recursos por cancelación y cierre de atención (RN-04)
# ---------------------------------------------------------------------------


def test_cancelacion_libera_recursos_para_reagendar_mismo_intervalo() -> None:
    """Task 3.1: un turno CANCELADO libera profesional y sillón permitiendo reagendar."""
    servicio = ServicioTurnos()
    turno_1 = servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    # Cancelar el turno
    servicio.cancelar(turno_1)

    # Reagendar en el mismo horario con el mismo profesional y sillón debe ser exitoso
    turno_2 = servicio.agendar_turno(
        paciente="Paciente B",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )

    assert turno_2.estado == ESTADO_CONFIRMADO
    assert turno_2.paciente == "Paciente B"
    assert len(servicio.turnos_registrados()) == 2


def test_turno_completado_no_bloquea_recursos() -> None:
    """Task 3.1: un turno COMPLETADO no bloquea recursos en la validación de solapamiento."""
    servicio = ServicioTurnos()
    turno_1 = servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    servicio.completar(turno_1)

    turno_2 = servicio.agendar_turno(
        paciente="Paciente B",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
    )
    assert turno_2.estado == ESTADO_CONFIRMADO


def test_transicionar_turno_no_registrado_lanza_value_error() -> None:
    """Intentar transicionar un turno que no pertenece a la colección lanza ValueError."""
    servicio = ServicioTurnos()
    turno_no_registrado = Turno(
        profesional=Profesional(nombre="Dr. Pérez"),
        sillon=Sillon(nombre="Sillón 1"),
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente Ficticio",
    )
    with pytest.raises(ValueError, match="no se encuentra registrado"):
        servicio.confirmar(turno_no_registrado)
