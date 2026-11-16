"""Pruebas de integración HTTP para la API FastAPI contra SQLite real (sin mocks).

Cumplimiento de AGENTS.md y skill odontologia-api-guard:
- SQLite real en archivo temporal (tmp_path), nunca mocks de BD o servicios (D-04).
- Aislamiento estricto por tenant mediante header X-Tenant-ID (RN-05).
- Datos 100% sintéticos (RN-06).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.domain.models import (
    ESTADO_PENDIENTE,
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


@pytest.fixture()
def entorno_api(tmp_path: Path) -> tuple[TestClient, Path]:
    """Inicializa una BD SQLite real con datos sintéticos en dos tenants y retorna TestClient."""
    db_file = tmp_path / "test_api.db"
    app = create_app(database_path=str(db_file))

    conn = get_connection(str(db_file))
    init_db(conn)
    try:
        repo_tenants = RepositorioTenants(conn)
        repo_profs = RepositorioProfesionales(conn)
        repo_sillones = RepositorioSillones(conn)
        repo_pacientes = RepositorioPacientes(conn)

        # Tenant A (demo-tenant)
        repo_tenants.guardar(Tenant(id="clinica-a", nombre="Clínica Dental Norte"))
        repo_profs.guardar(
            Profesional(id="prof-a1", tenant_id="clinica-a", nombre="Dr. Ejemplo")
        )
        repo_profs.guardar(
            Profesional(id="prof-a2", tenant_id="clinica-a", nombre="Dra. Prueba")
        )
        repo_sillones.guardar(
            Sillon(id="sil-a1", tenant_id="clinica-a", nombre="Sillón 1")
        )
        repo_sillones.guardar(
            Sillon(id="sil-a2", tenant_id="clinica-a", nombre="Sillón 2")
        )
        repo_pacientes.guardar(
            Paciente(
                id="pac-a1",
                tenant_id="clinica-a",
                nombre="Paciente Ficticio",
                dni="11223344",
            )
        )

        # Tenant B (clinica-b)
        repo_tenants.guardar(Tenant(id="clinica-b", nombre="Clínica Dental Sur"))
        repo_profs.guardar(
            Profesional(id="prof-b1", tenant_id="clinica-b", nombre="Dr. Ejemplo")
        )
        repo_sillones.guardar(
            Sillon(id="sil-b1", tenant_id="clinica-b", nombre="Sillón 1")
        )
        repo_pacientes.guardar(
            Paciente(
                id="pac-b1",
                tenant_id="clinica-b",
                nombre="Paciente B",
                dni="55667788",
            )
        )
    finally:
        conn.close()

    return TestClient(app), db_file


def test_api_health_y_swagger_disponibles(entorno_api: tuple[TestClient, Path]) -> None:
    """GET /api/health, /docs y /openapi.json responden 200 correctamente."""
    client, _ = entorno_api

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "turnos-odontologia-api"}

    docs = client.get("/docs")
    assert docs.status_code == 200

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/api/v1/turnos" in openapi.json()["paths"]


def test_api_crear_turno_exitoso_y_persistido_en_sqlite(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """POST /api/v1/turnos crea el turno con estado CONFIRMADO y lo persiste en SQLite."""
    client, db_file = entorno_api
    payload = {
        "paciente_id": "pac-a1",
        "profesional_id": "prof-a1",
        "sillon_id": "sil-a1",
        "fecha": "2026-11-20",
        "hora_inicio": "10:00",
        "hora_fin": "10:30",
    }

    resp = client.post("/api/v1/turnos", json=payload, headers={"X-Tenant-ID": "clinica-a"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["tenant_id"] == "clinica-a"
    assert data["estado"] == "CONFIRMADO"
    assert data["paciente_id"] == "pac-a1"
    assert data["profesional_id"] == "prof-a1"
    assert data["sillon_id"] == "sil-a1"

    conn = get_connection(str(db_file))
    try:
        persistido = RepositorioTurnos(conn).obtener_por_id("clinica-a", data["id"])
        assert persistido is not None
        assert persistido.estado == "CONFIRMADO"
    finally:
        conn.close()


def test_api_turnos_contiguos_permitidos(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """Intervalos semiabiertos [inicio, fin): un turno de 10:30 a 11:00 tras 10:00-10:30 retorna 201."""
    client, _ = entorno_api
    headers = {"X-Tenant-ID": "clinica-a"}

    r1 = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers=headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:30",
            "hora_fin": "11:00",
        },
        headers=headers,
    )
    assert r2.status_code == 201


def test_api_doble_validacion_conflictos_409_y_precedencia_rn09(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """Conflicto de profesional, conflicto de sillón y precedencia RN-09 retornan 409 estructurado."""
    client, _ = entorno_api
    headers = {"X-Tenant-ID": "clinica-a"}

    base = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers=headers,
    )
    assert base.status_code == 201

    # Conflicto de profesional en otro sillón
    conf_prof = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a2",
            "fecha": "2026-11-20",
            "hora_inicio": "10:15",
            "hora_fin": "10:45",
        },
        headers=headers,
    )
    assert conf_prof.status_code == 409
    assert conf_prof.json()["codigo"] == "SOLAPAMIENTO_PROFESIONAL"
    assert conf_prof.json()["recurso"] == "profesional"

    # Conflicto de sillón con otro profesional
    conf_sillon = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a2",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:15",
            "hora_fin": "10:45",
        },
        headers=headers,
    )
    assert conf_sillon.status_code == 409
    assert conf_sillon.json()["codigo"] == "SOLAPAMIENTO_SILLON"
    assert conf_sillon.json()["recurso"] == "sillon"

    # Conflicto simultáneo de ambos: RN-09 prioriza profesional
    conf_ambos = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:15",
            "hora_fin": "10:45",
        },
        headers=headers,
    )
    assert conf_ambos.status_code == 409
    assert conf_ambos.json()["codigo"] == "SOLAPAMIENTO_PROFESIONAL"


def test_api_recurso_inexistente_o_cross_tenant_retorna_404(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """Referenciar un ID inexistente o perteneciente a otro tenant retorna 404."""
    client, _ = entorno_api

    # Profesional de clinica-b solicitado desde clinica-a
    resp = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-b1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert resp.status_code == 404
    assert resp.json()["codigo"] == "RECURSO_NO_ENCONTRADO"
    assert resp.json()["recurso"] == "profesional"

    # Paciente inexistente
    resp_pac = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-inexistente",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert resp_pac.status_code == 404
    assert resp_pac.json()["recurso"] == "paciente"

    # Sillón inexistente
    resp_sil = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-inexistente",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert resp_sil.status_code == 404
    assert resp_sil.json()["recurso"] == "sillon"


def test_api_validacion_intervalo_y_header_tenant_422(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """Intervalo hora_fin <= hora_inicio o X-Tenant-ID faltante/vacío retornan 422."""
    client, _ = entorno_api

    # hora_fin == hora_inicio
    r_inv = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:00",
        },
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert r_inv.status_code == 422

    # Sin header X-Tenant-ID
    r_sin_tenant = client.get("/api/v1/turnos")
    assert r_sin_tenant.status_code == 422

    # Header X-Tenant-ID en blanco
    r_tenant_vacio = client.get("/api/v1/turnos", headers={"X-Tenant-ID": "   "})
    assert r_tenant_vacio.status_code == 422


def test_api_listar_turnos_con_filtros_y_aislamiento_tenant(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """GET /api/v1/turnos filtra por fecha/profesional/sillón y aísla estrictamente por tenant."""
    client, _ = entorno_api

    # Dos turnos en clinica-a y uno simultáneo en clinica-b
    assert (
        client.post(
            "/api/v1/turnos",
            json={
                "paciente_id": "pac-a1",
                "profesional_id": "prof-a1",
                "sillon_id": "sil-a1",
                "fecha": "2026-11-20",
                "hora_inicio": "09:00",
                "hora_fin": "09:30",
            },
            headers={"X-Tenant-ID": "clinica-a"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/turnos",
            json={
                "paciente_id": "pac-a1",
                "profesional_id": "prof-a2",
                "sillon_id": "sil-a2",
                "fecha": "2026-11-21",
                "hora_inicio": "11:00",
                "hora_fin": "11:30",
            },
            headers={"X-Tenant-ID": "clinica-a"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/turnos",
            json={
                "paciente_id": "pac-b1",
                "profesional_id": "prof-b1",
                "sillon_id": "sil-b1",
                "fecha": "2026-11-20",
                "hora_inicio": "09:00",
                "hora_fin": "09:30",
            },
            headers={"X-Tenant-ID": "clinica-b"},
        ).status_code
        == 201
    )

    todos_a = client.get("/api/v1/turnos", headers={"X-Tenant-ID": "clinica-a"})
    assert todos_a.status_code == 200
    assert len(todos_a.json()) == 2
    assert all(t["tenant_id"] == "clinica-a" for t in todos_a.json())

    filtrados_a = client.get(
        "/api/v1/turnos",
        params={"fecha": "2026-11-20", "profesional_id": "prof-a1"},
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert filtrados_a.status_code == 200
    assert len(filtrados_a.json()) == 1
    assert filtrados_a.json()[0]["sillon_id"] == "sil-a1"

    filtrados_sillon = client.get(
        "/api/v1/turnos",
        params={"sillon_id": "sil-a2"},
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert filtrados_sillon.status_code == 200
    assert len(filtrados_sillon.json()) == 1
    assert filtrados_sillon.json()[0]["profesional_id"] == "prof-a2"

    todos_b = client.get("/api/v1/turnos", headers={"X-Tenant-ID": "clinica-b"})
    assert todos_b.status_code == 200
    assert len(todos_b.json()) == 1
    assert todos_b.json()[0]["tenant_id"] == "clinica-b"


def test_api_cancelar_turno_libera_recursos_y_rechaza_transicion_invalida(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """PATCH cancelar libera profesional y sillón; transiciones inválidas devuelven 409."""
    client, _ = entorno_api
    headers = {"X-Tenant-ID": "clinica-a"}

    creado = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers=headers,
    )
    assert creado.status_code == 201
    turno_id = creado.json()["id"]

    # Intentar acceder desde clinica-b retorna 404
    cross_tenant = client.patch(
        f"/api/v1/turnos/{turno_id}/estado",
        json={"accion": "cancelar"},
        headers={"X-Tenant-ID": "clinica-b"},
    )
    assert cross_tenant.status_code == 404

    # Cancelar en clinica-a retorna 200 CANCELADO
    cancelado = client.patch(
        f"/api/v1/turnos/{turno_id}/estado",
        json={"accion": "cancelar"},
        headers=headers,
    )
    assert cancelado.status_code == 200
    assert cancelado.json()["estado"] == "CANCELADO"

    # Transición inválida sobre estado final CANCELADO retorna 409
    invalida = client.patch(
        f"/api/v1/turnos/{turno_id}/estado",
        json={"accion": "completar"},
        headers=headers,
    )
    assert invalida.status_code == 409
    assert invalida.json()["codigo"] == "TRANSICION_INVALIDA"

    # Reagendar en el mismo intervalo tras cancelación debe ser exitoso (201)
    reagendado = client.post(
        "/api/v1/turnos",
        json={
            "paciente_id": "pac-a1",
            "profesional_id": "prof-a1",
            "sillon_id": "sil-a1",
            "fecha": "2026-11-20",
            "hora_inicio": "10:00",
            "hora_fin": "10:30",
        },
        headers=headers,
    )
    assert reagendado.status_code == 201


def test_api_confirmar_y_completar_turno(
    entorno_api: tuple[TestClient, Path],
) -> None:
    """PATCH permite confirmar un turno PENDIENTE y luego completarlo a COMPLETADO."""
    client, db_file = entorno_api
    headers = {"X-Tenant-ID": "clinica-a"}

    # Sembrar turno en estado PENDIENTE en la BD real
    conn = get_connection(str(db_file))
    try:
        repo_turnos = RepositorioTurnos(conn)
        turno_pendiente = repo_turnos.guardar(
            Turno(
                id="turno-pend-1",
                tenant_id="clinica-a",
                profesional=Profesional(
                    id="prof-a1", tenant_id="clinica-a", nombre="Dr. Ejemplo"
                ),
                sillon=Sillon(
                    id="sil-a1", tenant_id="clinica-a", nombre="Sillón 1"
                ),
                fecha="2026-11-22",
                hora_inicio="09:00",
                hora_fin="09:30",
                paciente="Paciente Ficticio",
                paciente_id="pac-a1",
                estado=ESTADO_PENDIENTE,
            )
        )
    finally:
        conn.close()

    # Completar directamente un PENDIENTE debe fallar con 409
    comp_invalido = client.patch(
        f"/api/v1/turnos/{turno_pendiente.id}/estado",
        json={"accion": "completar"},
        headers=headers,
    )
    assert comp_invalido.status_code == 409
    assert comp_invalido.json()["codigo"] == "TRANSICION_INVALIDA"

    # Confirmar PENDIENTE -> CONFIRMADO
    confirmado = client.patch(
        f"/api/v1/turnos/{turno_pendiente.id}/estado",
        json={"accion": "confirmar"},
        headers=headers,
    )
    assert confirmado.status_code == 200
    assert confirmado.json()["estado"] == "CONFIRMADO"

    # Completar CONFIRMADO -> COMPLETADO
    completado = client.patch(
        f"/api/v1/turnos/{turno_pendiente.id}/estado",
        json={"accion": "completar"},
        headers=headers,
    )
    assert completado.status_code == 200
    assert completado.json()["estado"] == "COMPLETADO"


def test_api_sqlite_en_memoria_y_accion_invalida_422() -> None:
    """create_app(':memory:') mantiene tablas entre peticiones y rechaza acciones inválidas con 422."""
    app = create_app(database_path=":memory:")
    client = TestClient(app)

    assert client.get("/api/health").status_code == 200
    assert (
        client.get("/api/v1/turnos", headers={"X-Tenant-ID": "clinica-a"}).json()
        == []
    )
    r_bad = client.patch(
        "/api/v1/turnos/turno-x/estado",
        json={"accion": "eliminar"},
        headers={"X-Tenant-ID": "clinica-a"},
    )
    assert r_bad.status_code == 422
