---
name: odontologia-api-guard
description: >-
  Use this skill whenever designing, implementing, modifying, or reviewing HTTP
  endpoints, Pydantic schemas, FastAPI dependencies, or API integration tests in
  backend/src/api/ and backend/tests/. Enforces Clean Architecture boundaries,
  simultaneous double-resource validation delegation, strict tenant_id isolation,
  explicit domain-to-HTTP error mapping, synthetic data privacy, and real SQLite
  verification without mocks.
---

# Odontología API Guard

Project-specific architectural and domain guardrail for the **Turnos Odontológicos (SaaS)** FastAPI presentation layer.

## When to Activate

- Creating or editing routers, schemas, dependencies, or exception handlers in `backend/src/api/`.
- Creating or editing infrastructure wiring in `backend/src/infrastructure/`.
- Writing or updating HTTP integration tests in `backend/tests/`.
- Reviewing any API change (`C-03`, `C-04`, and subsequent endpoint changes) before archiving in OpenSpec.

## Mandatory Guardrails (6 Checks)

Before accepting or finishing any API task, verify all six guardrails:

1. **Clean Architecture & Dependency Direction (`D-02`, `architecture.md` §3)**
   - `src/api/` ONLY parses HTTP input, resolves `tenant_id`, invokes domain services (`ServicioTurnos`) or read-only catalog repositories, and serializes Pydantic responses.
   - **NEVER** implement overlap calculations (`inicio_a < fin_b and fin_a > inicio_b`), state transition matrices, or raw SQL queries inside `src/api/`.
   - **NEVER** import `fastapi`, `pydantic`, `starlette`, `sqlite3`, `src.persistence`, or `src.infrastructure` inside `src/domain/`.

2. **Double-Lock & Half-Open Interval Preservation (`RN-01`, `RN-02`, `RN-09`)**
   - All appointment creation MUST delegate to `ServicioTurnos.agendar_turno(...)` so Profesional and Sillón/Box availability are validated simultaneously and independently over `[inicio, fin)`.
   - HTTP schemas MUST validate basic input integrity (`YYYY-MM-DD`, `HH:MM`, and `hora_fin > hora_inicio` $\to$ `422 Unprocessable Entity`).

3. **Explicit Domain-to-HTTP Exception Mapping (`features.md` §5.2)**
   - Never leak unhandled domain exceptions as HTTP `500` or swallow them into generic `400`.
   - Use centralized FastAPI exception handlers matching [http-contracts.md](./references/http-contracts.md):
     - `SolapamientoProfesionalError` $\to$ `409 Conflict` (`codigo: "SOLAPAMIENTO_PROFESIONAL"`)
     - `SolapamientoSillonError` $\to$ `409 Conflict` (`codigo: "SOLAPAMIENTO_SILLON"`)
     - `TransicionInvalidaError` $\to$ `409 Conflict` (`codigo: "TRANSICION_INVALIDA"`)
     - Resource/appointment missing in tenant $\to$ `404 Not Found` (`codigo: "RECURSO_NO_ENCONTRADO"`)
     - Validation error $\to$ `422 Unprocessable Entity`

4. **Mandatory Multi-Tenant Isolation (`RN-05`, `D-01`)**
   - Every operational endpoint MUST require and propagate `tenant_id` via an explicit FastAPI dependency (`Annotated[str, Depends(obtener_tenant_id)]` reading `X-Tenant-ID` prior to JWT auth).
   - Never accept `tenant_id` inside business request bodies to override session/header context, and never fall back silently to a default tenant if the caller sends an empty/blank tenant header.
   - Referenced entities (`paciente_id`, `profesional_id`, `sillon_id`, `turno_id`) belonging to another tenant MUST fail as `404 Not Found`.

5. **Privacy, Synthetic Data & Config Hygiene (`RN-06`, `D-05`)**
   - OpenAPI `examples`, docstrings, fixtures, and seed data MUST use strictly synthetic names (`Paciente Ficticio`, `Dr. Ejemplo`, `Dra. Prueba`, `Sillón 1`).
   - Database paths and runtime settings MUST be loaded from environment variables (`.env` / `DATABASE_URL`) via `src/infrastructure/config.py`, with zero secrets in code or repo.

6. **Real SQLite Integration Testing & Swagger Completeness (`D-04`)**
   - API tests MUST use FastAPI `TestClient` wired to a real temporary SQLite file (`tmp_path`) with `PRAGMA foreign_keys = ON`. **NEVER** mock `ServicioTurnos` or SQLite repositories in API tests.
   - Endpoints MUST declare typed return models, explicit status codes, and documented error responses (`responses={409: ..., 404: ...}`) so Swagger UI (`/docs`) accurately documents and tests every business rule.

## Execution & Verification Procedure

1. Read [http-contracts.md](./references/http-contracts.md) when adding new endpoints or error mappings.
2. Ensure the corresponding OpenSpec specification exists in `openspec/changes/` before editing `backend/src/` or `backend/tests/` (`Spec First`).
3. Run the automated static guard checker from the repository root:
   ```powershell
   python .agents/skills/odontologia-api-guard/scripts/check_api_guards.py
   ```
4. Run the full test suite against real SQLite from `backend/`:
   ```powershell
   pytest -v
   ```
5. Both the guard script and the full `pytest` suite MUST pass with exit code `0`.
