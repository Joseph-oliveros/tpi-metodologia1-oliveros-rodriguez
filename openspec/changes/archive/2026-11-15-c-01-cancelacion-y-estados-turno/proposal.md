# Proposal: C-01 Cancelación y Estados de Turno

## Why
Actualmente el sistema solo permite crear turnos en estado inicial "CONFIRMADO" y no provee mecanismos para cancelar, confirmar o completar turnos. Esto impide liberar recursos ocupados (profesional y sillón) cuando un paciente cancela su turno, bloqueando turnos futuros innecesariamente y limitando el ciclo de vida operativo del consultorio.

## What Changes
- Incorporación de estados canónicos del turno: `PENDIENTE`, `CONFIRMADO`, `CANCELADO` y `COMPLETADO` (`RN-03`).
- Definición de la matriz de transiciones válidas y la nueva excepción de negocio `TransicionInvalidaError`.
- Métodos de transición en `ServicioTurnos`: `confirmar()`, `cancelar()` y `completar()`.
- Actualización de la regla de detección de solapamiento para considerar únicamente turnos en estado activo (`PENDIENTE`, `CONFIRMADO`); los turnos `CANCELADOS` y `COMPLETADOS` liberan inmediatamente profesional y sillón (`RN-04`).
- Se mantiene el alta directa con estado inicial `CONFIRMADO` (cumpliendo la especificación vigente y dejando abierta la discusión de `PA-13`).

## Capabilities

### New Capabilities
- `cancelacion-y-estados`: Gestión del ciclo de vida y transiciones de estado de los turnos odontológicos, asegurando la integridad de la máquina de estados y la liberación inmediata de recursos ante cancelaciones.

### Modified Capabilities
- `crear-turno`: Actualización de la validación de disponibilidad para considerar únicamente turnos en estado activo (`PENDIENTE` o `CONFIRMADO`), permitiendo reagendar en horarios previamente cancelados.

## Impact
- **Dominio (`backend/src/domain/`):**
  - `exceptions.py`: nueva excepción `TransicionInvalidaError`.
  - `models.py`: constantes/enum de estados de turno y matriz de transiciones permitidas.
  - `services.py`: nuevos métodos de ciclo de vida (`confirmar`, `cancelar`, `completar`) y filtro por estado activo en `agendar_turno()`.
- **Pruebas (`backend/tests/`):**
  - `test_turnos.py`: nuevos tests para transiciones válidas, transiciones inválidas y verificación de liberación de profesional y sillón.
