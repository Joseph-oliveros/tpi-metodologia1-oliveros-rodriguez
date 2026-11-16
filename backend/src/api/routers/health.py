"""Router de verificación de estado de salud del servicio."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["Salud"])


@router.get("/health", summary="Verificar estado de salud de la API")
def health_check() -> HealthResponse:
    """Retorna el estado operativo del servicio backend."""
    return HealthResponse(status="ok", service="turnos-odontologia-api")
