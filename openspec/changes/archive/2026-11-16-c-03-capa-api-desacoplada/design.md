# Design: C-03 Capa API Desacoplada y Endpoints de Turnos

## Context
Ver `proposal.md` para la motivación.
En `C-01` y `C-02` se consolidaron las reglas de dominio (`ServicioTurnos`, `RN-01` a `RN-09`) y la persistencia SQLite multi-tenant (`RepositorioTurnos`, `RepositorioProfesionales`, `RepositorioSillones`, `RepositorioPacientes`). Sin embargo:
1. `backend/src/domain/services.py` todavía importaba `get_connection`, `init_db` y `RepositorioTurnos` desde `src.persistence`, violando la regla de dependencia hacia adentro (`architecture.md` §2-§3).
2. No existía capa HTTP ni servidor FastAPI con Swagger UI para ejecutar y demostrar las operaciones contra persistencia real.
3. Conforme a la guía de adaptación del roadmap (`documento-tpi.pdf` pág. 2) y la coordinación del equipo, se decidió adelantar en `C-03` los endpoints operativos de turnos (`/api/v1/turnos`) junto a `/api/health`, y luego ejecutar `C-04` (Opción A: catálogo CRUD de profesionales, sillones y pacientes) antes de `C-05-auth` (JWT/RBAC).

## Goals / Non-Goals

**Goals:**
- Dejar `backend/src/domain/` 100% libre de imports de infraestructura, SQLite y HTTP mediante un puerto explícito (`RepositorioTurnosPort`).
- Exponer una API REST con FastAPI y Swagger UI (`/docs`) desacoplada en capas (`api -> domain -> ports <- persistence <- infrastructure`).
- Garantizar la resolución de `tenant_id` vía header `X-Tenant-ID` en todas las operaciones de turnos sin contaminar el payload JSON del recurso.
- Traducir de forma uniforme las excepciones de dominio a respuestas HTTP estructuradas (`409`, `404`, `422`).
- Aplicar y verificar la skill propia `.agents/skills/odontologia-api-guard/` en toda la capa API y su suite de pruebas contra SQLite real sin mocks.

**Non-Goals:**
- Autenticación JWT, login o permisos RBAC por rol (diferidos a `C-05-auth`).
- Endpoints CRUD de alta/listado de Profesionales, Sillones y Pacientes (planificados para `C-04` Opción A).
- Reprogramación de turnos (`C-08`), bloqueo por mantenimiento (`C-10`) y frontend web (`C-11`, `C-12`).

## Decisions

### 1. Resolución de `DP-01`: Python 3.11+ + FastAPI + Pydantic v2 + Uvicorn
Se adopta **FastAPI** como framework HTTP del backend (descartando Node.js).
- *Motivo:* reutilización directa del dominio Python (`ServicioTurnos`), tipado estático con `Annotated`, validación automática con Pydantic v2 y generación nativa de OpenAPI/Swagger UI (`/docs`) para demostración y pruebas.
- *Alternativa descartada:* Node.js/Express (duplicaría el núcleo de negocio o requeriría IPC).

### 2. Desacople estricto del dominio mediante `RepositorioTurnosPort` (`Protocol`)
Se crea `backend/src/domain/ports.py` con el protocolo `RepositorioTurnosPort` (métodos `guardar`, `actualizar`, `obtener_por_id`, `buscar_activos_por_fecha`, `listar_por_tenant`).
- `ServicioTurnos` recibe `repositorio_turnos: RepositorioTurnosPort | None = None`.
- Cuando se omite en pruebas unitarias puras (`test_turnos.py`), usa `RepositorioTurnosEnMemoria` (implementación Python pura en `ports.py`, sin `sqlite3`).
- En la API y pruebas de integración (`test_persistencia.py`, `test_api.py`), siempre se inyecta `RepositorioTurnos` respaldado por SQLite real (`D-04`).
- *Trade-off:* preserva retrocompatibilidad con los 21 tests unitarios preexistentes mientras asegura 0 imports externos en `src/domain/`.

### 3. Adaptación de alcance (`C-03` adelanta endpoints de turnos de `C-05`)
En `CHANGES.md` original, `C-03` solo contemplaba `GET /api/health`. Se amplía `C-03` para incluir:
- `GET /api/health`
- `POST /api/v1/turnos`
- `GET /api/v1/turnos` (filtros opcionales `fecha`, `profesional_id`, `sillon_id`)
- `PATCH /api/v1/turnos/{turno_id}/estado` (`confirmar`, `cancelar`, `completar`)
- *Motivo:* permite validar en Swagger UI el ciclo completo de negocio (doble candado, contiguos, liberación por cancelación, aislamiento por tenant) y servir de base directa para `C-04` (Opción A).

### 4. Tenancy temporal por Header `X-Tenant-ID`
- En `C-03` (previo a `C-05-auth`), toda operación bajo `/api/v1/turnos` exige el header HTTP `X-Tenant-ID` mediante la dependencia FastAPI `obtener_tenant_id` (`Annotated[str, Header(alias="X-Tenant-ID")]`), rechazando valores vacíos o compuestos solo por espacios (`422`).
- El cuerpo JSON de `POST /api/v1/turnos` no incluye `tenant_id`, respetando `knowledge-base/features.md` §5.1.
- *Migración futura:* al implementar JWT en `C-05-auth`, solo se reemplaza la función `obtener_tenant_id` para extraer `tenant_id` del token sin cambiar routers ni servicios.

### 5. Resolución por ID (`paciente_id`, `profesional_id`, `sillon_id`) y consistencia con `C-02`
- `POST /api/v1/turnos` recibe `paciente_id`, `profesional_id`, `sillon_id`, `fecha`, `hora_inicio`, `hora_fin`.
- Antes de invocar `ServicioTurnos.agendar_turno(...)`, el endpoint verifica mediante `RepositorioPacientes`, `RepositorioProfesionales` y `RepositorioSillones` que las tres entidades existan **dentro del `tenant_id` del header**. Si alguna no existe o pertenece a otro tenant, responde **`404 Not Found`** (`codigo: "RECURSO_NO_ENCONTRADO"`).
- Para mantener trazabilidad completa en la respuesta JSON (`TurnoResponse`), se añade `paciente_id: str = field(default="", compare=False)` en `Turno` (`models.py`) sin alterar las comparaciones de dataclasses en `test_turnos.py`.
- En `RepositorioTurnos.guardar()`, si `turno.profesional.id`, `turno.sillon.id` o `turno.paciente_id` ya existen en el mismo `tenant_id`, se vinculan esos registros exactos; en caso contrario se mantiene `obtener_o_crear` para preservar compatibilidad con `C-02`.
- En `ServicioTurnos.agendar_turno()`, la comprobación de conflicto verifica coincidencia por `id` o por `nombre` para ambos recursos (`profesional` y `sillon`), garantizando consistencia tanto con entidades persistidas por ID como con value-objects instanciados por nombre en tests unitarios.

### 6. Validación de intervalo y formato en frontera HTTP (`RP-01` parcial)
Los esquemas Pydantic v2 validan:
- `fecha`: formato estricto `YYYY-MM-DD` (tipo `datetime.date` serializado como `YYYY-MM-DD` hacia dominio).
- `hora_inicio` y `hora_fin`: formato estricto `HH:MM` (`00:00`–`23:59`).
- Invariante de intervalo: `hora_fin > hora_inicio` (de lo contrario Pydantic devuelve `422 Unprocessable Entity`).

### 7. Contrato explícito de errores de dominio a HTTP (`features.md` §5.2)
Se registran handlers globales en `backend/src/api/exception_handlers.py`:
- `SolapamientoProfesionalError` $\to$ `409 Conflict` (`{"detail": "...", "codigo": "SOLAPAMIENTO_PROFESIONAL", "recurso": "profesional"}`)
- `SolapamientoSillonError` $\to$ `409 Conflict` (`{"detail": "...", "codigo": "SOLAPAMIENTO_SILLON", "recurso": "sillon"}`)
- `TransicionInvalidaError` $\to$ `409 Conflict` (`{"detail": "...", "codigo": "TRANSICION_INVALIDA", "recurso": null}`)
- `RecursoNoEncontradoError` $\to$ `404 Not Found` (`{"detail": "...", "codigo": "RECURSO_NO_ENCONTRADO", "recurso": "..."}`)

### 8. Infraestructura, configuración y manejo de conexión SQLite en FastAPI
- `backend/src/infrastructure/config.py` resuelve `DATABASE_URL` desde `.env` / variables de entorno (por defecto `sqlite:///./turnos_odontologia.db`, soportando `sqlite:///...` y `:memory:`).
- `create_app(database_path: str | None = None)` inicializa la BD al crear la app y provee una conexión SQLite por petición mediante `yield` dependency (`try ... finally: conn.close()`), con handlers `def` síncronos para ejecutarse de forma segura en el threadpool de FastAPI sin conflictos de hilos de `sqlite3`.
- Se configura CORS básico abierto configurable por entorno solo si se requiere y la aplicación queda lista para `uvicorn src.api.main:app --reload`.

### 9. Skill propia `odontologia-api-guard`
- Creada en `.agents/skills/odontologia-api-guard/SKILL.md` (ubicación estándar de Antigravity no ignorada por `.gitignore`, a diferencia de `.gemini/`), con `references/http-contracts.md` y script ejecutable `scripts/check_api_guards.py` que valida automáticamente por AST pureza del dominio, desacople de API y ausencia de mocks de BD.

## Risks / Trade-offs
- **[Riesgo]** En `C-03` todavía no existen endpoints HTTP para crear nuevos profesionales/sillones/pacientes antes de `C-04` (Opción A).  
  $\to$ *Mitigación:* `backend/seed.py` ya genera `demo-tenant` con `prof-1`, `prof-2`, `sil-1`, `sil-2`, `pac-1`, lo que permite operar Swagger UI de inmediato tras correr `python seed.py`; en `C-04` se agregan los endpoints CRUD de catálogo.
- **[Riesgo]** Concurrencia de `sqlite3` bajo múltiples requests simultáneos en threadpool.  
  $\to$ *Mitigación:* conexión dedicada por request con `timeout=10.0` y cierre garantizado en `finally`.
