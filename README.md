# Sistema de Gestión de Turnos Odontológicos (SaaS)

Este repositorio contiene la arquitectura y lógica de dominio para la gestión de turnos odontológicos, resolviendo la doble restricción física de disponibilidad simultánea e independiente de profesionales y sillones/boxes bajo intervalos semiabiertos $[inicio, fin)$.

El proyecto está especificado y construido bajo la metodología **Spec-Driven Development (SDD)** con **OpenSpec** y arquitectura en capas desacoplada.

---

## Integrantes del Equipo

* **Joseph Oliveros**
* **Cristian Rodríguez**

**Repositorio:** [https://github.com/Joseph-oliveros/tpi-metodologia1-oliveros-rodriguez.git](https://github.com/Joseph-oliveros/tpi-metodologia1-oliveros-rodriguez.git)

---

## Requisitos Previos

* Python 3.11 o superior.
* Git.
* (Opcional para Servidor MCP) `uv` / `uvx` o `Node.js` (`npx`).

---

## Instalación y Guía de Reproducción

Seguí estos pasos para clonar el repositorio, inicializar la base de datos con datos sintéticos y ejecutar la suite completa de pruebas:

### 1. Clonar el repositorio
```bash
git clone https://github.com/Joseph-oliveros/tpi-metodologia1-oliveros-rodriguez.git
cd tpi-metodologia1-oliveros-rodriguez
```

### 2. Crear y activar el entorno virtual en `backend/`
```bash
cd backend
python -m venv venv
```
* En Windows (PowerShell):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* En Linux / macOS:
  ```bash
  source venv/bin/activate
  ```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (sin secretos)
Copiar la plantilla de configuración de ejemplo:
```bash
# En Windows:
copy .env.example .env

# En Linux / macOS:
cp .env.example .env
```
> **Nota de Seguridad:** Las credenciales y bases de datos locales están protegidas en `.gitignore`. Nunca se commitean secretos al repositorio (D-05, regla 6 de `AGENTS.md`).

### 5. Poblar la base de datos con el Seed sintético
Ejecutar el script de inicialización para crear `turnos_odontologia.db` con datos 100% ficticios:
```bash
python seed.py
```
El script generará en `backend/turnos_odontologia.db`:
- 1 Tenant: `Clínica Odontológica Demo` (`demo-tenant`)
- 2 Profesionales: `Dr. Ejemplo` y `Dra. Prueba`
- 2 Sillones: `Sillón 1` y `Sillón 2`
- 1 Paciente: `Paciente Ficticio`
- 2 Turnos confirmados de prueba sin solapamiento

### 6. Ejecutar la suite completa de pruebas y guardas arquitectónicas
Desde `backend/`:
```bash
pytest -v
```
o con reporte de cobertura:
```bash
pytest -v --cov=src
```
Y desde la raíz del repositorio, para verificar la skill propia `odontologia-api-guard`:
```bash
python .agents/skills/odontologia-api-guard/scripts/check_api_guards.py
```
> **Resultado esperado:** Los **42 tests pasan en verde** contra SQLite real sin mocks (`D-04`), garantizando:
> - Doble validación independiente de recursos (profesional y sillón).
> - Intervalos semiabiertos $[inicio, fin)$ y turnos contiguos.
> - Máquina de estados (`PENDIENTE`, `CONFIRMADO`, `CANCELADO`, `COMPLETADO`) y liberación de recursos ante cancelaciones.
> - Persistencia relacional y aislamiento estricto multi-tenant (`RN-05`).
> - Endpoints HTTP FastAPI de turnos y catálogo (profesionales, sillones, pacientes), unicidad por tenant, mapeo explícito `409`/`404`/`422` y filtrado por header `X-Tenant-ID`.

### 7. Levantar la API FastAPI y abrir Swagger UI
Desde `backend/`:
```bash
uvicorn src.api.main:app --reload
```
- **Swagger UI (documentación interactiva):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Esquema OpenAPI:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health check:** `GET http://127.0.0.1:8000/api/health`

Para probar en Swagger los endpoints bajo `/api/v1/*` tras correr `python seed.py` (o dando de alta recursos nuevos vía `POST /api/v1/profesionales`, `/api/v1/sillones` y `/api/v1/pacientes`):
- Header obligatorio: `X-Tenant-ID: demo-tenant`
- IDs sintéticos sembrados: `paciente_id = "pac-1"`, `profesional_id = "prof-1"` o `"prof-2"`, `sillon_id = "sil-1"` o `"sil-2"`.
- **Endpoints disponibles:**
  - `GET /api/health`
  - `GET / POST /api/v1/profesionales`, `GET /api/v1/profesionales/{profesional_id}`
  - `GET / POST /api/v1/sillones`, `GET /api/v1/sillones/{sillon_id}`
  - `GET / POST /api/v1/pacientes`, `GET /api/v1/pacientes/{paciente_id}`
  - `GET / POST /api/v1/turnos`, `PATCH /api/v1/turnos/{turno_id}/estado`

---

## Skill Propia del Proyecto (`odontologia-api-guard`)

- **Ubicación:** [`.agents/skills/odontologia-api-guard/SKILL.md`](.agents/skills/odontologia-api-guard/SKILL.md) (acompañada de [`references/http-contracts.md`](.agents/skills/odontologia-api-guard/references/http-contracts.md) y [`scripts/check_api_guards.py`](.agents/skills/odontologia-api-guard/scripts/check_api_guards.py)).
- **Origen y adaptación:** diseñada siguiendo la guía estándar de skills de Antigravity (`agy-customizations`: `SKILL.md` + `references/` + `scripts/`) y referenciada en `AGENTS.md`, `CLAUDE.md` y `.atl/skill-registry.md`.
- **Qué aporta:** exige que toda ruta FastAPI delegue el doble candado en `ServicioTurnos` sin lógica de negocio ni `sqlite3` en `src/api/`, mantenga `src/domain/` puro, mapee excepciones a `409`/`404`/`422`, exija `X-Tenant-ID`, use datos sintéticos y se pruebe con `TestClient` contra SQLite real sin mocks.

---

## Configuración del Servidor MCP (SQLite MCP)

Para inspeccionar o interactuar con la base de datos SQLite persistida mediante un asistente con soporte MCP (como Google Antigravity o Claude Desktop), agregá la siguiente configuración en tu archivo de configuración de servidores MCP (`mcp_config.json`):

```json
{
  "mcpServers": {
    "sqlite-turnos": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-sqlite",
        "./backend/turnos_odontologia.db"
      ]
    }
  }
}
```

> **Nota:** La configuración utiliza la ruta relativa `./backend/turnos_odontologia.db` para mantener la portabilidad del repositorio entre diferentes entornos sin requerir rutas absolutas locales personales.
>
> **Capacidades y uso verificado:** `mcp-sqlite` habilita herramientas para listar tablas, inspeccionar el esquema relacional (incluyendo las columnas migradas en `C-04`) y ejecutar consultas SQL de solo lectura para auditar los registros sintéticos generados por `seed.py` o desde la API.

---

## Estado del Roadmap de Changes (OpenSpec / SDD)

El roadmap completo del proyecto se encuentra documentado en [CHANGES.md](CHANGES.md):

### Changes Archivados (5 completados)
* [x] **`2026-10-15-crear-turno-sin-solapamientos`** *(Base Parcial 2)*: Lógica de creación de turnos, intervalos semiabiertos y doble candado independiente.
* [x] **`2026-11-15-c-01-cancelacion-y-estados-turno`**: Ciclo de vida y máquina de estados (`confirmar`, `cancelar`, `completar`), excepciones de dominio y liberación de recursos por cancelación (`RN-03`, `RN-04`).
* [x] **`2026-11-15-c-02-persistencia-sqlite`**: Capa de persistencia relacional SQLite con repositorios desacoplados y aislamiento multi-tenant estricto (`RN-05`, `D-01`, `D-04`).
* [x] **`2026-11-16-c-03-capa-api-desacoplada`**: Desacople de dominio por puerto (`RepositorioTurnosPort`), capa `infrastructure/`, API REST con **FastAPI** + **Swagger UI** (`/api/health`, `/api/v1/turnos`) y aplicación de la skill propia `odontologia-api-guard`.
* [x] **`2026-11-17-c-04-catalogo-recursos-pacientes-api`**: Endpoints REST multi-tenant para alta y consulta de profesionales, sillones y pacientes (`/api/v1/profesionales`, `/api/v1/sillones`, `/api/v1/pacientes`), migración idempotente SQLite y reglas de unicidad por tenant.

### Próximo Change Planificado
* [ ] **`C-05-auth auth-rbac-tenancy`**: Autenticación JWT, RBAC y reemplazo del header temporal `X-Tenant-ID`.

### Changes Pendientes (Roadmap MVP adaptado y Fases 2-5)
* [ ] **`C-08 reprogramacion-turno`**: Reprogramación atómica de turnos.
* [ ] **`C-09 admin-recursos-crud`**: Administración avanzada de profesionales y sillones con RBAC.
* [ ] **`C-10 bloqueo-sillon`**: Bloqueo de sillones por mantenimiento.
* [ ] **`C-11 frontend-shell`**: Shell de navegación y layout web.
* [ ] **`C-12 agenda-turnos-ui`**: Interfaz de usuario para la agenda de turnos.
* [ ] **`C-13 agenda-matricial`** *(Segunda etapa)*: Vista matricial por profesional y sillón.
* [ ] **`C-14 notificaciones-whatsapp`** *(Segunda etapa)*: Recordatorios automáticos.
* [ ] **`C-15 lista-espera`** *(Segunda etapa)*: Asignación automática ante turnos cancelados.

---

## Estructura del Proyecto

```text
├── .agents/
│   └── skills/
│       └── odontologia-api-guard/  # Skill propia del proyecto + verificador AST
├── .gitignore                      # Protección de .env, *.db y cachés
├── AGENTS.md                       # Reglas duras y guía canónica de agentes
├── CHANGES.md                      # Roadmap de cambios e índice SDD adaptado
├── CLAUDE.md                       # Sincronización de instrucciones
├── CONSIGNAS_TPI.md                # Consignas y matriz de evaluación del TPI
├── README.md                       # Guía de reproducción y documentación
├── backend/
│   ├── .env.example                # Plantilla de variables de entorno sin secretos
│   ├── pytest.ini                  # Configuración de pytest
│   ├── requirements.txt            # Dependencias del backend (FastAPI, Uvicorn, pytest)
│   ├── seed.py                     # Generador de datos sintéticos
│   ├── turnos_odontologia.db       # Base de datos SQLite local (en .gitignore)
│   ├── src/
│   │   ├── api/                    # Controladores FastAPI, esquemas Pydantic y handlers HTTP
│   │   ├── domain/                 # Dominio puro (modelos, servicios, puertos, excepciones)
│   │   ├── infrastructure/         # Configuración por entorno y sesión SQLite
│   │   └── persistence/            # Persistencia relacional (database, repositorios)
│   └── tests/                      # Suite de pruebas automatizadas (42 tests verdes)
├── knowledge-base/                 # Base de conocimiento del dominio (10 documentos)
└── openspec/                       # Especificaciones vivas y cambios archivados
    ├── changes/archive/            # Historial de cambios archivados
    └── specs/                      # Especificaciones vigentes del sistema
```
