"""Pruebas de integración HTTP para el catálogo multi-tenant (C-04) contra SQLite real.

Cumplimiento estricto de AGENTS.md y odontologia-api-guard:
- SQLite real en archivo temporal (tmp_path), sin mocks de BD ni servicios (D-04).
- Aislamiento por tenant mediante header X-Tenant-ID (RN-05).
- Datos 100% sintéticos (RN-06).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.persistence.database import get_connection


@pytest.fixture()
def cliente_catalogo(tmp_path: Path) -> tuple[TestClient, Path]:
    """Inicializa la aplicación FastAPI sobre una BD SQLite temporal limpia."""
    db_file = tmp_path / "test_catalogo.db"
    app = create_app(database_path=str(db_file))
    return TestClient(app), db_file


def test_catalogo_profesionales_alta_listado_filtro_y_detalle(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """POST y GET de profesionales persisten matrícula/especialidad y filtran por activo."""
    client, _ = cliente_catalogo
    headers = {"X-Tenant-ID": "clinica-a"}

    r1 = client.post(
        "/api/v1/profesionales",
        json={
            "nombre": "Dr. Ejemplo",
            "matricula": "MP-1001",
            "especialidad": "Odontología General",
            "activo": True,
        },
        headers=headers,
    )
    assert r1.status_code == 201
    prof1 = r1.json()
    assert prof1["nombre"] == "Dr. Ejemplo"
    assert prof1["matricula"] == "MP-1001"
    assert prof1["especialidad"] == "Odontología General"
    assert prof1["activo"] is True
    assert prof1["tenant_id"] == "clinica-a"

    r2 = client.post(
        "/api/v1/profesionales",
        json={
            "nombre": "Dra. Inactiva",
            "matricula": "MP-1002",
            "especialidad": "Endodoncia",
            "activo": False,
        },
        headers=headers,
    )
    assert r2.status_code == 201

    todos = client.get("/api/v1/profesionales", headers=headers)
    assert todos.status_code == 200
    assert len(todos.json()) == 2

    activos = client.get(
        "/api/v1/profesionales", params={"solo_activos": True}, headers=headers
    )
    assert activos.status_code == 200
    assert [p["nombre"] for p in activos.json()] == ["Dr. Ejemplo"]

    inactivos = client.get(
        "/api/v1/profesionales", params={"solo_activos": False}, headers=headers
    )
    assert inactivos.status_code == 200
    assert [p["nombre"] for p in inactivos.json()] == ["Dra. Inactiva"]

    detalle = client.get(f"/api/v1/profesionales/{prof1['id']}", headers=headers)
    assert detalle.status_code == 200
    assert detalle.json()["matricula"] == "MP-1001"

    inexistente = client.get("/api/v1/profesionales/no-existe", headers=headers)
    assert inexistente.status_code == 404
    assert inexistente.json()["codigo"] == "RECURSO_NO_ENCONTRADO"


def test_catalogo_profesionales_duplicado_409_y_aislamiento_entre_tenants(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """Duplicar matrícula o nombre en el mismo tenant retorna 409; en otro tenant se permite."""
    client, _ = cliente_catalogo
    headers_a = {"X-Tenant-ID": "clinica-a"}
    headers_b = {"X-Tenant-ID": "clinica-b"}

    assert (
        client.post(
            "/api/v1/profesionales",
            json={"nombre": "Dr. Ejemplo", "matricula": "MP-2001"},
            headers=headers_a,
        ).status_code
        == 201
    )

    # Misma matrícula en clinica-a -> 409
    dup_mat = client.post(
        "/api/v1/profesionales",
        json={"nombre": "Dra. Prueba", "matricula": "mp-2001"},
        headers=headers_a,
    )
    assert dup_mat.status_code == 409
    assert dup_mat.json()["codigo"] == "RECURSO_DUPLICADO"
    assert dup_mat.json()["recurso"] == "profesional"

    # Mismo nombre en clinica-a -> 409
    dup_nom = client.post(
        "/api/v1/profesionales",
        json={"nombre": "dr. ejemplo", "matricula": "MP-9999"},
        headers=headers_a,
    )
    assert dup_nom.status_code == 409
    assert dup_nom.json()["codigo"] == "RECURSO_DUPLICADO"

    # Mismos datos en clinica-b -> 201 permitido
    otro_tenant = client.post(
        "/api/v1/profesionales",
        json={"nombre": "Dr. Ejemplo", "matricula": "MP-2001"},
        headers=headers_b,
    )
    assert otro_tenant.status_code == 201


def test_catalogo_sillones_alta_filtro_duplicado_409_y_404(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """POST/GET de sillones persisten equipamiento, filtran activos y rechazan duplicados."""
    client, _ = cliente_catalogo
    headers = {"X-Tenant-ID": "clinica-a"}

    r1 = client.post(
        "/api/v1/sillones",
        json={
            "nombre": "Sillón 1",
            "equipamiento": "Unidad dental con RX",
            "activo": True,
        },
        headers=headers,
    )
    assert r1.status_code == 201
    sil1 = r1.json()
    assert sil1["equipamiento"] == "Unidad dental con RX"

    r2 = client.post(
        "/api/v1/sillones",
        json={
            "nombre": "Sillón Mantenimiento",
            "equipamiento": "Unidad quirúrgica",
            "activo": False,
        },
        headers=headers,
    )
    assert r2.status_code == 201

    activos = client.get(
        "/api/v1/sillones", params={"solo_activos": True}, headers=headers
    )
    assert activos.status_code == 200
    assert [s["nombre"] for s in activos.json()] == ["Sillón 1"]

    detalle = client.get(f"/api/v1/sillones/{sil1['id']}", headers=headers)
    assert detalle.status_code == 200
    assert detalle.json()["nombre"] == "Sillón 1"

    duplicado = client.post(
        "/api/v1/sillones",
        json={"nombre": "sillón 1", "equipamiento": "Otro equipo"},
        headers=headers,
    )
    assert duplicado.status_code == 409
    assert duplicado.json()["codigo"] == "RECURSO_DUPLICADO"
    assert duplicado.json()["recurso"] == "sillon"

    assert client.get("/api/v1/sillones/no-existe", headers=headers).status_code == 404


def test_catalogo_pacientes_alta_filtros_dni_nombre_y_duplicado_409(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """POST/GET de pacientes filtran por dni/nombre y rechazan DNI repetido en el tenant."""
    client, _ = cliente_catalogo
    headers_a = {"X-Tenant-ID": "clinica-a"}
    headers_b = {"X-Tenant-ID": "clinica-b"}

    r1 = client.post(
        "/api/v1/pacientes",
        json={
            "nombre": "Paciente Ficticio",
            "dni": "99887766",
            "telefono": "11-0000-0001",
        },
        headers=headers_a,
    )
    assert r1.status_code == 201
    pac1 = r1.json()
    assert pac1["telefono"] == "11-0000-0001"

    r2 = client.post(
        "/api/v1/pacientes",
        json={"nombre": "Paciente Prueba Dos", "dni": "11223344", "telefono": ""},
        headers=headers_a,
    )
    assert r2.status_code == 201

    por_dni = client.get(
        "/api/v1/pacientes", params={"dni": "99887766"}, headers=headers_a
    )
    assert por_dni.status_code == 200
    assert len(por_dni.json()) == 1
    assert por_dni.json()[0]["id"] == pac1["id"]

    por_nombre = client.get(
        "/api/v1/pacientes", params={"nombre": "ficticio"}, headers=headers_a
    )
    assert por_nombre.status_code == 200
    assert [p["nombre"] for p in por_nombre.json()] == ["Paciente Ficticio"]

    dup_dni = client.post(
        "/api/v1/pacientes",
        json={"nombre": "Otro Paciente", "dni": "99887766"},
        headers=headers_a,
    )
    assert dup_dni.status_code == 409
    assert dup_dni.json()["codigo"] == "RECURSO_DUPLICADO"
    assert dup_dni.json()["recurso"] == "paciente"

    # Mismo DNI con distinto case (ej. alfanumérico) en mismo tenant -> 409
    assert (
        client.post(
            "/api/v1/pacientes",
            json={"nombre": "Paciente Alfanumérico", "dni": "EXT-100"},
            headers=headers_a,
        ).status_code
        == 201
    )
    dup_dni_case = client.post(
        "/api/v1/pacientes",
        json={"nombre": "Otro Paciente", "dni": "ext-100"},
        headers=headers_a,
    )
    assert dup_dni_case.status_code == 409
    assert dup_dni_case.json()["codigo"] == "RECURSO_DUPLICADO"

    # Mismo DNI en otro tenant sí se permite
    assert (
        client.post(
            "/api/v1/pacientes",
            json={"nombre": "Paciente B", "dni": "99887766"},
            headers=headers_b,
        ).status_code
        == 201
    )


def test_catalogo_aislamiento_cross_tenant_y_validaciones_422(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """Lecturas cross-tenant devuelven 404 y payloads/headers inválidos devuelven 422."""
    client, _ = cliente_catalogo
    headers_a = {"X-Tenant-ID": "clinica-a"}
    headers_b = {"X-Tenant-ID": "clinica-b"}

    prof = client.post(
        "/api/v1/profesionales",
        json={"nombre": "Dr. Ejemplo"},
        headers=headers_a,
    ).json()
    sillon = client.post(
        "/api/v1/sillones",
        json={"nombre": "Sillón 1"},
        headers=headers_a,
    ).json()
    paciente = client.post(
        "/api/v1/pacientes",
        json={"nombre": "Paciente Ficticio", "dni": "99887766"},
        headers=headers_a,
    ).json()

    assert (
        client.get(f"/api/v1/profesionales/{prof['id']}", headers=headers_b).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/sillones/{sillon['id']}", headers=headers_b).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/pacientes/{paciente['id']}", headers=headers_b).status_code
        == 404
    )
    assert client.get("/api/v1/profesionales", headers=headers_b).json() == []
    assert client.get("/api/v1/sillones", headers=headers_b).json() == []
    assert client.get("/api/v1/pacientes", headers=headers_b).json() == []

    # Nombres en blanco o falta de X-Tenant-ID -> 422
    assert (
        client.post(
            "/api/v1/profesionales",
            json={"nombre": "   "},
            headers=headers_a,
        ).status_code
        == 422
    )
    assert client.get("/api/v1/pacientes").status_code == 422


def test_catalogo_flujo_e2e_alta_recursos_y_reserva_turno(
    cliente_catalogo: tuple[TestClient, Path],
) -> None:
    """Los recursos y pacientes creados vía HTTP sirven de inmediato para reservar turnos."""
    client, _ = cliente_catalogo
    headers = {"X-Tenant-ID": "clinica-e2e"}

    prof = client.post(
        "/api/v1/profesionales",
        json={
            "nombre": "Dra. Prueba",
            "matricula": "MP-3001",
            "especialidad": "Ortodoncia",
        },
        headers=headers,
    ).json()
    sillon = client.post(
        "/api/v1/sillones",
        json={"nombre": "Sillón 1", "equipamiento": "Unidad completa"},
        headers=headers,
    ).json()
    paciente = client.post(
        "/api/v1/pacientes",
        json={
            "nombre": "Paciente Ficticio",
            "dni": "44556677",
            "telefono": "11-0000-0002",
        },
        headers=headers,
    ).json()

    turno = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": paciente["id"],
            "profesional_id": prof["id"],
            "sillon_id": sillon["id"],
            "fecha": "2026-11-25",
            "hora_inicio": "14:00",
            "hora_fin": "14:30",
        },
        headers=headers,
    )
    assert turno.status_code == 201
    data = turno.json()
    assert data["profesional_nombre"] == "Dra. Prueba"
    assert data["sillon_nombre"] == "Sillón 1"
    assert data["paciente_nombre"] == "Paciente Ficticio"

    # Un segundo turno solapado sobre el mismo profesional debe devolver 409
    solapado = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": paciente["id"],
            "profesional_id": prof["id"],
            "sillon_id": sillon["id"],
            "fecha": "2026-11-25",
            "hora_inicio": "14:15",
            "hora_fin": "14:45",
        },
        headers=headers,
    )
    assert solapado.status_code == 409
    assert solapado.json()["codigo"] == "SOLAPAMIENTO_PROFESIONAL"


def test_migracion_idempotente_desde_esquema_c02_conserva_datos(
    tmp_path: Path,
) -> None:
    """Una BD creada con el esquema antiguo C-02 migra columnas nuevas sin perder registros."""
    db_file = tmp_path / "legacy_c02.db"
    conn = get_connection(str(db_file))
    with conn:
        conn.executescript(
            """
            CREATE TABLE tenants (id TEXT PRIMARY KEY, nombre TEXT NOT NULL);
            CREATE TABLE profesionales (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE sillones (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE pacientes (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                dni TEXT
            );
            INSERT INTO tenants (id, nombre) VALUES ('demo-tenant', 'Clínica Demo');
            INSERT INTO profesionales (id, tenant_id, nombre, activo)
                VALUES ('prof-legacy', 'demo-tenant', 'Dr. Ejemplo', 1);
            INSERT INTO sillones (id, tenant_id, nombre, activo)
                VALUES ('sil-legacy', 'demo-tenant', 'Sillón 1', 1);
            INSERT INTO pacientes (id, tenant_id, nombre, dni)
                VALUES ('pac-legacy', 'demo-tenant', 'Paciente Ficticio', '12345678');
            """
        )
    conn.close()

    app = create_app(database_path=str(db_file))
    client = TestClient(app)
    headers = {"X-Tenant-ID": "demo-tenant"}

    profs = client.get("/api/v1/profesionales", headers=headers)
    assert profs.status_code == 200
    assert profs.json()[0]["id"] == "prof-legacy"
    assert profs.json()[0]["matricula"] == ""

    sillones = client.get("/api/v1/sillones", headers=headers)
    assert sillones.status_code == 200
    assert sillones.json()[0]["id"] == "sil-legacy"
    assert sillones.json()[0]["equipamiento"] == ""

    pacientes = client.get("/api/v1/pacientes", headers=headers)
    assert pacientes.status_code == 200
    assert pacientes.json()[0]["id"] == "pac-legacy"
    assert pacientes.json()[0]["telefono"] == ""
