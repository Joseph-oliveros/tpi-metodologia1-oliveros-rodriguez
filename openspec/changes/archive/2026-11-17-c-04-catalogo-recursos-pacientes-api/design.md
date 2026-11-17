# Design: C-04 Catálogo API Multi-Tenant de Profesionales, Sillones y Pacientes

## Context
Ver `proposal.md` para la motivación.
A partir de `C-03` la API REST cuenta con FastAPI, Swagger UI, resolución de tenant por header `X-Tenant-ID` y la skill `odontologia-api-guard`. Este change implementa la **Opción A** acordada en el roadmap adaptado para permitir crear y consultar Profesionales, Sillones y Pacientes por HTTP antes de crear turnos.

## Goals / Non-Goals

**Goals:**
- Exponer alta (`POST`), listado filtrado (`GET`) y consulta individual (`GET /{id}`) para Profesionales, Sillones y Pacientes bajo `X-Tenant-ID`.
- Mantener la arquitectura desacoplada exigida por `odontologia-api-guard`: routers delgados sin SQL ni reglas de negocio; unicidad validada en dominio (`ServicioCatalogo`) mediante puertos (`Protocol`).
- Incorporar los campos de `data-models.md` (`matricula`, `especialidad`, `equipamiento`, `telefono`) preservando retrocompatibilidad con las pruebas y la BD ya sembrada de `C-02`/`C-03`.
- Demostrar el flujo completo en Swagger y en tests de integración reales: crear recursos sintéticos $\to$ usarlos en `POST /api/v1/turnos`.

**Non-Goals:**
- Autenticación JWT y autorización RBAC por rol (`Administrador`, `Recepcionista`, `Profesional`), reservadas para `C-05-auth`.
- Edición (`PUT`/`PATCH`) o inactivación/baja lógica con impacto sobre turnos ya agendados (`PA-16`, `RP-07`), reservadas para `C-09` y `C-10`.
- Configuración de horarios de atención por profesional/sillón (`DP-08`).

## Decisions

### 1. Alcance acotado a `POST` + `GET` (listado y por ID)
Se limita `C-04` a creación, listado con filtros y obtención por ID (`POST` / `GET`), dejando `PUT`/`PATCH` de recursos e inactivación para `C-09` / `C-10`.
- *Motivo:* habilita el flujo completo en Swagger sin abrir las preguntas pendientes `PA-16` y `RP-07` sobre turnos futuros de recursos dados de baja.

### 2. Extensión retrocompatible de modelos + migración idempotente en SQLite
- `Profesional`: agrega `matricula: str = ""` y `especialidad: str = ""`.
- `Sillon`: agrega `equipamiento: str = ""`.
- `Paciente`: agrega `telefono: str = ""`.
- `init_db` ejecuta `_migrar_columnas_faltantes(conn)` consultando `PRAGMA table_info(...)` para agregar columnas con `ALTER TABLE ... ADD COLUMN ... TEXT NOT NULL DEFAULT ''` si la BD provenía de `C-02`/`C-03`.
- *Alternativa descartada:* recrear la base borrando el archivo `.db` (rompería instalaciones existentes).

### 3. Reglas de unicidad por tenant en dominio (`RecursoDuplicadoError` $\to$ `409`)
En `ServicioCatalogo` (capa `domain/services.py`):
- **Profesional:** dentro del mismo `tenant_id`, no se admite otro profesional con igual `matricula` (no vacía, comparación insensible a mayúsculas y espacios) ni con igual `nombre`.
- **Sillón:** dentro del mismo `tenant_id`, no se admite otro sillón con igual `nombre`.
- **Paciente:** dentro del mismo `tenant_id`, si se informa `dni` no vacío, no se admite otro paciente con igual `dni`.
- En **tenants distintos**, los mismos nombres, matrículas y DNIs están permitidos (`RN-05`).
- `RecursoDuplicadoError` se mapea centralizadamente en `exception_handlers.py` a `409 Conflict` (`codigo: "RECURSO_DUPLICADO"`).

### 4. Desacople mediante puertos de catálogo y servicio de dominio
Se añaden `RepositorioProfesionalesPort`, `RepositorioSillonesPort` y `RepositorioPacientesPort` en `src/domain/ports.py` y `ServicioCatalogo` en `src/domain/services.py`.
- Las rutas de `src/api/routers/{profesionales,sillones,pacientes}.py` reciben `ServicioCatalogoDep` vía `Annotated[..., Depends(...)]` y no importan `sqlite3` ni implementan validaciones de unicidad en la capa HTTP.

### 5. Filtros de consulta ergonómicos y aislados por tenant
- `GET /api/v1/profesionales?solo_activos=true|false` y `GET /api/v1/sillones?solo_activos=true|false`.
- `GET /api/v1/pacientes?dni=...&nombre=...` (`dni` coincidencia exacta tras `strip()`; `nombre` coincidencia parcial insensible a mayúsculas/minúsculas).
- Todo `GET /{id}` verifica `tenant_id` y devuelve `404` (`RECURSO_NO_ENCONTRADO`) si el registro no existe o pertenece a otro tenant.

## Risks / Trade-offs
- **[Riesgo]** Bases de datos `turnos_odontologia.db` creadas en `C-02`/`C-03` carecen de las nuevas columnas.  
  $\to$ *Mitigación:* migración automática e idempotente en `init_db`, verificada con test explícito sobre esquema legacy.
- **[Riesgo]** El verificador estático `check_api_guards.py` solo inspeccionaba `test_api.py` en busca de mocks prohibidos.  
  $\to$ *Mitigación:* ampliar `check_api_guards.py` para auditar todos los `test_*.py` de `backend/tests/`.
