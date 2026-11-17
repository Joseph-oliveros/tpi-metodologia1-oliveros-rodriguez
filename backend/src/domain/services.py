"""Servicio de dominio para el agendamiento de turnos odontológicos."""

from dataclasses import replace

from src.domain.exceptions import (
    RecursoDuplicadoError,
    SolapamientoProfesionalError,
    SolapamientoSillonError,
    TransicionInvalidaError,
)
from src.domain.models import (
    ESTADO_CANCELADO,
    ESTADO_COMPLETADO,
    ESTADO_CONFIRMADO,
    TRANSICIONES_PERMITIDAS,
    Paciente,
    Profesional,
    Sillon,
    Turno,
)
from src.domain.ports import (
    RepositorioPacientesPort,
    RepositorioProfesionalesPort,
    RepositorioSillonesPort,
    RepositorioTurnosEnMemoria,
    RepositorioTurnosPort,
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
    """Registra turnos validando solapamientos mediante puerto de persistencia multi-tenant (D-01, RN-05)."""

    def __init__(self, repositorio_turnos: RepositorioTurnosPort | None = None) -> None:
        self._repo: RepositorioTurnosPort = (
            repositorio_turnos
            if repositorio_turnos is not None
            else RepositorioTurnosEnMemoria()
        )

    def cerrar(self) -> None:
        """Conservado por compatibilidad; el ciclo de conexión pertenece a infraestructura."""
        return None

    @property
    def _turnos(self):
        """Adaptador de compatibilidad hacia atrás que redirige al puerto de turnos."""

        class _TurnosAdapter:
            def __init__(self, repo: RepositorioTurnosPort, tenant_id: str = "tenant-default"):
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
        paciente_id: str = "",
    ) -> Turno:
        """Crea y registra un turno si no hay solapamiento de profesional ni de sillón en el tenant."""
        inicio = _horas_a_minutos(hora_inicio)
        fin = _horas_a_minutos(hora_fin)
        if fin <= inicio:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")

        turnos_activos = self._repo.buscar_activos_por_fecha(tenant_id, fecha)
        for turno_existente in turnos_activos:
            existente_inicio = _horas_a_minutos(turno_existente.hora_inicio)
            existente_fin = _horas_a_minutos(turno_existente.hora_fin)
            if not _hay_solapamiento(inicio, fin, existente_inicio, existente_fin):
                continue
            # Doble validación de recurso: profesional y sillón, de forma independiente.
            mismo_profesional = (
                turno_existente.profesional.id == profesional.id
                or turno_existente.profesional.nombre == profesional.nombre
            )
            if mismo_profesional:
                raise SolapamientoProfesionalError(
                    f"El profesional {profesional.nombre} ya tiene un turno "
                    f"el {fecha} de {turno_existente.hora_inicio} a {turno_existente.hora_fin}"
                )
            mismo_sillon = (
                turno_existente.sillon.id == sillon.id
                or turno_existente.sillon.nombre == sillon.nombre
            )
            if mismo_sillon:
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
            paciente_id=paciente_id,
        )
        return self._repo.guardar(turno)

    def obtener_turno(self, tenant_id: str, turno_id: str) -> Turno | None:
        """Obtiene un turno por ID dentro del ámbito estricto del tenant."""
        return self._repo.obtener_por_id(tenant_id, turno_id)

    def listar_turnos(
        self,
        tenant_id: str = "tenant-default",
        fecha: str | None = None,
        profesional_id: str | None = None,
        sillon_id: str | None = None,
    ) -> list[Turno]:
        """Lista turnos del tenant aplicando filtros opcionales de agenda."""
        return self._repo.listar_por_tenant(
            tenant_id=tenant_id,
            fecha=fecha,
            profesional_id=profesional_id,
            sillon_id=sillon_id,
        )

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


class ServicioCatalogo:
    """Gestiona alta y consulta multi-tenant de profesionales, sillones y pacientes."""

    def __init__(
        self,
        repo_profesionales: RepositorioProfesionalesPort,
        repo_sillones: RepositorioSillonesPort,
        repo_pacientes: RepositorioPacientesPort,
    ) -> None:
        self._repo_profs = repo_profesionales
        self._repo_sillones = repo_sillones
        self._repo_pacientes = repo_pacientes

    def crear_profesional(
        self,
        tenant_id: str,
        nombre: str,
        matricula: str = "",
        especialidad: str = "",
        activo: bool = True,
    ) -> Profesional:
        """Registra un profesional validando unicidad de matrícula y nombre en el tenant."""
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre del profesional no puede estar vacío")
        matricula_limpia = matricula.strip()
        especialidad_limpia = especialidad.strip()

        existentes = self._repo_profs.listar_por_tenant(tenant_id)
        for existente in existentes:
            if (
                matricula_limpia
                and existente.matricula.strip().lower() == matricula_limpia.lower()
            ):
                raise RecursoDuplicadoError(
                    "profesional",
                    f"Ya existe un profesional con matrícula '{matricula_limpia}' en el tenant",
                )
            if existente.nombre.strip().lower() == nombre_limpio.lower():
                raise RecursoDuplicadoError(
                    "profesional",
                    f"Ya existe un profesional llamado '{nombre_limpio}' en el tenant",
                )

        return self._repo_profs.guardar(
            Profesional(
                nombre=nombre_limpio,
                tenant_id=tenant_id,
                activo=activo,
                matricula=matricula_limpia,
                especialidad=especialidad_limpia,
            )
        )

    def listar_profesionales(
        self, tenant_id: str, solo_activos: bool | None = None
    ) -> list[Profesional]:
        """Lista los profesionales del tenant con filtro opcional por estado activo."""
        return self._repo_profs.listar_por_tenant(
            tenant_id=tenant_id, solo_activos=solo_activos
        )

    def obtener_profesional(
        self, tenant_id: str, profesional_id: str
    ) -> Profesional | None:
        """Obtiene un profesional por ID dentro del tenant."""
        return self._repo_profs.obtener_por_id(tenant_id, profesional_id)

    def crear_sillon(
        self,
        tenant_id: str,
        nombre: str,
        equipamiento: str = "",
        activo: bool = True,
    ) -> Sillon:
        """Registra un sillón/box validando unicidad de nombre en el tenant."""
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre del sillón no puede estar vacío")
        equipamiento_limpio = equipamiento.strip()

        for existente in self._repo_sillones.listar_por_tenant(tenant_id):
            if existente.nombre.strip().lower() == nombre_limpio.lower():
                raise RecursoDuplicadoError(
                    "sillon",
                    f"Ya existe un sillón llamado '{nombre_limpio}' en el tenant",
                )

        return self._repo_sillones.guardar(
            Sillon(
                nombre=nombre_limpio,
                tenant_id=tenant_id,
                activo=activo,
                equipamiento=equipamiento_limpio,
            )
        )

    def listar_sillones(
        self, tenant_id: str, solo_activos: bool | None = None
    ) -> list[Sillon]:
        """Lista los sillones del tenant con filtro opcional por estado activo."""
        return self._repo_sillones.listar_por_tenant(
            tenant_id=tenant_id, solo_activos=solo_activos
        )

    def obtener_sillon(self, tenant_id: str, sillon_id: str) -> Sillon | None:
        """Obtiene un sillón por ID dentro del tenant."""
        return self._repo_sillones.obtener_por_id(tenant_id, sillon_id)

    def crear_paciente(
        self,
        tenant_id: str,
        nombre: str,
        dni: str = "",
        telefono: str = "",
    ) -> Paciente:
        """Registra un paciente validando unicidad de DNI no vacío dentro del tenant."""
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre del paciente no puede estar vacío")
        dni_limpio = dni.strip()
        telefono_limpio = telefono.strip()

        if dni_limpio:
            for existente in self._repo_pacientes.listar_por_tenant(
                tenant_id, dni=dni_limpio
            ):
                if existente.dni.strip().lower() == dni_limpio.lower():
                    raise RecursoDuplicadoError(
                        "paciente",
                        f"Ya existe un paciente con DNI '{dni_limpio}' en el tenant",
                    )

        return self._repo_pacientes.guardar(
            Paciente(
                nombre=nombre_limpio,
                dni=dni_limpio,
                tenant_id=tenant_id,
                telefono=telefono_limpio,
            )
        )

    def listar_pacientes(
        self,
        tenant_id: str,
        dni: str | None = None,
        nombre: str | None = None,
    ) -> list[Paciente]:
        """Lista los pacientes del tenant filtrando opcionalmente por DNI o nombre."""
        return self._repo_pacientes.listar_por_tenant(
            tenant_id=tenant_id,
            dni=dni.strip() if dni is not None else None,
            nombre=nombre.strip() if nombre is not None else None,
        )

    def obtener_paciente(self, tenant_id: str, paciente_id: str) -> Paciente | None:
        """Obtiene un paciente por ID dentro del tenant."""
        return self._repo_pacientes.obtener_por_id(tenant_id, paciente_id)
