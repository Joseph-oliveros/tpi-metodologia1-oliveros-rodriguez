"""Configuración de la aplicación desde variables de entorno y archivo .env (D-05)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def resolver_ruta_sqlite(database_url: str) -> str:
    """Convierte un DATABASE_URL en una ruta utilizable por sqlite3."""
    url = database_url.strip()
    if url in {":memory:", "sqlite:///:memory:"}:
        return ":memory:"
    if url.startswith("sqlite:///"):
        raw_path = url.removeprefix("sqlite:///")
        path = Path(raw_path)
        if not path.is_absolute():
            return str((BACKEND_DIR / path).resolve())
        return str(path)
    return url


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución de la API sin secretos embebidos."""

    app_name: str = "API de Turnos Odontológicos"
    app_version: str = "0.4.0"
    database_url: str = "sqlite:///./turnos_odontologia.db"

    @property
    def sqlite_path(self) -> str:
        """Retorna la ruta física o ':memory:' para SQLite."""
        return resolver_ruta_sqlite(self.database_url)


def get_settings() -> Settings:
    """Carga la configuración vigente desde el entorno."""
    return Settings(
        app_name=os.getenv("APP_NAME", "API de Turnos Odontológicos"),
        app_version=os.getenv("APP_VERSION", "0.4.0"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./turnos_odontologia.db"),
    )
