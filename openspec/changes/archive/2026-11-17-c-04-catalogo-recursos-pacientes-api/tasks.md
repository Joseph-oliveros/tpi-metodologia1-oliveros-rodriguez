# Tasks: C-04 Catálogo API Multi-Tenant de Profesionales, Sillones y Pacientes

## 1. Dominio Puro, Excepciones y Puertos

- [x] 1.1 Extender `Profesional`, `Sillon` y `Paciente` en `backend/src/domain/models.py` con `matricula`, `especialidad`, `equipamiento` y `telefono` opcionales (default `""`) manteniendo retrocompatibilidad.
- [x] 1.2 Agregar `RecursoDuplicadoError` en `backend/src/domain/exceptions.py`, definir `RepositorioProfesionalesPort`, `RepositorioSillonesPort` y `RepositorioPacientesPort` en `backend/src/domain/ports.py`, e implementar `ServicioCatalogo` en `backend/src/domain/services.py` con validaciones de unicidad por tenant.

## 2. Persistencia SQLite, Migración Idempotente y Seed

- [x] 2.1 Actualizar `backend/src/persistence/database.py` para incluir las nuevas columnas en DDL y migrar tablas existentes de forma idempotente (`_migrar_columnas_faltantes`).
- [x] 2.2 Actualizar `backend/src/persistence/repositories.py` con soporte de nuevos campos y métodos `listar_por_tenant` filtrados en `RepositorioProfesionales`, `RepositorioSillones` y `RepositorioPacientes`, además de hidratar los campos completos en `RepositorioTurnos`.
- [x] 2.3 Enriquecer `backend/seed.py` con datos sintéticos de matrícula, especialidad, equipamiento y teléfono.

## 3. Capa API FastAPI y Skill `odontologia-api-guard`

- [x] 3.1 Actualizar `.agents/skills/odontologia-api-guard/references/http-contracts.md` (`RECURSO_DUPLICADO`) y ampliar `scripts/check_api_guards.py` para auditar todos los `test_*.py`.
- [x] 3.2 Agregar esquemas Pydantic v2 de Profesionales, Sillones y Pacientes en `backend/src/api/schemas.py`, handler de `RecursoDuplicadoError` (`409`) en `exception_handlers.py`, y `ServicioCatalogoDep` en `dependencies.py`.
- [x] 3.3 Implementar `routers/profesionales.py`, `routers/sillones.py`, `routers/pacientes.py` y registrarlos en `backend/src/api/main.py` aplicando `odontologia-api-guard`.

## 4. Verificación, Pruebas Reales y Documentación

- [x] 4.1 Crear `backend/tests/test_catalogo_api.py` contra SQLite real (`tmp_path`, sin mocks) cubriendo altas, listados, filtros, duplicados `409`, aislamiento multi-tenant (`404`), validaciones `422`, migración idempotente desde esquema `C-02` y flujo completo catálogo $\to$ turno (`POST /api/v1/turnos`).
- [x] 4.2 Ejecutar `python .agents/skills/odontologia-api-guard/scripts/check_api_guards.py`, `pytest -v` en `backend/` y verificación en vivo de Uvicorn + Swagger (`/openapi.json` y requests reales sobre `seed.py`).
- [x] 4.3 Actualizar `CHANGES.md`, `CONSIGNAS_TPI.md`, `README.md`, `AGENTS.md` y `CLAUDE.md`, validar con `openspec validate` y archivar `C-04`.
