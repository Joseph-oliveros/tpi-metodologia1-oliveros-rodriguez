# Tasks: C-03 Capa API Desacoplada y Endpoints de Turnos

## 1. Skill Propia, Documentación y Adaptación del Roadmap

- [x] 1.1 Crear la skill propia `.agents/skills/odontologia-api-guard/` (`SKILL.md`, `references/http-contracts.md` y `scripts/check_api_guards.py`) e integrarla en `AGENTS.md`, `CLAUDE.md` y `.atl/skill-registry.md`.
- [x] 1.2 Actualizar `CHANGES.md` reflejando el alcance adaptado de `C-03` y la planificación de `C-04` (`catalogo-recursos-pacientes-api`, Opción A), conservando intacta la trazabilidad histórica de `C-01` y `C-02`.

## 2. Desacople Estricto del Dominio y Soporte de Consultas en Repositorios

- [x] 2.1 Crear `backend/src/domain/ports.py` con `RepositorioTurnosPort` (`Protocol`) y `RepositorioTurnosEnMemoria`, eliminando de `backend/src/domain/services.py` los imports de `src.persistence`.
- [x] 2.2 Incorporar `paciente_id` en `Turno` (`backend/src/domain/models.py`) y métodos `obtener_turno` / `listar_turnos` en `ServicioTurnos` preservando compatibilidad con los 25 tests existentes.
- [x] 2.3 Actualizar `backend/src/persistence/repositories.py` para respetar IDs explícitos de `profesional`, `sillon` y `paciente` en `guardar()` y soportar filtros opcionales (`fecha`, `profesional_id`, `sillon_id`) en `listar_por_tenant()`.

## 3. Infraestructura y Capa API FastAPI

- [x] 3.1 Actualizar `backend/requirements.txt` con `fastapi`, `uvicorn`, `httpx`, `pydantic-settings` y `python-dotenv`.
- [x] 3.2 Crear `backend/src/infrastructure/config.py` y `backend/src/infrastructure/db.py` para resolver `DATABASE_URL` desde entorno/`.env` y administrar conexiones SQLite reales con `PRAGMA foreign_keys = ON`.
- [x] 3.3 Crear `backend/src/api/` (`schemas.py`, `exception_handlers.py`, `dependencies.py`, `routers/health.py`, `routers/turnos.py` y `main.py` con `create_app()`) aplicando `odontologia-api-guard`.

## 4. Verificación, Pruebas Reales y Documentación

- [x] 4.1 Implementar `backend/tests/test_api.py` con FastAPI `TestClient` sobre SQLite real (`tmp_path`, sin mocks), cubriendo `/api/health`, `/docs`, `POST /api/v1/turnos` (201, contiguos, conflictos 409, RN-09, 404, 422), `GET /api/v1/turnos` (filtros y aislamiento `X-Tenant-ID`) y `PATCH /api/v1/turnos/{id}/estado` (confirmar, cancelar con liberación, completar, 409 transición inválida).
- [x] 4.2 Ejecutar `python .agents/skills/odontologia-api-guard/scripts/check_api_guards.py` y `pytest -v` verificando el 100% de las pruebas en verde.
- [x] 4.3 Probar el servidor Uvicorn en vivo contra la base sembrada con `backend/seed.py` verificando `/api/health`, `/docs` (`/openapi.json`) y requests reales HTTP.
- [x] 4.4 Actualizar `AGENTS.md`, `CLAUDE.md`, `CONSIGNAS_TPI.md` y `README.md` con instrucciones de arranque de la API, acceso a Swagger, uso de `odontologia-api-guard` y estado completo vs. pendiente.
