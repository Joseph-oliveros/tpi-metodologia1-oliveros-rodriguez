# Design: C-02 Persistencia en SQLite y Multi-tenancy

## Context
Ver `proposal.md` para la motivación.
En el change anterior (`C-01`), `ServicioTurnos` operaba con una colección interna `_turnos: list[Turno]` en memoria. No existía soporte para `tenant_id`, perdiendo el aislamiento de clínicas requerido por la arquitectura multi-tenant (`RN-05`, `D-01`).

## Goals / Non-Goals

**Goals:**
- Implementar el esquema relacional en SQLite (`D-04`) con claves foráneas e integridad referencial para `tenants`, `profesionales`, `sillones`, `pacientes` y `turnos`.
- Implementar clases de repositorio (`RepositorioTurnos`, `RepositorioProfesionales`, `RepositorioSillones`, `RepositorioPacientes`) que exijan `tenant_id` en todas sus operaciones de lectura y escritura (`RN-05`).
- Refactorizar `ServicioTurnos` para desacoplarlo mediante inyección de dependencias (`repositorio_turnos: RepositorioTurnos`), permitiendo persistencia duradera.
- Mantener compatibilidad hacia atrás: permitir `ServicioTurnos()` sin parámetros instanciando un repositorio SQLite en memoria (`:memory:`) por defecto.
- Ejecutar todas las pruebas contra SQLite real (sin mocks de base de datos, regla 5 de `AGENTS.md`).

**Non-Goals:**
- Exposición de endpoints HTTP / API REST con FastAPI (reservado para `C-03`).
- Autenticación JWT / RBAC de usuarios del sistema (reservado para `C-04`).
- ORM de producción pesado o migraciones Alembic (reservado para etapas posteriores `DP-02`).

## Decisions

### 1. Motor de Persistencia y DDL Relacional (SQLite)
Se crea un módulo `backend/src/persistence/database.py` que provee:
- Conexión configurada con `PRAGMA foreign_keys = ON;`.
- Creación del schema DDL relacional con tablas:
  - `tenants (id TEXT PRIMARY KEY, nombre TEXT NOT NULL)`
  - `profesionales (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), nombre TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1)`
  - `sillones (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), nombre TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1)`
  - `pacientes (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), nombre TEXT NOT NULL, dni TEXT)`
  - `turnos (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id), paciente_id TEXT NOT NULL, profesional_id TEXT NOT NULL, sillon_id TEXT NOT NULL, fecha TEXT NOT NULL, hora_inicio TEXT NOT NULL, hora_fin TEXT NOT NULL, estado TEXT NOT NULL)`

*Alternativa considerada:* Usar SQLAlchemy completo desde ahora. Se prefiere SQLite nativo con Repositorios explícitos para mantener el MVP liviano y desacoplado, facilitando la futura migración a PostgreSQL o SQLAlchemy sin alterar el dominio (`DP-02`).

### 2. Contrato de Repositorios y Filtrado Obligatorio por Tenant
Se crea `backend/src/persistence/repositories.py`:
- `RepositorioTurnos`:
  - `guardar(turno: Turno) -> Turno`
  - `actualizar(turno: Turno) -> Turno`
  - `obtener_por_id(tenant_id: str, turno_id: str) -> Turno | None`
  - `buscar_activos_por_fecha(tenant_id: str, fecha: str) -> list[Turno]`
  - `listar_por_tenant(tenant_id: str) -> list[Turno]`
Todas las consultas SQL parametrizan `tenant_id` (`WHERE tenant_id = ?`), impidiendo fugas de datos o solapamientos entre consultorios distintos.

### 3. Desacople e Inyección de Dependencias en `ServicioTurnos`
`ServicioTurnos` delega la persistencia y lectura de turnos al `RepositorioTurnos`:
- En `agendar_turno()` consulta los turnos activos en esa fecha mediante `self._repo.buscar_activos_por_fecha(tenant_id, fecha)` y aplica la doble validación de solapamiento en intervalos semiabiertos `[inicio, fin)`.
- Si no hay colisión, persiste el nuevo turno con `self._repo.guardar(turno)` y lo retorna.
- Métodos `confirmar()`, `cancelar()`, `completar()` actualizan el estado en base de datos mediante `self._repo.actualizar(turno_actualizado)`.
- Para preservar el contrato de la suite previa de 20 tests, si no se suministra un repositorio, `ServicioTurnos` inicializa automáticamente una base SQLite en memoria (`:memory:`).

### 4. Identificadores y Multi-tenancy en Entidades
Las entidades de dominio reciben `tenant_id: str = "tenant-default"` e `id: str = ""` (autogenerado con UUID si está vacío) para asegurar compatibilidad retroactiva con llamadas posicionales y garantizar persistencia consistente.

## Risks / Trade-offs

- **[Riesgo]** Romper la suite de 20 pruebas preexistentes al introducir la capa de persistencia.  
  $\to$ *Mitigación:* Se provee valor predeterminado para `tenant_id` y repositorio `:memory:` automático en `ServicioTurnos`, preservando los tests existentes mientras se incorporan los nuevos tests de persistencia y multi-tenant.
- **[Riesgo]** Inconsistencias de concurrencia bajo escrituras simultáneas en SQLite.  
  $\to$ *Mitigación:* Transacciones atómicas de SQLite con modo WAL o transacciones de conexión única para tests.
