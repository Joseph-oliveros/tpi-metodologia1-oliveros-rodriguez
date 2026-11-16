"""Gestión de conexiones SQLite y ensamblado de repositorios en infraestructura."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from src.persistence.database import get_connection, init_db
from src.persistence.repositories import (
    RepositorioPacientes,
    RepositorioProfesionales,
    RepositorioSillones,
    RepositorioTurnos,
)


def init_database(database_path: str) -> sqlite3.Connection | None:
    """Inicializa el esquema relacional y mantiene la conexión si es ':memory:'."""
    if database_path == ":memory:":
        conn = get_connection(":memory:")
        init_db(conn)
        return conn
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(database_path)
    try:
        init_db(conn)
    finally:
        conn.close()
    return None


@contextmanager
def db_session(database_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Provee una conexión SQLite por petición cerrándola de forma segura."""
    conn = get_connection(database_path)
    try:
        yield conn
    finally:
        conn.close()


def crear_repositorios(
    conn: sqlite3.Connection,
) -> tuple[
    RepositorioTurnos,
    RepositorioProfesionales,
    RepositorioSillones,
    RepositorioPacientes,
]:
    """Ensambla los adaptadores de repositorio sobre la conexión activa."""
    return (
        RepositorioTurnos(conn),
        RepositorioProfesionales(conn),
        RepositorioSillones(conn),
        RepositorioPacientes(conn),
    )
