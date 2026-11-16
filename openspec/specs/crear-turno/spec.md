# crear-turno Specification

## Purpose
Gestionar la creación de turnos odontológicos garantizando que no haya solapamientos, validando de forma simultánea e independiente la disponibilidad del profesional y del sillón/box, y permitiendo turnos contiguos en el límite exacto (intervalos semiabiertos `[inicio, fin)`).

## Requirements

### Requirement: Validación de solapamiento por profesional y por sillón
El sistema SHALL validar, antes de registrar un turno, la disponibilidad del profesional y del sillón de forma simultánea e independiente considerando únicamente turnos activos (estados PENDIENTE o CONFIRMADO) que pertenezcan al mismo tenant (`tenant_id`); SHALL rechazar la solicitud si existe superposición con otro turno activo del mismo profesional o del mismo sillón en la misma clínica; y SHALL registrar los turnos sin conflicto con estado "CONFIRMADO".

#### Scenario: Creación exitosa de turno sin conflicto (Camino Feliz)
- **Dado** que el profesional "Dr. Pérez" no tiene turnos asignados el "2026-11-01" de "10:00" a "10:30" en el tenant "Clinica Dental Norte"
- **Y** el "Sillón 1" está libre el "2026-11-01" de "10:00" a "10:30" en el tenant "Clinica Dental Norte"
- **Cuando** se solicita agendar un turno para el paciente "Paciente A" de "10:00" a "10:30" con el "Dr. Pérez" en el "Sillón 1" para "Clinica Dental Norte"
- **Entonces** el turno debe registrarse con éxito y quedar con estado "CONFIRMADO"

#### Scenario: Rechazo de turno por conflicto de agenda (Error de Negocio)
- **Dado** que el "Dr. Pérez" ya tiene un turno confirmado el "2026-11-01" de "10:00" a "10:30" en el "Sillón 1" para el tenant "Clinica Dental Norte"
- **Cuando** se intenta agendar un nuevo turno para el "Dr. Pérez" el "2026-11-01" de "10:15" a "10:45" en el "Sillón 2" para el mismo tenant
- **Entonces** el sistema debe rechazar la solicitud lanzando "SolapamientoProfesionalError"

#### Scenario: Reagendamiento exitoso en horario de turno cancelado
- **Dado** que existía un turno para el profesional "Dr. Pérez" y "Sillón 1" el "2026-11-01" de "10:00" a "10:30" en el tenant "Clinica Dental Norte" pero fue cancelado
- **Cuando** se solicita agendar un nuevo turno para el paciente "Paciente B" de "10:00" a "10:30" con el "Dr. Pérez" en el "Sillón 1" en el mismo tenant
- **Entonces** el sistema debe registrar el nuevo turno con éxito sin lanzar SolapamientoProfesionalError ni SolapamientoSillonError

#### Scenario: Turnos simultáneos en clínicas distintas no solapan
- **Dado** que el tenant "Clinica A" tiene un turno confirmado de "10:00" a "10:30"
- **Cuando** el tenant "Clinica B" solicita un turno de "10:00" a "10:30"
- **Entonces** el sistema registra el turno en "Clinica B" exitosamente sin conflicto de solapamiento

### Requirement: Turnos contiguos permitidos en el límite exacto
El sistema SHALL tratar los turnos contiguos como válidos: si la hora de inicio de un nuevo turno coincide exactamente con la hora de fin de un turno existente, esa coincidencia no constituye solapamiento y el turno SHALL registrarse sin errores.

#### Scenario: Agendamiento de turnos contiguos en el límite exacto (Caso de Borde)
- **Dado** que existe un turno registrado para el "Sillón 1" el "2026-11-01" de "10:00" a "10:30"
- **Cuando** se solicita agendar un nuevo turno para el "Sillón 1" el "2026-11-01" de "10:30" a "11:00"
- **Entonces** el sistema debe permitir la reserva exitosamente sin lanzar errores de solapamiento
