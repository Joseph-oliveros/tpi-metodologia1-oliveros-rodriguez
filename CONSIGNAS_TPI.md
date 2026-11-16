# Consignas del Trabajo Práctico Integrador (TPI)

**Materia:** Metodología de Sistemas I  
**Integrantes:**
- Joseph Oliveros
- Cristian Rodríguez

---

## 1. Reglas Generales del TPI

1. **Equipo de Trabajo:**
   - Conformado por 2 integrantes: Joseph Oliveros y Cristian Rodríguez.

2. **Mínimo de Changes Requeridos:**
   - El proyecto debe contar con un **mínimo de 4 changes completos y archivados**, incluyendo el cambio fundacional del Parcial 2.

3. **Ciclo Metodológico SDD (Spec-Driven Development):**
   - Todo cambio debe seguir estrictamente el flujo:
     $$\text{Propuesto (/opsx:propose)} \longrightarrow \text{Aplicado (/opsx:apply)} \longrightarrow \text{Verificado con pytest} \longrightarrow \text{Archivado (/opsx:archive)}$$
   - **Spec First:** NUNCA modificar o escribir código de producción ni tests sin la especificación aprobada correspondiente en `openspec/changes/`.
   - **Suite Verde:** Toda tarea y change debe finalizar con la suite de pruebas completa en verde (`pytest -v`).

4. **Skill Propia:**
   - Es obligatorio el diseño e integración de al menos una **Skill personalizada** adaptada a las necesidades del proyecto.

5. **Servidor MCP:**
   - Es obligatorio el uso e integración de al menos un **servidor MCP (Model Context Protocol)** en el entorno de desarrollo del agente.

6. **Datos Ficticios y Privacidad:**
   - Política estricta de datos sintéticos: NUNCA almacenar ni procesar información real de pacientes o profesionales. Todos los fixtures, tests y ejemplos deben utilizar nombres y datos ficticios (ej. `Paciente Ficticio`, `Dr. Ejemplo`).

---

## 2. Alcance Planificado (Changes TPI)

El alcance planificado para la entrega del TPI supera el mínimo exigido de 4 changes completos y archivados:

| # | Identificador | Nombre / Descripción | Estado |
|---|---------------|----------------------|--------|
| **1** | `2026-10-15-crear-turno-sin-solapamientos` | Creación de turnos con doble validación de recursos (profesional y sillón/box) bajo intervalos semiabiertos $[inicio, fin)$ *(Base Parcial 2)*. | **Archivado** ✔ |
| **2** | `C-01` | `cancelacion-y-estados-turno`: Ciclo de vida y máquina de estados del turno (confirmar, cancelar, completar) y reglas de liberación de recursos por cancelación (`RN-03`, `RN-04`). | **Archivado** ✔ |
| **3** | `C-02` | `persistencia-sqlite`: Capa de persistencia con base de datos SQLite real para tests y desarrollo (sin mockear la BD), repositorios y mapeo de entidades de dominio. | **Archivado** ✔ |
| **4** | `C-03` | `capa-api-desacoplada`: Exposición de endpoints HTTP mediante **FastAPI** (`/api/health`, `/api/v1/turnos`) con documentación interactiva **Swagger/OpenAPI**, desacoplada del dominio puro y validada con la skill `odontologia-api-guard`. | **Archivado** ✔ |
| **5** | `C-04` | `catalogo-recursos-pacientes-api` *(Opción A)*: Endpoints CRUD multi-tenant para Profesionales, Sillones y Pacientes sobre FastAPI reutilizando los repositorios SQLite de `C-02`. | *Planificado* |

---

## 3. Matriz de Cumplimiento de Requisitos

- [x] **2 Integrantes:** Joseph Oliveros y Cristian Rodríguez.
- [x] **Mínimo 4 Changes Completos y Archivados:**
  - [x] 1. `2026-10-15-crear-turno-sin-solapamientos` (Archivado en `openspec/changes/archive/2026-10-15-crear-turno-sin-solapamientos/`)
  - [x] 2. `C-01 cancelacion-y-estados-turno` (Archivado en `openspec/changes/archive/2026-11-15-c-01-cancelacion-y-estados-turno/`)
  - [x] 3. `C-02 persistencia-sqlite` (Archivado en `openspec/changes/archive/2026-11-15-c-02-persistencia-sqlite/`)
  - [x] 4. `C-03 capa-api-desacoplada` (Archivado en `openspec/changes/archive/2026-11-16-c-03-capa-api-desacoplada/`)
  - [ ] 5. `C-04 catalogo-recursos-pacientes-api` *(Opción A planificada como refuerzo adicional)*
- [x] **Ciclo SDD riguroso:** Propose $\to$ Apply $\to$ Pytest verde $\to$ Archive.
- [x] **Skill propia** creada y documentada (`.agents/skills/odontologia-api-guard/`).
- [x] **Servidor MCP** configurado e integrado (`sqlite-turnos` documentado y validado con `seed.py` en `C-02`).
- [x] **Datos Ficticios:** Garantizados en el diseño y en la suite de pruebas.
