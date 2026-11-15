# Tasks: C-01 Cancelación y Estados de Turno

## 1. Excepciones y Modelos de Estados

- [x] 1.1 Definir la excepción `TransicionInvalidaError` en `backend/src/domain/exceptions.py` y verificar con test unitario que hereda de `Exception`.
- [x] 1.2 Definir las constantes de estado (`PENDIENTE`, `CONFIRMADO`, `CANCELADO`, `COMPLETADO`), conjuntos `ESTADOS_ACTIVOS` / `ESTADOS_FINALES` y matriz `TRANSICIONES_PERMITIDAS` en `backend/src/domain/models.py`, verificando consistencia mediante tests unitarios.

## 2. Transiciones de Estado en ServicioTurnos

- [x] 2.1 Implementar el método `confirmar(turno)` en `ServicioTurnos` para transicionar de `PENDIENTE` a `CONFIRMADO`, rechazando estados inválidos con `TransicionInvalidaError` y verificando mediante tests en `backend/tests/test_turnos.py`.
- [x] 2.2 Implementar el método `cancelar(turno)` en `ServicioTurnos` para transicionar desde `PENDIENTE` o `CONFIRMADO` a `CANCELADO`, rechazando estados finales con `TransicionInvalidaError` y verificando mediante tests en `backend/tests/test_turnos.py`.
- [x] 2.3 Implementar el método `completar(turno)` en `ServicioTurnos` para transicionar de `CONFIRMADO` a `COMPLETADO`, rechazando estados inválidos con `TransicionInvalidaError` y verificando mediante tests en `backend/tests/test_turnos.py`.

## 3. Liberación de Recursos y Verificación Integral

- [x] 3.1 Actualizar el chequeo de solapamiento en `ServicioTurnos.agendar_turno()` para filtrar únicamente turnos en `ESTADOS_ACTIVOS`, permitiendo agendar un nuevo turno en el horario de un turno cancelado o completado, y verificar mediante tests del escenario de liberación de recursos.
- [x] 3.2 Ejecutar la suite completa de tests de dominio en `backend/tests/test_turnos.py` y verificar que tanto los 8 tests preexistentes como los nuevos tests de transiciones y liberación pasen en verde.

## Workflow follow-up

- Ejecutar `/opsx:apply c-01-cancelacion-y-estados-turno` siguiendo el ciclo de TDD estricto.
- Verificar suite verde y archivar el change con `/opsx:archive c-01-cancelacion-y-estados-turno`.
