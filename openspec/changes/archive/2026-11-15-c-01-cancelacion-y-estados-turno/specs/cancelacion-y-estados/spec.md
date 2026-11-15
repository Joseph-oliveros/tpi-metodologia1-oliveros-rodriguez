# Spec Delta

## Purpose
Gestionar el ciclo de vida y las transiciones de estado de los turnos odontológicos, asegurando la integridad de la máquina de estados y la liberación inmediata de recursos ante cancelaciones.

## ADDED Requirements

### Requirement: Máquina de estados y transiciones permitidas
El sistema SHALL gestionar las transiciones de estado de los turnos (`PENDIENTE`, `CONFIRMADO`, `CANCELADO`, `COMPLETADO`) según las reglas de negocio, permitiendo confirmar (`PENDIENTE` a `CONFIRMADO`), cancelar (`PENDIENTE` o `CONFIRMADO` a `CANCELADO`) y completar (`CONFIRMADO` a `COMPLETADO`), y SHALL rechazar con `TransicionInvalidaError` cualquier transición no autorizada o intento de modificar estados finales.

#### Scenario: Confirmación exitosa de un turno pendiente
- **WHEN** se solicita confirmar un turno que se encuentra en estado "PENDIENTE"
- **THEN** el sistema actualiza el estado del turno a "CONFIRMADO" manteniendo los recursos reservados

#### Scenario: Cancelación exitosa de un turno confirmado o pendiente
- **WHEN** se solicita cancelar un turno que se encuentra en estado "CONFIRMADO" o "PENDIENTE"
- **THEN** el sistema actualiza el estado del turno a "CANCELADO"

#### Scenario: Finalización exitosa de un turno confirmado
- **WHEN** se solicita completar un turno que se encuentra en estado "CONFIRMADO"
- **THEN** el sistema actualiza el estado del turno a "COMPLETADO"

#### Scenario: Rechazo de transición inválida
- **WHEN** se solicita realizar una transición no permitida (por ejemplo, completar un turno en estado "PENDIENTE", o modificar un turno ya "CANCELADO" o "COMPLETADO")
- **THEN** el sistema rechaza la operación lanzando "TransicionInvalidaError" y mantiene el estado previo del turno

### Requirement: Liberación inmediata de recursos por cancelación
El sistema SHALL excluir de las validaciones de solapamiento a los turnos en estado `CANCELADO` o `COMPLETADO`, liberando de inmediato la disponibilidad del profesional y del sillón para el intervalo horario correspondiente.

#### Scenario: Liberación de recursos tras cancelar turno
- **WHEN** un turno confirmado es cancelado
- **THEN** tanto el profesional como el sillón quedan disponibles inmediatamente para agendar nuevos turnos en ese mismo intervalo
