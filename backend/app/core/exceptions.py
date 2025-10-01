"""
Custom exception classes dla TamteKlipy
"""
from fastapi import status


class TamteKlipyException(Exception):
    """Bazowa klasa dla własnych wyjątków"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(TamteKlipyException):
    """Błąd autoryzacji - nieprawidłowe dane logowania"""

    def __init__(self, message: str = "Nieprawidłowe dane logowania"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(TamteKlipyException):
    """Błąd autoryzacji - brak uprawnień"""

    def __init__(self, message: str = "Brak uprawnień do wykonania tej operacji"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(TamteKlipyException):
    """Zasób nie został znaleziony"""

    def __init__(self, message: str = "Zasób nie został znaleziony"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(TamteKlipyException):
    """Błąd walidacji danych wejściowych"""

    def __init__(self, message: str = "Nieprawidłowe dane wejściowe"):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileUploadError(TamteKlipyException):
    """Błąd podczas uploadu pliku"""

    def __init__(self, message: str = "Błąd podczas uploadu pliku"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class StorageError(TamteKlipyException):
    """Błąd dostępu do storage"""

    def __init__(self, message: str = "Błąd dostępu do storage"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseError(TamteKlipyException):
    """Błąd bazy danych"""

    def __init__(self, message: str = "Błąd bazy danych"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
