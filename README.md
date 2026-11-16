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

### 6. Ejecutar la suite completa de pruebas
```bash
pytest -v
```
o con reporte de cobertura:
```bash
pytest -v --cov=src
```
> **Resultado esperado:** Los **25 tests pasan en verde** contra SQLite real sin mocks (`D-04`), garantizando:
> - Doble validación independiente de recursos (profesional y sillón).
> - Intervalos semiabiertos $[inicio, fin)$ y turnos contiguos.
> - Máquina de estados (`PENDIENTE`, `CONFIRMADO`, `CANCELADO`, `COMPLETADO`) y liberación de recursos ante cancelaciones.
> - Persistencia relacional y aislamiento estricto multi-tenant (`RN-05`).

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

---

## Estado del Roadmap de Changes (OpenSpec / SDD)

El roadmap completo del proyecto se encuentra documentado en [CHANGES.md](CHANGES.md):

### Changes Archivados (3 completados)
* [x] **`2026-10-15-crear-turno-sin-solapamientos`** *(Base Parcial 2)*: Lógica de creación de turnos, intervalos semiabiertos y doble candado independiente.
* [x] **`2026-11-15-c-01-cancelacion-y-estados-turno`**: Ciclo de vida y máquina de estados (`confirmar`, `cancelar`, `completar`), excepciones de dominio y liberación de recursos por cancelación (`RN-03`, `RN-04`).
* [x] **`2026-11-15-c-02-persistencia-sqlite`**: Capa de persistencia relacional SQLite con repositorios desacoplados y aislamiento multi-tenant estricto (`RN-05`, `D-01`, `D-04`).

### Próximo Change
* [ ] **`C-03 capa-api-desacoplada`**: Exposición de endpoints REST con **FastAPI** y documentación interactiva **Swagger/OpenAPI**, desacoplada de la capa de dominio.

### Changes Pendientes (Roadmap MVP y Fases 2-5)
* [ ] **`C-04 auth-rbac-tenancy`**: Autenticación, RBAC y contexto de tenant en la API.
* [ ] **`C-05 endpoints-turnos`**: Endpoints HTTP completos de alta, consulta y estados de turnos.
* [ ] **`C-06 endpoints-recursos`**: Endpoints de consulta para profesionales y sillones.
* [ ] **`C-07 gestion-pacientes`**: Gestión básica de pacientes.
* [ ] **`C-08 reprogramacion-turno`**: Reprogramación atómica de turnos.
* [ ] **`C-09 admin-recursos-crud`**: Administración de profesionales y sillones.
* [ ] **`C-10 bloqueo-sillon`**: Bloqueo de sillones por mantenimiento.
* [ ] **`C-11 frontend-shell`**: Shell de navegación y layout web.
* [ ] **`C-12 agenda-turnos-ui`**: Interfaz de usuario para la agenda de turnos.
* [ ] **`C-13 agenda-matricial`** *(Segunda etapa)*: Vista matricial por profesional y sillón.
* [ ] **`C-14 notificaciones-whatsapp`** *(Segunda etapa)*: Recordatorios automáticos.
* [ ] **`C-15 lista-espera`** *(Segunda etapa)*: Asignación automática ante turnos cancelados.

---

## Estructura del Proyecto

```text
├── .gitignore                      # Protección de .env, *.db y cachés
├── AGENTS.md                       # Reglas duras y guía canónica de agentes
├── CHANGES.md                      # Roadmap de cambios e índice SDD
├── CLAUDE.md                       # Sincronización de instrucciones
├── CONSIGNAS_TPI.md                # Consignas y matriz de evaluación del TPI
├── README.md                       # Guía de reproducción y documentación
├── backend/
│   ├── .env.example                # Plantilla de variables de entorno sin secretos
│   ├── pytest.ini                  # Configuración de pytest
│   ├── requirements.txt            # Dependencias del backend
│   ├── seed.py                     # Generador de datos sintéticos
│   ├── turnos_odontologia.db       # Base de datos SQLite local (en .gitignore)
│   ├── src/
│   │   ├── domain/                 # Dominio puro (modelos, servicios, excepciones)
│   │   └── persistence/            # Persistencia relacional (database, repositorios)
│   └── tests/                      # Suite de pruebas automatizadas (25 tests verdes)
├── knowledge-base/                 # Base de conocimiento del dominio (10 documentos)
└── openspec/                       # Especificaciones vivas y cambios archivados
    ├── changes/archive/            # Historial de cambios archivados
    └── specs/                      # Especificaciones vigentes del sistema
```
