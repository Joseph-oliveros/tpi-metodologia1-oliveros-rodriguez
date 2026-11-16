# capa-api-desacoplada Specification

## Purpose
Exponer una capa de presentación HTTP REST con FastAPI y Swagger UI desacoplada del dominio y la persistencia, que traduzca errores de negocio a códigos HTTP estándar, resuelva el contexto multi-tenant y permita operar turnos sobre SQLite real.

## Requirements

### Requirement: Desacople arquitectónico entre API, dominio e infraestructura
La capa de dominio (`src/domain/`) SHALL permanecer independiente de HTTP, FastAPI, Pydantic y detalles de SQLite mediante un puerto explícito (`RepositorioTurnosPort`), mientras que la capa API (`src/api/`) SHALL delegar todas las reglas de solapamiento y transiciones de estado en `ServicioTurnos` sin duplicar lógica de negocio ni acceder directamente a SQL.

#### Scenario: Verificación de pureza de dependencias del dominio y desacople de la API
- **WHEN** se inspeccionan los módulos de `backend/src/domain/` y `backend/src/api/` mediante el verificador de `odontologia-api-guard`
- **THEN** `backend/src/domain/` no importa módulos de FastAPI, Pydantic, `sqlite3` ni `src.persistence` / `src.api`, y `backend/src/api/` no importa `sqlite3` ni implementa lógica de solapamiento

### Requirement: Health check y documentación interactiva OpenAPI/Swagger
El sistema SHALL exponer el endpoint `GET /api/health` y habilitar la documentación interactiva OpenAPI/Swagger UI en `/docs` (y esquema en `/openapi.json`), obteniendo la configuración de base de datos desde variables de entorno sin credenciales embebidas.

#### Scenario: Consulta de estado de salud del servicio y acceso a Swagger
- **WHEN** se envía una solicitud `GET /api/health` y `GET /docs` a la aplicación FastAPI
- **THEN** ambos responden con código HTTP `200`, y `/api/health` retorna el estado operativo `"ok"`

### Requirement: Registro de turno vía API REST con doble validación y aislamiento por tenant
El sistema SHALL exponer `POST /api/v1/turnos` exigiendo el header `X-Tenant-ID`, validando el formato y coherencia temporal (`hora_fin > hora_inicio`), verificando la existencia de `paciente_id`, `profesional_id` y `sillon_id` dentro del tenant solicitante, y delegando a `ServicioTurnos` la doble validación simultánea e independiente sobre SQLite real.

#### Scenario: Creación exitosa de turno vía HTTP
- **WHEN** se envía `POST /api/v1/turnos` con `X-Tenant-ID` válido y recursos existentes y disponibles en el intervalo `[hora_inicio, hora_fin)`
- **THEN** el sistema persiste el turno en SQLite y responde con HTTP `201`, estado `"CONFIRMADO"` e identificadores asociados

#### Scenario: Turnos contiguos aceptados vía HTTP
- **WHEN** existe un turno activo de `"10:00"` a `"10:30"` y se envía `POST /api/v1/turnos` de `"10:30"` a `"11:00"` para el mismo profesional y sillón en el mismo tenant
- **THEN** el sistema registra el nuevo turno y responde con HTTP `201`

#### Scenario: Rechazo con HTTP 409 por conflicto de profesional, sillón o precedencia
- **WHEN** se envía `POST /api/v1/turnos` en un horario solapado con un turno activo del mismo profesional, del mismo sillón o de ambos en el mismo tenant
- **THEN** el sistema responde con HTTP `409` indicando `codigo: "SOLAPAMIENTO_PROFESIONAL"` (incluso si ambos recursos colisionan, por `RN-09`) o `codigo: "SOLAPAMIENTO_SILLON"` cuando solo el sillón está ocupado

#### Scenario: Rechazo con HTTP 404 cuando algún recurso no existe en el tenant
- **WHEN** se envía `POST /api/v1/turnos` referenciando un `profesional_id`, `sillon_id` o `paciente_id` inexistente o perteneciente a otro tenant
- **THEN** el sistema responde con HTTP `404` (`codigo: "RECURSO_NO_ENCONTRADO"`) y no persiste el turno

#### Scenario: Rechazo con HTTP 422 ante intervalo inválido o header tenant vacío
- **WHEN** se envía `POST /api/v1/turnos` con `hora_fin <= hora_inicio`, formato inválido o header `X-Tenant-ID` ausente o vacío
- **THEN** el sistema responde con HTTP `422`

### Requirement: Consulta filtrada y gestión de ciclo de vida de turnos vía API REST
El sistema SHALL exponer `GET /api/v1/turnos` con filtros opcionales (`fecha`, `profesional_id`, `sillon_id`) acotados al `X-Tenant-ID`, y `PATCH /api/v1/turnos/{turno_id}/estado` para ejecutar las acciones `confirmar`, `cancelar` y `completar` respetando la máquina de estados (`RN-03`) y liberando ambos recursos ante cancelaciones (`RN-04`).

#### Scenario: Aislamiento multi-tenant en consulta y filtros de turnos
- **WHEN** dos clínicas registran turnos en la misma fecha y horario usando headers `X-Tenant-ID` distintos y una de ellas consulta `GET /api/v1/turnos` con filtros opcionales
- **THEN** la respuesta HTTP `200` devuelve únicamente los turnos del tenant solicitante que coinciden con los filtros

#### Scenario: Cancelación vía PATCH libera profesional y sillón para nueva reserva
- **WHEN** se envía `PATCH /api/v1/turnos/{turno_id}/estado` con `{"accion": "cancelar"}` sobre un turno confirmado y luego se envía `POST /api/v1/turnos` en el mismo intervalo, profesional y sillón
- **THEN** la cancelación responde HTTP `200` con estado `"CANCELADO"` y la nueva reserva responde HTTP `201`

#### Scenario: Transición inválida rechazada con HTTP 409
- **WHEN** se envía `PATCH /api/v1/turnos/{turno_id}/estado` solicitando una transición no permitida por la máquina de estados (por ejemplo confirmar o completar un turno ya cancelado)
- **THEN** el sistema responde HTTP `409` con `codigo: "TRANSICION_INVALIDA"` y mantiene intacto el estado del turno en SQLite
