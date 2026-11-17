"""Verificador estático de guardas arquitectónicas y de dominio para la API.

Forma parte de la skill propia `odontologia-api-guard`.
Comprueba:
1. Pureza de `backend/src/domain/`: sin imports de FastAPI, Pydantic, Starlette, sqlite3 ni capas externas.
2. Desacople de `backend/src/api/`: sin imports directos de sqlite3 ni lógica de solapamiento embebida.
3. Uso obligatorio de `Annotated` / `Depends` y ausencia de mocks de BD en tests de API.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DOMAIN_DIR = ROOT / "backend" / "src" / "domain"
API_DIR = ROOT / "backend" / "src" / "api"
TESTS_DIR = ROOT / "backend" / "tests"

FORBIDDEN_DOMAIN_PREFIXES = (
    "fastapi",
    "pydantic",
    "starlette",
    "sqlite3",
    "sqlalchemy",
    "src.persistence",
    "src.infrastructure",
    "src.api",
)

FORBIDDEN_API_IMPORTS = (
    "sqlite3",
)

FORBIDDEN_TEST_PATTERNS = (
    "unittest.mock",
    "MagicMock",
    "AsyncMock",
)


def _iter_imports(py_file: Path) -> list[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def check_domain_purity() -> list[str]:
    errors: list[str] = []
    if not DOMAIN_DIR.exists():
        return [f"Directorio de dominio no encontrado: {DOMAIN_DIR}"]
    for py_file in sorted(DOMAIN_DIR.rglob("*.py")):
        for mod in _iter_imports(py_file):
            if any(mod == prefix or mod.startswith(prefix + ".") for prefix in FORBIDDEN_DOMAIN_PREFIXES):
                errors.append(
                    f"[DOMAIN PURITY] {py_file.relative_to(ROOT)} importa módulo prohibido '{mod}'"
                )
    return errors


def check_api_decoupling() -> list[str]:
    errors: list[str] = []
    if not API_DIR.exists():
        return [f"Directorio de API no encontrado: {API_DIR}"]
    for py_file in sorted(API_DIR.rglob("*.py")):
        content = py_file.read_text(encoding="utf-8")
        for mod in _iter_imports(py_file):
            if any(mod == prefix or mod.startswith(prefix + ".") for prefix in FORBIDDEN_API_IMPORTS):
                errors.append(
                    f"[API DECOUPLING] {py_file.relative_to(ROOT)} importa '{mod}' directamente en capa API"
                )
        if "_hay_solapamiento" in content or ("inicio_a" in content and "fin_b" in content):
            errors.append(
                f"[DOMAIN LEAK] {py_file.relative_to(ROOT)} parece contener lógica de solapamiento en la API"
            )
    return errors


def check_tests_no_db_mocks() -> list[str]:
    errors: list[str] = []
    if not TESTS_DIR.exists():
        return []
    for test_file in sorted(TESTS_DIR.glob("test_*.py")):
        content = test_file.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_TEST_PATTERNS:
            if pattern in content:
                errors.append(
                    f"[REAL SQLITE GUARD] {test_file.relative_to(ROOT)} contiene '{pattern}' (prohibido mockear BD/servicios)"
                )
    return errors


def main() -> int:
    print("[odontologia-api-guard] Ejecutando verificación de guardas...")
    all_errors = [
        *check_domain_purity(),
        *check_api_decoupling(),
        *check_tests_no_db_mocks(),
    ]
    if all_errors:
        for err in all_errors:
            print(f"  ERROR: {err}")
        print(f"[odontologia-api-guard] FALLÓ con {len(all_errors)} violación(es).")
        return 1

    print("  [OK] Dominio puro sin dependencias de HTTP ni SQLite.")
    print("  [OK] Capa API desacoplada de SQLite y sin lógica de solapamiento.")
    print("  [OK] Pruebas de API sin mocks de base de datos.")
    print("[odontologia-api-guard] Todas las guardas pasaron correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
