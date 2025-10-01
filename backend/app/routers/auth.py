"""
Router dla autoryzacji - logowanie, rejestracja, tokeny JWT
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

# OAuth2 scheme do pobierania tokenu z headera
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint logowania - zwraca JWT token
    POST /api/auth/login
    Body: username, password (form-data)
    """
    # TODO: Implementacja po dodaniu bazy danych i modeli
    # 1. Sprawdź czy użytkownik istnieje
    # 2. Zweryfikuj hasło (bcrypt)
    # 3. Wygeneruj JWT token
    # 4. Zwróć token

    return {
        "message": "Login endpoint - implementacja wkrótce",
        "username": form_data.username,
        "status": "not_implemented"
    }


@router.post("/register")
async def register():
    """
    Endpoint rejestracji nowego użytkownika
    POST /api/auth/register
    Body: username, email, password
    """
    # TODO: Implementacja po dodaniu bazy danych
    # 1. Sprawdź czy użytkownik nie istnieje
    # 2. Zahashuj hasło (bcrypt)
    # 3. Utwórz użytkownika w bazie
    # 4. Zwróć sukces

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Rejestracja będzie dostępna wkrótce"
    )


@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Endpoint zwracający dane zalogowanego użytkownika
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    """
    # TODO: Implementacja po dodaniu JWT
    # 1. Zdekoduj token
    # 2. Pobierz użytkownika z bazy
    # 3. Zwróć dane użytkownika

    return {
        "message": "User info endpoint - implementacja wkrótce",
        "token_received": bool(token),
        "status": "not_implemented"
    }


@router.post("/refresh")
async def refresh_token():
    """
    Endpoint do odświeżania JWT tokenu
    POST /api/auth/refresh
    """
    # TODO: Implementacja po dodaniu JWT

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token będzie dostępny wkrótce"
    )
