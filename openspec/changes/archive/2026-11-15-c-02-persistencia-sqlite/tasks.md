# Tasks: C-02 Persistencia en SQLite y Multi-tenancy

## 1. Esquema Relacional e Inicialización de Base de Datos

- [x] 1.1 Crear el módulo `backend/src/persistence/database.py` con DDL relacional (tablas `tenants`, `profesionales`, `sillones`, `pacientes`, `turnos` con soporte de FKs y `PRAGMA foreign_keys = ON`) y verificar creación de tablas con test en SQLite real.

## 2. Repositorios de Persistencia con Filtrado por Tenant

- [x] 2.1 Implementar `RepositorioTurnos` en `backend/src/persistence/repositories.py` (`guardar`, `actualizar`, `obtener_por_id`, `buscar_activos_por_fecha`, `listar_por_tenant`) y verificar operaciones CRUD y filtrado por tenant con tests en SQLite real.
- [x] 2.2 Implementar repositorios auxiliares (`RepositorioProfesionales`, `RepositorioSillones`, `RepositorioPacientes`) en `backend/src/persistence/repositories.py` y verificar persistencia básica y aislamiento por tenant con tests.

## 3. Integración en Dominio y Validación Multi-tenant

- [x] 3.1 Actualizar los modelos en `backend/src/domain/models.py` para incorporar `id` y `tenant_id` manteniendo compatibilidad hacia atrás, y verificar con tests unitarios.
- [x] 3.2 Refactorizar `ServicioTurnos` en `backend/src/domain/services.py` para recibir `RepositorioTurnos` por inyección de dependencias (con fallback a SQLite `:memory:`) y validar solapamiento sobre persistencia real filtrada por `tenant_id`.
- [x] 3.3 Verificar el escenario de turnos simultáneos en clínicas distintas (aislamiento multi-tenant sin solapamiento entre tenants) mediante tests de integración en `backend/tests/test_persistencia.py`.
- [x] 3.4 Ejecutar la suite completa de pruebas (`pytest -v`) en `backend/` y confirmar que los 20 tests preexistentes y los nuevos tests de persistencia pasen en verde.

## Workflow follow-up

- Revisar los artefactos con el usuario (Governance ALTO).
- Ejecutar `/opsx:apply c-02-persistencia-sqlite` bajo ciclo Strict TDD.
- Ejecutar `pytest -v` y archivar con `/opsx:archive c-02-persistencia-sqlite`.
