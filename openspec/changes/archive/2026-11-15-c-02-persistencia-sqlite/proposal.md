# Proposal: C-02 Persistencia en SQLite y Multi-tenancy

## Why
Hasta ahora los turnos se almacenan únicamente en una lista volátil en memoria (`ServicioTurnos._turnos`) sin soporte de base de datos relacional ni aislamiento por tenant (`RN-05`, `D-01`). Esto impide la persistencia entre sesiones de uso, expone al sistema a pérdida de datos y no refleja la arquitectura multi-tenant requerida para operar clínicas independientes.

## What Changes
- Creación de la capa de persistencia relacional con **SQLite** (`D-04`) y esquema relacional para `tenant`, `profesional`, `sillon`, `paciente` y `turno`.
- Soporte estricto de **multi-tenancy** (`RN-05`): toda consulta y operación de persistencia se parametriza y aísla por `tenant_id`. Dos clínicas pueden registrar turnos en el mismo intervalo sin conflicto.
- Implementación de repositorios de datos (`RepositorioTurnos`, `RepositorioProfesionales`, `RepositorioSillones`, `RepositorioPacientes`).
- Desacople de `ServicioTurnos` para delegar la persistencia y la consulta de solapamientos al `RepositorioTurnos` mediante inyección de dependencias.
- Suite de pruebas de persistencia contra SQLite real en memoria (`:memory:`) o archivo temporal, sin ningún tipo de mock (`D-04`, regla dura 5 de `AGENTS.md`).

## Capabilities

### New Capabilities
- `persistencia-multi-tenant`: Almacenamiento relacional de turnos y recursos en SQLite con filtrado, integridad referencial y aislamiento estricto por tenant (`RN-05`, `D-01`, `D-04`).

### Modified Capabilities
- `crear-turno`: La validación de solapamiento y la reserva de turnos se ejecutan dentro del ámbito estricto del tenant especificado (`tenant_id`), garantizando que recursos y agendas de distintas clínicas sean independientes.

## Impact
- **Persistencia (`backend/src/persistence/`):**
  - Nuevo módulo `database.py`: inicialización de tablas DDL y manejo de conexiones SQLite.
  - Nuevo módulo `repositories.py`: clases de repositorio con consultas parametrizadas (`tenant_id`).
- **Dominio (`backend/src/domain/`):**
  - `models.py`: modelos actualizados con identificadores y `tenant_id` (`Tenant`, `Paciente`, `Profesional`, `Sillon`, `Turno`).
  - `services.py`: `ServicioTurnos` recibe `RepositorioTurnos` y valida solapamientos con persistencia real.
- **Tests (`backend/tests/`):**
  - Nuevos tests de integración contra SQLite real para aislamiento multi-tenant y ciclo de vida persistido.
