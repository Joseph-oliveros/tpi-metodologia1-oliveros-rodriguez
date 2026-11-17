# catalogo-recursos-pacientes Specification

## Purpose
Proveer endpoints HTTP REST multi-tenant en FastAPI para dar de alta, listar con filtros y consultar por ID Profesionales, Sillones/Boxes y Pacientes sobre SQLite real, manteniendo el dominio desacoplado y respetando reglas de unicidad por clínica.

## Requirements

### Requirement: Gestión REST multi-tenant de Profesionales
El sistema SHALL exponer `POST /api/v1/profesionales`, `GET /api/v1/profesionales` (filtro opcional `solo_activos`) y `GET /api/v1/profesionales/{profesional_id}` exigiendo `X-Tenant-ID`, persistiendo en SQLite real `nombre`, `matricula`, `especialidad` y `activo`, y rechazando duplicados de matrícula (cuando se informa) o nombre dentro del mismo tenant con HTTP `409`.

#### Scenario: Alta y consulta de profesional en el tenant
- **WHEN** se envía `POST /api/v1/profesionales` con `X-Tenant-ID` válido y datos sintéticos (`nombre`, `matricula`, `especialidad`)
- **THEN** el sistema responde HTTP `201` con el `id` generado y permite recuperarlo mediante `GET /api/v1/profesionales` y `GET /api/v1/profesionales/{id}` dentro del mismo tenant

#### Scenario: Rechazo de profesional duplicado en el mismo tenant
- **WHEN** se intenta registrar un profesional con igual `matricula` o igual `nombre` dentro del mismo `tenant_id`
- **THEN** el sistema responde HTTP `409` con `codigo: "RECURSO_DUPLICADO"` y `recurso: "profesional"`

### Requirement: Gestión REST multi-tenant de Sillones/Boxes
El sistema SHALL exponer `POST /api/v1/sillones`, `GET /api/v1/sillones` (filtro opcional `solo_activos`) y `GET /api/v1/sillones/{sillon_id}` exigiendo `X-Tenant-ID`, persistiendo `nombre`, `equipamiento` y `activo` en SQLite real, y rechazando sillones con nombre duplicado en el mismo tenant con HTTP `409`.

#### Scenario: Alta, filtrado por estado activo y rechazo de nombre duplicado en sillones
- **WHEN** se crean sillones activos e inactivos en un tenant y se intenta repetir el `nombre` de uno existente
- **THEN** `GET /api/v1/sillones?solo_activos=true` devuelve solo los activos del tenant y el alta duplicada responde HTTP `409` (`codigo: "RECURSO_DUPLICADO"`, `recurso: "sillon"`)

### Requirement: Gestión REST multi-tenant de Pacientes
El sistema SHALL exponer `POST /api/v1/pacientes`, `GET /api/v1/pacientes` (filtros opcionales `dni` y `nombre`) y `GET /api/v1/pacientes/{paciente_id}` exigiendo `X-Tenant-ID`, persistiendo `nombre`, `dni` y `telefono` en SQLite real, y rechazando pacientes con igual `dni` no vacío dentro del mismo tenant con HTTP `409`.

#### Scenario: Alta, filtrado por DNI/nombre y rechazo de DNI duplicado en el mismo tenant
- **WHEN** se registra un paciente sintético con `dni` y `telefono` y luego se consulta por `?dni=` o `?nombre=`, o se intenta crear otro paciente con el mismo `dni` en el mismo tenant
- **THEN** las consultas filtradas devuelven HTTP `200` con el paciente coincidente y el alta con `dni` repetido responde HTTP `409` (`codigo: "RECURSO_DUPLICADO"`, `recurso: "paciente"`)

### Requirement: Aislamiento estricto por tenant, migración segura e integración con turnos
El sistema SHALL aislar completamente todos los listados, consultas por ID y reglas de unicidad por `X-Tenant-ID` (respondiendo `404` ante accesos cross-tenant), SHALL migrar de forma idempotente tablas SQLite previas conservando registros existentes, y SHALL permitir usar inmediatamente los IDs creados para reservar turnos vía `POST /api/v1/turnos`.

#### Scenario: Flujo integrado desde alta de catálogo hasta reserva de turno
- **WHEN** una clínica da de alta un profesional, un sillón y un paciente por sus endpoints `/api/v1/*` y utiliza esos tres IDs en `POST /api/v1/turnos`
- **THEN** la reserva se crea con HTTP `201`, mientras que otro tenant puede registrar entidades con los mismos datos pero recibe HTTP `404` si intenta consultar por ID los recursos del primer tenant
