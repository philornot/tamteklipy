"""
Globalne handlery błędów dla FastAPI
"""
import logging

from app.core.exceptions import TamteKlipyException
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def tamteklipy_exception_handler(request: Request, exc: TamteKlipyException):
    """
    Handler dla własnych wyjątków TamteKlipyException
    """
    logger.error(
        f"TamteKlipy Exception: {exc.message} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method} | "
        f"Details: {exc.details}"
    )

    response_content = {
        "error": exc.__class__.__name__,
        "message": exc.message,
        "path": str(request.url.path)
    }

    # Dodaj details jeśli są dostępne
    if exc.details:
        response_content["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler dla błędów walidacji Pydantic
    """
    logger.warning(
        f"Validation Error: {exc.errors()} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Nieprawidłowe dane wejściowe",
            "details": exc.errors(),
            "path": str(request.url.path)
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler dla błędów SQLAlchemy
    """
    logger.error(
        f"Database Error: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "Błąd bazy danych",
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handler dla wszystkich nieobsłużonych wyjątków
    """
    logger.error(
        f"Unhandled Exception: {str(exc)} | "
        f"Type: {type(exc).__name__} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Wystąpił nieoczekiwany błąd serwera",
            "path": str(request.url.path)
        }
    )
