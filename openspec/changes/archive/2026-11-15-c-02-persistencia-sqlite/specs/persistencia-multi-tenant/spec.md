# Spec Delta

## Purpose
Proveer almacenamiento relacional persistente para entidades odontológicas en SQLite garantizando aislamiento estricto por tenant en todas las consultas y mutaciones de datos.

## ADDED Requirements

### Requirement: Aislamiento estricto de datos por tenant
El sistema SHALL requerir un `tenant_id` en todas las consultas y operaciones de persistencia, asegurando que los registros de una clínica no sean visibles, modificables ni generen conflictos de disponibilidad con los de otra clínica.

#### Scenario: Turnos idénticos en horarios simultáneos para clínicas diferentes
- **WHEN** dos clínicas distintas ("Tenant A" y "Tenant B") registran un turno en el mismo intervalo horario ("2026-11-01" de "10:00" a "10:30")
- **THEN** ambas operaciones se registran con éxito en la base de datos sin generar errores de solapamiento

#### Scenario: Filtrado de turnos exclusivos del tenant
- **WHEN** una clínica consulta su listado de turnos registrados
- **THEN** el sistema devuelve únicamente los turnos asociados al `tenant_id` de esa clínica

### Requirement: Persistencia relacional de turnos y recursos en SQLite
El sistema SHALL persistir entidades de dominio (turnos, profesionales, sillones, pacientes y tenants) en SQLite respetando tipos de datos, claves primarias y claves foráneas, sin utilizar simulaciones en memoria ni mocks.

#### Scenario: Persistencia y recuperación íntegra de un turno
- **WHEN** se guarda un turno odontológico en SQLite y se vuelve a consultar mediante el repositorio
- **THEN** los atributos de fecha, hora, estado, paciente, profesional, sillón y tenant coinciden con los guardados

#### Scenario: Persistencia de transiciones de estado
- **WHEN** se cancela o completa un turno persistido
- **THEN** la base de datos SQLite refleja el nuevo estado del turno de forma consistente y duradera
