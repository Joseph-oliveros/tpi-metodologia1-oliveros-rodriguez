"""Script de inicialización de datos sintéticos para SQLite (C-02 / Servidor MCP).

Crea la base de datos local 'turnos_odontologia.db' con datos 100% ficticios:
- 1 Tenant (Clínica Odontológica Demo)
- 2 Profesionales (Dr. Ejemplo y Dra. Prueba)
- 2 Sillones (Sillón 1 y Sillón 2)
- 1 Paciente ficticio (Paciente Ficticio)
- 2 Turnos de ejemplo confirmados sin solapamiento
"""

import sys
from pathlib import Path

# Asegurar que el directorio backend esté en el sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.domain.models import (
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


def seed_database(db_path: Path | None = None) -> Path:
    if db_path is None:
        db_path = backend_dir / "turnos_odontologia.db"

    print(f"[*] Inicializando base de datos en: {db_path}")
    conn = get_connection(str(db_path))
    init_db(conn)

    repo_tenants = RepositorioTenants(conn)
    repo_profs = RepositorioProfesionales(conn)
    repo_sillones = RepositorioSillones(conn)
    repo_pacientes = RepositorioPacientes(conn)
    repo_turnos = RepositorioTurnos(conn)

    tenant_id = "demo-tenant"

    # 1. Tenant
    tenant = repo_tenants.guardar(
        Tenant(id=tenant_id, nombre="Clínica Odontológica Demo")
    )
    print(f" [✓] Tenant registrado: {tenant.nombre} (ID: {tenant.id})")

    # 2. Profesionales sintéticos
    prof_1 = repo_profs.guardar(
        Profesional(id="prof-1", tenant_id=tenant_id, nombre="Dr. Ejemplo")
    )
    prof_2 = repo_profs.guardar(
        Profesional(id="prof-2", tenant_id=tenant_id, nombre="Dra. Prueba")
    )
    print(f" [✓] Profesionales registrados: {prof_1.nombre}, {prof_2.nombre}")

    # 3. Sillones sintéticos
    sillon_1 = repo_sillones.guardar(
        Sillon(id="sil-1", tenant_id=tenant_id, nombre="Sillón 1")
    )
    sillon_2 = repo_sillones.guardar(
        Sillon(id="sil-2", tenant_id=tenant_id, nombre="Sillón 2")
    )
    print(f" [✓] Sillones registrados: {sillon_1.nombre}, {sillon_2.nombre}")

    # 4. Paciente sintético
    paciente_1 = repo_pacientes.guardar(
        Paciente(
            id="pac-1",
            tenant_id=tenant_id,
            nombre="Paciente Ficticio",
            dni="99887766",
        )
    )
    print(f" [✓] Paciente registrado: {paciente_1.nombre} (DNI: {paciente_1.dni})")

    # 5. Turnos de ejemplo
    turno_1 = repo_turnos.guardar(
        Turno(
            id="turno-1",
            tenant_id=tenant_id,
            profesional=prof_1,
            sillon=sillon_1,
            fecha="2026-11-20",
            hora_inicio="09:00",
            hora_fin="09:30",
            paciente=paciente_1.nombre,
            estado=ESTADO_CONFIRMADO,
        )
    )
    turno_2 = repo_turnos.guardar(
        Turno(
            id="turno-2",
            tenant_id=tenant_id,
            profesional=prof_2,
            sillon=sillon_2,
            fecha="2026-11-20",
            hora_inicio="10:00",
            hora_fin="10:30",
            paciente=paciente_1.nombre,
            estado=ESTADO_CONFIRMADO,
        )
    )
    print(
        f" [✓] Turnos registrados: {turno_1.id} ({turno_1.fecha} {turno_1.hora_inicio}-{turno_1.hora_fin}) "
        f"y {turno_2.id} ({turno_2.fecha} {turno_2.hora_inicio}-{turno_2.hora_fin})"
    )

    conn.close()
    print("[*] Seed completado con éxito.")
    return db_path


if __name__ == "__main__":
    seed_database()
