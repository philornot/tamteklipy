"""
Custom exception classes dla TamteKlipy
"""
from typing import Optional, Dict, Any

from fastapi import status


class TamteKlipyException(Exception):
    """Bazowa klasa dla własnych wyjątków"""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TamteKlipyException):
    """Błąd autoryzacji - nieprawidłowe dane logowania"""

    def __init__(
            self,
            message: str = "Nieprawidłowe dane logowania",
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(TamteKlipyException):
    """Błąd autoryzacji - brak uprawnień"""

    def __init__(
            self,
            message: str = "Brak uprawnień do wykonania tej operacji",
            required_scope: Optional[str] = None
    ):
        details = {"required_scope": required_scope} if required_scope else {}
        super().__init__(
            message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundError(TamteKlipyException):
    """Zasób nie został znaleziony"""

    def __init__(
            self,
            resource: str = "Zasób",
            resource_id: Optional[int] = None
    ):
        message = f"{resource} nie został znaleziony"
        if resource_id:
            message = f"{resource} o ID {resource_id} nie został znaleziony"

        details = {"resource": resource}
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ValidationError(TamteKlipyException):
    """Błąd walidacji danych wejściowych"""

    def __init__(
            self,
            message: str = "Nieprawidłowe dane wejściowe",
            field: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None
    ):
        if field and not details:
            details = {"field": field}

        super().__init__(
            message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class FileUploadError(TamteKlipyException):
    """Błąd podczas uploadu pliku"""

    def __init__(
            self,
            message: str = "Błąd podczas uploadu pliku",
            filename: Optional[str] = None,
            reason: Optional[str] = None
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if reason:
            details["reason"] = reason

        super().__init__(
            message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class StorageError(TamteKlipyException):
    """Błąd dostępu do storage"""

    def __init__(
            self,
            message: str = "Błąd dostępu do storage",
            path: Optional[str] = None,
            *,
            status_code: Optional[int] = None,
            details: Optional[Dict[str, Any]] = None
    ):
        combined_details = dict(details) if details else {}
        if path and "path" not in combined_details:
            combined_details["path"] = path

        resolved_status = status_code or status.HTTP_500_INTERNAL_SERVER_ERROR

        super().__init__(
            message,
            status_code=resolved_status,
            details=combined_details
        )


class DatabaseError(TamteKlipyException):
    """Błąd bazy danych"""

    def __init__(
            self,
            message: str = "Błąd bazy danych",
            operation: Optional[str] = None
    ):
        details = {"operation": operation} if operation else {}
        super().__init__(
            message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DuplicateError(TamteKlipyException):
    """Zasób już istnieje (duplikat)"""

    def __init__(
            self,
            resource: str = "Zasób",
            field: Optional[str] = None,
            value: Optional[str] = None
    ):
        message = f"{resource} już istnieje"
        if field and value:
            message = f"{resource} z {field}='{value}' już istnieje"

        details = {"resource": resource}
        if field:
            details["field"] = field
        if value:
            details["value"] = value

        super().__init__(
            message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(TamteKlipyException):
    """Przekroczono limit requestów"""

    def __init__(
            self,
            message: str = "Przekroczono limit requestów",
            retry_after: Optional[int] = None
    ):
        details = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(
            message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )
