"""Mapeo centralizado de excepciones de dominio a respuestas HTTP estándar."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.api.schemas import ErrorResponse
from src.domain.exceptions import (
    SolapamientoProfesionalError,
    SolapamientoSillonError,
    TransicionInvalidaError,
)


class RecursoNoEncontradoError(Exception):
    """El recurso o turno solicitado no existe dentro del tenant activo."""

    def __init__(self, recurso: str, mensaje: str) -> None:
        self.recurso = recurso
        super().__init__(mensaje)


def _error_json(
    status_code: int, detail: str, codigo: str, recurso: str | None = None
) -> JSONResponse:
    payload = ErrorResponse(detail=detail, codigo=codigo, recurso=recurso)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de errores de negocio en FastAPI."""

    @app.exception_handler(SolapamientoProfesionalError)
    def handle_solapamiento_profesional(
        _request: Request, exc: SolapamientoProfesionalError
    ) -> JSONResponse:
        return _error_json(
            status.HTTP_409_CONFLICT,
            str(exc),
            "SOLAPAMIENTO_PROFESIONAL",
            "profesional",
        )

    @app.exception_handler(SolapamientoSillonError)
    def handle_solapamiento_sillon(
        _request: Request, exc: SolapamientoSillonError
    ) -> JSONResponse:
        return _error_json(
            status.HTTP_409_CONFLICT,
            str(exc),
            "SOLAPAMIENTO_SILLON",
            "sillon",
        )

    @app.exception_handler(TransicionInvalidaError)
    def handle_transicion_invalida(
        _request: Request, exc: TransicionInvalidaError
    ) -> JSONResponse:
        return _error_json(
            status.HTTP_409_CONFLICT,
            str(exc),
            "TRANSICION_INVALIDA",
        )

    @app.exception_handler(RecursoNoEncontradoError)
    def handle_recurso_no_encontrado(
        _request: Request, exc: RecursoNoEncontradoError
    ) -> JSONResponse:
        return _error_json(
            status.HTTP_404_NOT_FOUND,
            str(exc),
            "RECURSO_NO_ENCONTRADO",
            exc.recurso,
        )
