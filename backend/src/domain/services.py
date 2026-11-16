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
    TRANSICIONES_PERMITIDAS,
    Profesional,
    Sillon,
    Turno,
)
from src.persistence.database import get_connection, init_db
from src.persistence.repositories import RepositorioTurnos


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
    """Registra turnos validando solapamientos con persistencia SQLite y soporte multi-tenant (D-01, RN-05)."""

    def __init__(self, repositorio_turnos: RepositorioTurnos | None = None) -> None:
        self._owned_conn = None
        if repositorio_turnos is None:
            conn = get_connection(":memory:")
            init_db(conn)
            self._owned_conn = conn
            self._repo = RepositorioTurnos(conn)
        else:
            self._repo = repositorio_turnos

    def cerrar(self) -> None:
        """Cierra la conexión a la base de datos si fue creada internamente."""
        if self._owned_conn is not None:
            self._owned_conn.close()
            self._owned_conn = None

    def __del__(self) -> None:
        self.cerrar()

    @property
    def _turnos(self):
        """Adaptador de compatibilidad hacia atrás que redirige a persistencia SQLite."""
        class _TurnosAdapter:
            def __init__(self, repo: RepositorioTurnos, tenant_id: str = "tenant-default"):
                self._repo = repo
                self._tenant_id = tenant_id

            def append(self, turno: Turno) -> None:
                self._repo.guardar(turno)

            def __iter__(self):
                return iter(self._repo.listar_por_tenant(self._tenant_id))

            def __len__(self):
                return len(self._repo.listar_por_tenant(self._tenant_id))

        return _TurnosAdapter(self._repo)

    def agendar_turno(
        self,
        paciente: str,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        profesional: Profesional,
        sillon: Sillon,
        tenant_id: str = "tenant-default",
    ) -> Turno:
        """Crea y registra un turno si no hay solapamiento de profesional ni de sillón en el tenant."""
        inicio = _horas_a_minutos(hora_inicio)
        fin = _horas_a_minutos(hora_fin)

        turnos_activos = self._repo.buscar_activos_por_fecha(tenant_id, fecha)
        for turno_existente in turnos_activos:
            existente_inicio = _horas_a_minutos(turno_existente.hora_inicio)
            existente_fin = _horas_a_minutos(turno_existente.hora_fin)
            if not _hay_solapamiento(inicio, fin, existente_inicio, existente_fin):
                continue
            # Doble validación de recurso: profesional y sillón, de forma independiente.
            if turno_existente.profesional.nombre == profesional.nombre:
                raise SolapamientoProfesionalError(
                    f"El profesional {profesional.nombre} ya tiene un turno "
                    f"el {fecha} de {turno_existente.hora_inicio} a {turno_existente.hora_fin}"
                )
            if turno_existente.sillon.nombre == sillon.nombre:
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
            tenant_id=tenant_id,
        )
        return self._repo.guardar(turno)

    def turnos_registrados(self, tenant_id: str = "tenant-default") -> list[Turno]:
        """Devuelve los turnos registrados del tenant especificado."""
        return self._repo.listar_por_tenant(tenant_id)

    def _transicionar(self, turno: Turno, nuevo_estado: str) -> Turno:
        """Aplica una transición de estado validando la matriz de transiciones permitidas."""
        turno_existente = self._repo.obtener_por_id(turno.tenant_id, turno.id)
        if not turno_existente:
            raise ValueError("El turno especificado no se encuentra registrado")
        destinos_validos = TRANSICIONES_PERMITIDAS.get(turno_existente.estado, set())
        if nuevo_estado not in destinos_validos:
            raise TransicionInvalidaError(
                f"Transición no permitida: no se puede pasar de '{turno_existente.estado}' a '{nuevo_estado}'"
            )
        turno_actualizado = replace(turno_existente, estado=nuevo_estado)
        return self._repo.actualizar(turno_actualizado)

    def confirmar(self, turno: Turno) -> Turno:
        """Confirma un turno en estado PENDIENTE."""
        return self._transicionar(turno, ESTADO_CONFIRMADO)

    def cancelar(self, turno: Turno) -> Turno:
        """Cancela un turno en estado PENDIENTE o CONFIRMADO."""
        return self._transicionar(turno, ESTADO_CANCELADO)

    def completar(self, turno: Turno) -> Turno:
        """Marca como completado un turno en estado CONFIRMADO."""
        return self._transicionar(turno, ESTADO_COMPLETADO)
