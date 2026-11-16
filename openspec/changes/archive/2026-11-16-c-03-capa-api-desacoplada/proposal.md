# Proposal: C-03 Capa API Desacoplada y Endpoints de Turnos

## Why
Hasta `C-02` el proyecto cuenta con reglas de dominio puras (`C-01`) y persistencia relacional multi-tenant en SQLite (`C-02`), pero todavía no expone una API REST HTTP ejecutable con documentación interactiva Swagger/OpenAPI para operar el sistema desde un cliente web o desde pruebas reales. Además, `ServicioTurnos` (`backend/src/domain/services.py`) aún importa directamente módulos de `src.persistence`, acoplando la capa de dominio a SQLite.

Con la adaptación aprobada del roadmap para el TPI (resolución de `DP-01` con Python/FastAPI y adelanto de los endpoints de agenda de `C-05` previo a `C-04` Opción A y `C-05-auth`), este change cierra el desacople arquitectónico del backend y habilita el ciclo completo de turnos por HTTP.

## What Changes
- **Desacople del dominio (`Ports & Adapters`):**
  - Se define el puerto `RepositorioTurnosPort` (`Protocol`) en `backend/src/domain/ports.py` junto a un adaptador en memoria puro para mantener las pruebas unitarias sin dependencias de SQLite.
  - `ServicioTurnos` elimina sus imports directos de `src.persistence.database` y `src.persistence.repositories`, incorporando además métodos de consulta filtrada y obtención por ID (`listar_turnos`, `obtener_turno`).
- **Nueva capa de infraestructura (`backend/src/infrastructure/`):**
  - `config.py`: resolución de `DATABASE_URL` y parámetros de aplicación desde `.env` / variables de entorno (`D-05`), sin credenciales en el código.
  - `db.py`: inicialización del esquema SQLite y proveedor de conexiones con `PRAGMA foreign_keys = ON`.
- **Nueva capa de presentación HTTP (`backend/src/api/`):**
  - App factory `create_app(database_path: str | None = None)` en FastAPI con Swagger UI (`/docs`) y OpenAPI (`/openapi.json`).
  - Dependencias tipadas (`Annotated` / `Depends`) para ciclo de vida de conexión SQLite por request, repositorios, `ServicioTurnos` y resolución de contexto multi-tenant vía header `X-Tenant-ID`.
  - Mapeo centralizado de excepciones de dominio a códigos HTTP (`409 Conflict` para `SolapamientoProfesionalError`, `SolapamientoSillonError` y `TransicionInvalidaError`; `404 Not Found` para recursos o turnos inexistentes en el tenant; `422 Unprocessable Entity` para validaciones de formato/intervalo).
  - Endpoints:
    - `GET /api/health`
    - `POST /api/v1/turnos`
    - `GET /api/v1/turnos` (filtros opcionales `fecha`, `profesional_id`, `sillon_id`)
    - `PATCH /api/v1/turnos/{turno_id}/estado` (`confirmar` / `cancelar` / `completar`)
- **Integración de Skill Propia (`odontologia-api-guard`):**
  - Creación e integración en `.agents/skills/odontologia-api-guard/SKILL.md` (junto con referencia de contratos HTTP y script verificador estático `check_api_guards.py`), referenciada en `AGENTS.md`, `CLAUDE.md` y `.atl/skill-registry.md`.
- **Pruebas de integración reales (`backend/tests/test_api.py`):**
  - Suite HTTP con FastAPI `TestClient` contra SQLite real (`tmp_path`, sin mocks), verificando camino feliz, doble candado, precedencia `RN-09`, contiguos, aislamiento `X-Tenant-ID`, cancelación que libera recursos, `404`, `422` y Swagger UI.

## Capabilities

### New Capabilities
- `capa-api-desacoplada`: Exposición de API REST con FastAPI y Swagger UI desacoplada del dominio mediante puertos y adaptadores, resolución de contexto multi-tenant vía `X-Tenant-ID`, mapeo explícito de excepciones de dominio a HTTP y operación completa de turnos sobre SQLite real.

### Modified Capabilities

## Impact
- **Dominio (`backend/src/domain/`):** `ports.py` (nuevo), `models.py` (`paciente_id` opcional con `compare=False`), `services.py` (desacople de `src.persistence` y métodos de consulta para API).
- **Persistencia (`backend/src/persistence/repositories.py`):** soporte de filtrado opcional en `listar_por_tenant` y preservación de IDs explícitos de `profesional`/`sillon`/`paciente` en `guardar`.
- **Infraestructura (`backend/src/infrastructure/`):** nuevos módulos `config.py` y `db.py`.
- **API (`backend/src/api/`):** nuevos módulos `main.py`, `dependencies.py`, `schemas.py`, `exception_handlers.py`, `routers/health.py`, `routers/turnos.py`.
- **Dependencias y Pruebas (`backend/`):** actualización de `requirements.txt` (`fastapi`, `uvicorn`, `httpx`, `pydantic-settings`, `python-dotenv`) y nuevo archivo `tests/test_api.py`.
- **Documentación y Skills:** `.agents/skills/odontologia-api-guard/`, `AGENTS.md`, `CLAUDE.md`, `.atl/skill-registry.md`, `CHANGES.md`, `README.md`.
