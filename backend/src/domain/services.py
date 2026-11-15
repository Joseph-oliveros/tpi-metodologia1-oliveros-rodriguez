"""Servicio de dominio para el agendamiento de turnos odontológicos."""

from dataclasses import replace

from src.domain.exceptions import (
    SolapamientoProfesionalError,
    SolapamientoSillonError,
    TransicionInvalidaError,
)
from src.domain.models import (
    ESTADO_CANCELADO,
    ESTADO_COMPLETADO,
    ESTADO_CONFIRMADO,
    ESTADOS_ACTIVOS,
    TRANSICIONES_PERMITIDAS,
    Profesional,
    Sillon,
    Turno,
)


def _horas_a_minutos(hora: str) -> int:
    """Convierte una hora 'HH:MM' a minutos desde medianoche."""
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def _hay_solapamiento(
    inicio_a: int, fin_a: int, inicio_b: int, fin_b: int
) -> bool:
    """Intervalos semiabiertos [inicio, fin): solapan iff a_inicio < b_fin and a_fin > b_inicio.

    Si fin_a == inicio_b (contiguo) NO hay solapamiento.
    """
    return inicio_a < fin_b and fin_a > inicio_b


class ServicioTurnos:
    """Registra turnos validando solapamientos por profesional y por sillón de forma independiente."""

    def __init__(self) -> None:
        self._turnos: list[Turno] = []

    def agendar_turno(
        self,
        paciente: str,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        profesional: Profesional,
        sillon: Sillon,
    ) -> Turno:
        """Crea y registra un turno si no hay solapamiento de profesional ni de sillón."""
        inicio = _horas_a_minutos(hora_inicio)
        fin = _horas_a_minutos(hora_fin)

        for turno_existente in self._turnos:
            if turno_existente.estado not in ESTADOS_ACTIVOS:
                continue
            if turno_existente.fecha != fecha:
                continue
            existente_inicio = _horas_a_minutos(turno_existente.hora_inicio)
            existente_fin = _horas_a_minutos(turno_existente.hora_fin)
            if not _hay_solapamiento(inicio, fin, existente_inicio, existente_fin):
                continue
            # Doble validación de recurso: profesional y sillón, de forma independiente.
            if turno_existente.profesional == profesional:
                raise SolapamientoProfesionalError(
                    f"El profesional {profesional.nombre} ya tiene un turno "
                    f"el {fecha} de {turno_existente.hora_inicio} a {turno_existente.hora_fin}"
                )
            if turno_existente.sillon == sillon:
                raise SolapamientoSillonError(
                    f"El sillón {sillon.nombre} ya está ocupado "
                    f"el {fecha} de {turno_existente.hora_inicio} a {turno_existente.hora_fin}"
                )

        turno = Turno(
            profesional=profesional,
            sillon=sillon,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            paciente=paciente,
        )
        self._turnos.append(turno)
        return turno

    def turnos_registrados(self) -> list[Turno]:
        """Devuelve una copia de la lista de turnos registrados."""
        return list(self._turnos)

    def _transicionar(self, turno: Turno, nuevo_estado: str) -> Turno:
        """Aplica una transición de estado validando la matriz de transiciones permitidas."""
        if turno not in self._turnos:
            raise ValueError("El turno especificado no se encuentra registrado")
        destinos_validos = TRANSICIONES_PERMITIDAS.get(turno.estado, set())
        if nuevo_estado not in destinos_validos:
            raise TransicionInvalidaError(
                f"Transición no permitida: no se puede pasar de '{turno.estado}' a '{nuevo_estado}'"
            )
        turno_actualizado = replace(turno, estado=nuevo_estado)
        indice = self._turnos.index(turno)
        self._turnos[indice] = turno_actualizado
        return turno_actualizado

    def confirmar(self, turno: Turno) -> Turno:
        """Confirma un turno en estado PENDIENTE."""
        return self._transicionar(turno, ESTADO_CONFIRMADO)

    def cancelar(self, turno: Turno) -> Turno:
        """Cancela un turno en estado PENDIENTE o CONFIRMADO."""
        return self._transicionar(turno, ESTADO_CANCELADO)

    def completar(self, turno: Turno) -> Turno:
        """Marca como completado un turno en estado CONFIRMADO."""
        return self._transicionar(turno, ESTADO_COMPLETADO)
