"""Inicialización y gestión de conexiones SQLite para persistencia relacional."""

import sqlite3


def get_connection(database_url: str = ":memory:") -> sqlite3.Connection:
    """Retorna una conexión a SQLite configurada con PRAGMA foreign_keys y row_factory."""
    conn = sqlite3.connect(database_url)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Crea el esquema DDL relacional con tablas y restricciones multi-tenant."""
    with conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profesionales (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sillones (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pacientes (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                dni TEXT,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS turnos (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                paciente_id TEXT NOT NULL,
                profesional_id TEXT NOT NULL,
                sillon_id TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                estado TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                FOREIGN KEY (profesional_id) REFERENCES profesionales(id) ON DELETE CASCADE,
                FOREIGN KEY (sillon_id) REFERENCES sillones(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_turnos_tenant_fecha
                ON turnos(tenant_id, fecha);
            CREATE INDEX IF NOT EXISTS idx_turnos_profesional
                ON turnos(tenant_id, profesional_id, fecha);
            CREATE INDEX IF NOT EXISTS idx_turnos_sillon
                ON turnos(tenant_id, sillon_id, fecha);
            """
        )
