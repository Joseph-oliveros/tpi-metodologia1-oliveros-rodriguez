# Contratos HTTP y Mapeo de Errores — `odontologia-api-guard`

Referencia normativa para la capa `backend/src/api/` alineada con `knowledge-base/features.md` §5.2 y `knowledge-base/business-rules.md`.

## 1. Contexto Multi-Tenant (`C-03` / pre-JWT)

- **Header obligatorio:** `X-Tenant-ID` (string no vacío, longitud mínima 1 tras `strip()`).
- Si falta el header o viene vacío/espacios:
  - Missing header $\to$ `422 Unprocessable Entity` (FastAPI validation).
  - Blank string $\to$ `422 Unprocessable Entity` (`X-Tenant-ID no puede estar vacío`).
- **Regla Swagger:** los esquemas de ejemplo en OpenAPI deben usar `"demo-tenant"` (coherente con `backend/seed.py`) y nunca datos reales de clínicas.

## 2. Tabla de Mapeo de Excepciones de Dominio a HTTP

| Excepción / Situación | HTTP Status | `codigo` | `recurso` (opcional) | Regla |
|---|---|---|---|---|
| `SolapamientoProfesionalError` | `409 Conflict` | `SOLAPAMIENTO_PROFESIONAL` | `"profesional"` | `RN-01`, `RN-09` |
| `SolapamientoSillonError` | `409 Conflict` | `SOLAPAMIENTO_SILLON` | `"sillon"` | `RN-01` |
| `TransicionInvalidaError` | `409 Conflict` | `TRANSICION_INVALIDA` | `null` | `RN-03` |
| Entidad/turno inexistente o de otro tenant | `404 Not Found` | `RECURSO_NO_ENCONTRADO` | nombre recurso | `RN-05` |
| Error de formato o `hora_fin <= hora_inicio` | `422 Unprocessable Entity` | estándar FastAPI/Pydantic | `null` | `RP-01` |

### Formato estándar de respuesta de error de negocio (`ErrorResponse`)

```json
{
  "detail": "El profesional Dr. Ejemplo ya tiene un turno el 2026-11-20 de 09:00 a 09:30",
  "codigo": "SOLAPAMIENTO_PROFESIONAL",
  "recurso": "profesional"
}
```

## 3. Estándares FastAPI del Proyecto

- Usar `Annotated[T, Depends(...)]`, `Annotated[str, Header(...)]`, `Annotated[str, Query(...)]`.
- Usar funciones síncronas `def` en routers que operan contra `sqlite3` para ejecutarse de forma segura en el threadpool de FastAPI sin bloquear el event loop.
- Declarar `prefix`, `tags` y `responses` en `APIRouter` o decoradores de operación.
- Nunca utilizar `...` como default en parámetros requeridos con `Annotated` cuando no aporta valor; en Pydantic v2 preferir `Field(...)` o tipos explícitos con `examples=[...]`.
