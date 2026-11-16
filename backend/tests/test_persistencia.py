"""Pruebas de la capa de persistencia en SQLite real con multi-tenancy.

Cumplimiento estricto de AGENTS.md:
- SQLite real sin mocks (D-04, regla 5).
- tenant_id siempre presente y aislamiento estricto (RN-05, D-01, regla 8).
- Datos 100% sintéticos (regla 3).
"""

import sqlite3
from dataclasses import replace
import pytest

from src.domain.exceptions import SolapamientoProfesionalError
from src.domain.models import (
    ESTADO_CANCELADO,
    ESTADO_CONFIRMADO,
    Paciente,
    Profesional,
    Sillon,
    Tenant,
    Turno,
)
from src.persistence.database import get_connection, init_db
from src.persistence.repositories import (
    RepositorioPacientes,
    RepositorioProfesionales,
    RepositorioSillones,
    RepositorioTenants,
    RepositorioTurnos,
)


def test_inicializacion_base_de_datos_crea_tablas_relacionales() -> None:
    """Task 1.1: init_db crea todas las tablas requeridas con foreign keys activas."""
    conn = get_connection(":memory:")
    init_db(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = {fila[0] for fila in cursor.fetchall()}

    tablas_esperadas = {"tenants", "profesionales", "sillones", "pacientes", "turnos"}
    assert tablas_esperadas.issubset(tablas)

    # Verificar que PRAGMA foreign_keys está activo
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    assert fk_status == 1

    conn.close()


def test_repositorios_auxiliares_crud_y_aislamiento_tenant() -> None:
    """Task 2.2: Repositorios de Tenants, Profesionales, Sillones y Pacientes en SQLite real."""
    conn = get_connection(":memory:")
    init_db(conn)

    repo_tenants = RepositorioTenants(conn)
    repo_profs = RepositorioProfesionales(conn)
    repo_sillones = RepositorioSillones(conn)
    repo_pacientes = RepositorioPacientes(conn)

    tenant_a = repo_tenants.guardar(Tenant(id="tenant-a", nombre="Clínica Norte"))
    tenant_b = repo_tenants.guardar(Tenant(id="tenant-b", nombre="Clínica Sur"))

    prof_a = repo_profs.guardar(Profesional(nombre="Dr. Pérez", tenant_id="tenant-a"))
    prof_b = repo_profs.guardar(Profesional(nombre="Dr. Pérez", tenant_id="tenant-b"))

    assert repo_profs.obtener_por_id("tenant-a", prof_a.id) is not None
    # No se puede acceder con otro tenant_id (aislamiento)
    assert repo_profs.obtener_por_id("tenant-b", prof_a.id) is None

    sillon_a = repo_sillones.guardar(Sillon(nombre="Sillón 1", tenant_id="tenant-a"))
    assert repo_sillones.obtener_por_id("tenant-a", sillon_a.id) is not None
    assert repo_sillones.obtener_por_id("tenant-b", sillon_a.id) is None

    paciente_a = repo_pacientes.guardar(
        Paciente(nombre="Paciente Ficticio", dni="123456", tenant_id="tenant-a")
    )
    assert repo_pacientes.obtener_por_id("tenant-a", paciente_a.id) is not None
    assert repo_pacientes.obtener_por_id("tenant-b", paciente_a.id) is None

    conn.close()


def test_repositorio_turnos_crud_y_filtrado_por_tenant() -> None:
    """Task 2.1: RepositorioTurnos guarda, actualiza y filtra por tenant y fecha en SQLite real."""
    conn = get_connection(":memory:")
    init_db(conn)

    repo_turnos = RepositorioTurnos(conn)
    profesional = Profesional(nombre="Dr. Pérez", tenant_id="tenant-a")
    sillon = Sillon(nombre="Sillón 1", tenant_id="tenant-a")
    turno = Turno(
        profesional=profesional,
        sillon=sillon,
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        paciente="Paciente Ficticio",
        estado=ESTADO_CONFIRMADO,
        tenant_id="tenant-a",
    )

    turno_guardado = repo_turnos.guardar(turno)
    assert turno_guardado.id != ""

    # Recuperar por ID
    turno_obtenido = repo_turnos.obtener_por_id("tenant-a", turno_guardado.id)
    assert turno_obtenido is not None
    assert turno_obtenido.paciente == "Paciente Ficticio"
    assert turno_obtenido.profesional.nombre == "Dr. Pérez"
    assert turno_obtenido.sillon.nombre == "Sillón 1"

    # Aislamiento: con tenant_id incorrecto no lo encuentra
    assert repo_turnos.obtener_por_id("tenant-b", turno_guardado.id) is None

    # Buscar activos por fecha
    activos = repo_turnos.buscar_activos_por_fecha("tenant-a", "2026-11-01")
    assert len(activos) == 1

    # Actualizar estado a CANCELADO
    turno_cancelado = replace(turno_guardado, estado=ESTADO_CANCELADO)
    repo_turnos.actualizar(turno_cancelado)

    turno_actualizado = repo_turnos.obtener_por_id("tenant-a", turno_guardado.id)
    assert turno_actualizado is not None
    assert turno_actualizado.estado == ESTADO_CANCELADO

    # Al estar cancelado, ya no aparece como activo
    activos_post_cancelacion = repo_turnos.buscar_activos_por_fecha("tenant-a", "2026-11-01")
    assert len(activos_post_cancelacion) == 0

    conn.close()


def test_escenario_turnos_simultaneos_en_clinicas_distintas_no_solapan() -> None:
    """Task 3.3: Aislamiento multi-tenant (RN-05): clínicas distintas no generan conflicto de agenda."""
    from src.domain.services import ServicioTurnos

    conn = get_connection(":memory:")
    init_db(conn)
    repo_turnos = RepositorioTurnos(conn)
    servicio = ServicioTurnos(repositorio_turnos=repo_turnos)

    # Clínica A agenda de 10:00 a 10:30
    turno_a = servicio.agendar_turno(
        paciente="Paciente A",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez", tenant_id="clinica-a"),
        sillon=Sillon(nombre="Sillón 1", tenant_id="clinica-a"),
        tenant_id="clinica-a",
    )
    assert turno_a.estado == ESTADO_CONFIRMADO

    # Clínica B agenda en el MISMO horario exacto con mismos nombres de recursos: NO debe haber conflicto
    turno_b = servicio.agendar_turno(
        paciente="Paciente B",
        fecha="2026-11-01",
        hora_inicio="10:00",
        hora_fin="10:30",
        profesional=Profesional(nombre="Dr. Pérez", tenant_id="clinica-b"),
        sillon=Sillon(nombre="Sillón 1", tenant_id="clinica-b"),
        tenant_id="clinica-b",
    )
    assert turno_b.estado == ESTADO_CONFIRMADO

    # Cada clínica solo ve sus turnos
    assert len(servicio.turnos_registrados(tenant_id="clinica-a")) == 1
    assert len(servicio.turnos_registrados(tenant_id="clinica-b")) == 1

    # Pero dentro de la MISMA clínica A, solaparse sí lanza SolapamientoProfesionalError
    with pytest.raises(SolapamientoProfesionalError):
        servicio.agendar_turno(
            paciente="Paciente C",
            fecha="2026-11-01",
            hora_inicio="10:15",
            hora_fin="10:45",
            profesional=Profesional(nombre="Dr. Pérez", tenant_id="clinica-a"),
            sillon=Sillon(nombre="Sillón 2", tenant_id="clinica-a"),
            tenant_id="clinica-a",
        )

    conn.close()
