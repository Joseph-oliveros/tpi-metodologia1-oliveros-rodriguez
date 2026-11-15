# Design: C-01 Cancelación y Estados de Turno

## Context
Ver `proposal.md` para la motivación general del cambio.
El sistema actual cuenta con un servicio de dominio puro en memoria (`ServicioTurnos`) y modelos inmutables (`dataclass(frozen=True)`). Hasta ahora, todo turno se registra directamente con estado `"CONFIRMADO"` y la validación de solapamiento verifica todos los turnos almacenados en la lista `_turnos`, sin distinguir si un turno fue cancelado o si está activo.

## Goals / Non-Goals

**Goals:**
- Implementar la máquina de estados de turnos con los estados `PENDIENTE`, `CONFIRMADO`, `CANCELADO` y `COMPLETADO` (`RN-03`).
- Proveer métodos explícitos en `ServicioTurnos` (`confirmar`, `cancelar`, `completar`) que validen las transiciones según la matriz permitida.
- Lanzar la excepción de dominio `TransicionInvalidaError` ante transiciones inválidas o intentos de alterar estados terminales.
- Modificar el filtro de solapamiento en `agendar_turno()` para considerar únicamente turnos en estado activo (`PENDIENTE`, `CONFIRMADO`), permitiendo el re-agendamiento inmediato ante cancelaciones (`RN-04`).
- Mantener la compatibilidad regresiva con la suite de pruebas existente (8 tests verdes).

**Non-Goals:**
- Persistencia en base de datos SQLite (reservado para `C-02`).
- Exposición de endpoints HTTP o controllers FastAPI (reservado para `C-03`).
- Reprogramación automática de turnos (reservado para `C-08`).
- Modificar el estado inicial de creación a `PENDIENTE` (se mantiene `"CONFIRMADO"` para respetar el comportamiento vigente y la pregunta abierta `PA-13`).

## Decisions

### 1. Representación de Estados y Matriz de Transiciones
Se definen constantes y/o clase de constantes de tipo string en `models.py`:
- `ESTADO_PENDIENTE = "PENDIENTE"`
- `ESTADO_CONFIRMADO = "CONFIRMADO"`
- `ESTADO_CANCELADO = "CANCELADO"`
- `ESTADO_COMPLETADO = "COMPLETADO"`
- `ESTADOS_ACTIVOS = {ESTADO_PENDIENTE, ESTADO_CONFIRMADO}`
- `ESTADOS_FINALES = {ESTADO_CANCELADO, ESTADO_COMPLETADO}`

Matriz de transiciones:
- `PENDIENTE` $\to$ `{CONFIRMADO, CANCELADO}`
- `CONFIRMADO` $\to$ `{COMPLETADO, CANCELADO}`
- `CANCELADO` $\to$ `{}` (terminal)
- `COMPLETADO` $\to$ `{}` (terminal)

*Alternativa considerada:* Usar `enum.Enum`. Se opta por constantes string o StrEnum para mantener total compatibilidad hacia atrás con el campo `estado: str = "CONFIRMADO"` en `Turno` y las aserciones existentes en los tests.

### 2. Manejo de Inmutabilidad y Actualización de Estado en `ServicioTurnos`
Dado que `Turno` está definido como `@dataclass(frozen=True)`, no se debe mutar el atributo directamente:
- Para realizar una transición, `ServicioTurnos` utiliza `dataclasses.replace(turno, estado=nuevo_estado)` (o recrea la instancia).
- El servicio actualiza su lista interna de turnos reemplazando la referencia previa y retorna la nueva instancia del turno con el estado actualizado.

*Alternativa considerada:* Hacer `Turno` mutable removiendo `frozen=True`. Se descarta para preservar el principio de inmutabilidad de los objetos de valor y evitar efectos colaterales fuera del servicio de dominio.

### 3. Excepción de Dominio Explícita
Se agrega `TransicionInvalidaError` en `backend/src/domain/exceptions.py`, heredando directamente de `Exception`, siguiendo el patrón de `SolapamientoProfesionalError` y `SolapamientoSillonError`.

### 4. Filtrado en Detección de Solapamiento
En `ServicioTurnos.agendar_turno()`, dentro del bucle de validación, se evalúa:
```python
if turno_existente.estado not in ESTADOS_ACTIVOS:
    continue
```
Esto asegura que un turno en `CANCELADO` o `COMPLETADO` sea ignorado en la comprobación de intervalos, liberando tanto el profesional como el sillón.

## Risks / Trade-offs

- **[Riesgo]** Romper aserciones en tests existentes si se alterara la firma de `Turno` o el estado inicial.  
  $\to$ *Mitigación:* Se conserva el valor por defecto `estado: str = "CONFIRMADO"` en `Turno` y la firma de `agendar_turno()` inalterada.
- **[Riesgo]** Identificación del turno a modificar en memoria sin un identificador único `id`.  
  $\to$ *Mitigación:* Se pasan las instancias de `Turno` a los métodos `confirmar(turno)`, `cancelar(turno)`, `completar(turno)` y se localizan por igualdad en la colección de `ServicioTurnos._turnos`. En `C-02` se incorporará persistencia formal con IDs/UUIDs.
