# Proposal: C-04 Catálogo API Multi-Tenant de Profesionales, Sillones y Pacientes

## Why
En `C-03` se expuso la capa HTTP FastAPI y los endpoints operativos de turnos (`/api/v1/turnos`), pero las clínicas todavía dependen de los registros pre-cargados en `backend/seed.py` para poder crear un turno desde Swagger UI. No existen endpoints REST para dar de alta ni consultar profesionales, sillones y pacientes por clínica (`tenant_id`), ni los campos descriptivos previstos en el modelo de datos (`matricula`, `especialidad`, `equipamiento`, `telefono`).

Conforme a la adaptación aprobada del roadmap (`CHANGES.md`, Opción A), este change expone el catálogo multi-tenant en FastAPI aplicando la skill `odontologia-api-guard`, completando el flujo operativo de extremo a extremo desde Swagger UI sobre SQLite real.

## What Changes
- **Extensión de modelos y migración idempotente de esquema SQLite (`data-models.md` §2.2–2.4):**
  - Incorporación de campos descriptivos opcionales (con default `""` para retrocompatibilidad total): `matricula` y `especialidad` en `Profesional`, `equipamiento` en `Sillon`, y `telefono` en `Paciente`.
  - Migración automática e idempotente de columnas faltantes en `init_db` (`PRAGMA table_info` + `ALTER TABLE`) para preservar bases SQLite ya existentes sin pérdida de datos.
- **Puertos, validación de unicidad y servicio de catálogo en dominio (`backend/src/domain/`):**
  - Nuevos puertos (`RepositorioProfesionalesPort`, `RepositorioSillonesPort`, `RepositorioPacientesPort`) en `ports.py`.
  - Nueva excepción explícita `RecursoDuplicadoError` en `exceptions.py`.
  - Nuevo `ServicioCatalogo` en `services.py` que centraliza alta, listado filtrado y consulta por ID garantizando unicidad por tenant (matrícula/nombre en profesional, nombre en sillón, DNI no vacío en paciente).
- **Ampliación de repositorios SQLite y seed (`backend/src/persistence/`, `backend/seed.py`):**
  - Métodos `listar_por_tenant` con filtros (`solo_activos` para profesionales/sillones; `dni` y `nombre` parcial para pacientes) y mapeo completo de nuevos campos.
  - Enriquecimiento del `seed.py` con datos sintéticos completos.
- **Nuevos endpoints FastAPI bajo `odontologia-api-guard` (`backend/src/api/`):**
  - `POST /api/v1/profesionales`, `GET /api/v1/profesionales` (`?solo_activos=`), `GET /api/v1/profesionales/{profesional_id}`
  - `POST /api/v1/sillones`, `GET /api/v1/sillones` (`?solo_activos=`), `GET /api/v1/sillones/{sillon_id}`
  - `POST /api/v1/pacientes`, `GET /api/v1/pacientes` (`?dni=`, `?nombre=`), `GET /api/v1/pacientes/{paciente_id}`
  - Mapeo de `RecursoDuplicadoError` a `409 Conflict` (`codigo: "RECURSO_DUPLICADO"`).
- **Pruebas de integración HTTP contra SQLite real (`backend/tests/test_catalogo_api.py`):**
  - Suite completa sin mocks validando altas, consultas, filtros, duplicados `409`, aislamiento multi-tenant (`X-Tenant-ID` / `404`), validaciones `422`, migración de esquema y flujo E2E (alta de recursos + reserva de turno).

## Capabilities

### New Capabilities
- `catalogo-recursos-pacientes`: Gestión REST multi-tenant (alta, listado filtrado y consulta por ID) de Profesionales, Sillones/Boxes y Pacientes sobre SQLite real con reglas de unicidad por clínica.

### Modified Capabilities

## Impact
- **Dominio (`backend/src/domain/`):** `models.py`, `exceptions.py`, `ports.py`, `services.py`.
- **Persistencia (`backend/src/persistence/`):** `database.py` (migración idempotente), `repositories.py` (`listar_por_tenant` y mapeo de nuevos campos).
- **Seed (`backend/seed.py`):** datos sintéticos enriquecidos.
- **API (`backend/src/api/`):** `schemas.py`, `exception_handlers.py`, `dependencies.py`, `main.py` y nuevos routers `routers/profesionales.py`, `routers/sillones.py`, `routers/pacientes.py`.
- **Skill y Tests:** `.agents/skills/odontologia-api-guard/` (`http-contracts.md` y `check_api_guards.py`) y `backend/tests/test_catalogo_api.py`.
- **Documentación:** `CHANGES.md`, `CONSIGNAS_TPI.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`.
