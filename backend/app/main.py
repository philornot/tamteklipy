"""
TamteKlipy – Główny plik aplikacji FastAPI

Architektura:
- Frontend: React SPA (Single Page Application)
- Backend: FastAPI REST API
- Deployment: Cloudflare Tunnel → RPi (localhost:8001)
- Database: SQLite
"""
import logging
import time
from pathlib import Path

from app.core.config import settings
from app.core.database import engine
from app.core.error_handlers import (
    tamteklipy_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler
)
from app.core.exceptions import TamteKlipyException
from app.core.init_db import init_db
from app.core.logging_config import setup_logging
from app.models import User
from app.routers import auth, files, awards, admin, my_awards, comments
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

# ───────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ───────────────────────────────────────────────────────────────────────────────
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────────
# FASTAPI APP INITIALIZATION
# ───────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Prywatna platforma do zarządzania klipami z gier",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc alternative docs
)

# ───────────────────────────────────────────────────────────────────────────────
# EXCEPTION HANDLERS
# ───────────────────────────────────────────────────────────────────────────────
# Rejestrujemy custom handlery dla różnych typów błędów
# Zapewnia to spójne formatowanie błędów w API
app.add_exception_handler(TamteKlipyException, tamteklipy_exception_handler)  # Nasze custom exceptions
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # Pydantic validation
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)  # Database errors
app.add_exception_handler(Exception, generic_exception_handler)  # Catch-all dla nieobsłużonych błędów

# ───────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE - CORS
# ───────────────────────────────────────────────────────────────────────────────
# Cross-Origin Resource Sharing - pozwala frontendowi (localhost:5173 w dev)
# komunikować się z backendem (localhost:8001 w dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,  # Lista dozwolonych domen (z .env)
    allow_credentials=True,  # Pozwala na cookies/auth headers
    allow_methods=["*"],  # Wszystkie metody HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Wszystkie headers
)

# ───────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE - TRUSTED HOST
# ───────────────────────────────────────────────────────────────────────────────
# Zabezpiecza przed Host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # W produkcji można zawęzić do ["tamteklipy.pl", "localhost"]
)



# ───────────────────────────────────────────────────────────────────────────────
# STARTUP EVENT
# ───────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """
    Wykonywane JEDEN RAZ przy starcie aplikacji.
    Inicjalizuje:
    - Bazę danych (SQLite)
    - Cache (Redis w prod, InMemory w dev)
    - Katalogi na pliki (clips, thumbnails, award icons)
    """
    logger.info(f"{settings.app_name} startuje...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS Allowed Origins: {settings.allowed_origins}")
    logger.info(f"CORS Origins List: {settings.origins_list}")

    # 1. Inicjalizuj bazę danych (SQLite)
    try:
        init_db()  # Tworzy tabele jeśli nie istnieją
        logger.info("Baza danych gotowa")
    except Exception as e:
        logger.error(f"Błąd inicjalizacji bazy danych: {e}")

    # 2. Inicjalizuj cache
    # CACHE ZOSTAŁO USUNIĘTE TK-603

    # 3. Utwórz katalog na ikony nagród
    try:
        icons_dir = Path(settings.award_icons_path)
        if settings.environment == "development":
            icons_dir = Path("uploads/award_icons")

        icons_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Award icons directory: {icons_dir}")
    except Exception as e:
        logger.error(f"Błąd tworzenia katalogu ikon nagród: {e}")

    logger.info("Dokumentacja dostępna na: http://localhost:8001/docs")


# ───────────────────────────────────────────────────────────────────────────────
# SHUTDOWN EVENT
# ───────────────────────────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown_event():
    """
    Wykonywane przy zamykaniu aplikacji (graceful shutdown).
    Można tutaj zamykać połączenia, zapisywać state, etc.
    """
    logger.info(f"{settings.app_name} wyłącza się...")


# ───────────────────────────────────────────────────────────────────────────────
# API ROUTERS
# ───────────────────────────────────────────────────────────────────────────────
# Rejestrujemy wszystkie endpointy z osobnych plików (routers/)
# Prefix /api/ dla wszystkich endpointów API
app.include_router(auth.router, prefix="/api/auth", tags=["Autoryzacja"])
app.include_router(files.router, prefix="/api/files", tags=["Pliki"])
app.include_router(awards.router, prefix="/api/awards", tags=["Nagrody"])
app.include_router(my_awards.router, prefix="/api/my-awards", tags=["My Custom Awards"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(comments.router, prefix="/api", tags=["Komentarze"])

# ───────────────────────────────────────────────────────────────────────────────
# FRONTEND SERVING (SPA)
# ───────────────────────────────────────────────────────────────────────────────
# FastAPI serwuje React frontend jako static files
# Frontend jest zbudowany jako SPA (Single Page Application)
# i używa React Router do nawigacji client-side

frontend_dist = Path("../frontend/dist")

if frontend_dist.exists():
    # 1. Static assets (JS, CSS, images)
    # /assets/* będzie serwowane bezpośrednio z katalogu dist/assets/
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


    # 2. Root endpoint - REDIRECT do /dashboard
    # Zamiast pokazywać JSON, przekierowujemy użytkownika do aplikacji
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """
        Redirect root URL (tamteklipy.pl) do /dashboard.
        React Router następnie przekieruje do /login jeśli user nie jest zalogowany.

        include_in_schema=False - nie pokazuj w /docs (to nie jest API endpoint)
        """
        return RedirectResponse(url="/dashboard", status_code=302)


    # 3. Health check endpoint - dla monitoringu/alertów
    @app.get("/health", tags=["Status"])
    async def health_check():
        """
        Health check dla monitoringu.
        Sprawdza:
        - Status API (online/offline)
        - Połączenie z bazą danych
        - Dostęp do storage (tylko w produkcji)

        Zwraca:
        - 200 OK: wszystko działa ("healthy")
        - 200 OK: częściowe problemy ("degraded")
        - 500 Error: krytyczne problemy ("unhealthy")
        """
        health_status = {
            "status": "healthy",
            "api": "online",
            "version": "0.1.0",
            "environment": settings.environment,
            "checks": {}
        }

        # Check 1: Baza danych
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")  # Simple query to test connection
            db.close()
            health_status["checks"]["database"] = {"status": "ok"}
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            health_status["checks"]["database"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"

        # Check 2: Cache
        # CACHE ZOSTAŁO USUNIĘTE - TK-603

        # Check 3: Storage (tylko w produkcji - na RPi)
        if settings.environment == "production":
            try:
                storage_path = Path(settings.storage_path)
                storage_accessible = storage_path.exists() and storage_path.is_dir()

                health_status["checks"]["storage"] = {
                    "status": "ok" if storage_accessible else "error",
                    "path": settings.storage_path,
                    "accessible": storage_accessible
                }

                if not storage_accessible:
                    health_status["status"] = "degraded"

            except Exception as e:
                logger.error(f"Storage check failed: {e}")
                health_status["checks"]["storage"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        else:
            # W dev nie sprawdzamy storage (używamy lokalnych katalogów)
            health_status["checks"]["storage"] = {
                "status": "skipped",
                "reason": "Development environment"
            }

        return health_status


    # 4. Catch-all route - serwuje index.html dla React Router
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """
        Catch-all route dla React Router (SPA).

        Obsługuje:
        - /dashboard → index.html (React Router obsłuży routing)
        - /upload → index.html
        - /login → index.html
        - /favicon.ico → zwróć plik
        - /logo.png → zwróć plik

        API routes (/api/*) są już obsłużone przez routery powyżej,
        więc tutaj trafiają tylko frontend routes i static files.
        """
        # API routes już są obsłużone wyżej przez routery
        # Ten check jest na wszelki wypadek
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404

        # Próbuj zwrócić konkretny plik (dla favicon, images, etc.)
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Fallback: zwróć index.html
        # React Router obsłuży routing client-side
        # Wszystkie routes (/dashboard, /upload, etc.) dostają ten sam index.html
        return FileResponse(frontend_dist / "index.html")

else:
    # ───────────────────────────────────────────────────────────────────────────────
    # FALLBACK - gdy frontend NIE jest zbudowany
    # ───────────────────────────────────────────────────────────────────────────────
    # W dev: jeśli nie zrobiłeś 'npm run build', API nadal działa
    # ale pokazuje JSON zamiast frontendu

    @app.get("/", tags=["Status"])
    async def root():
        """
        API status endpoint (fallback gdy brak frontendu).
        Pokazuje podstawowe info o API i dostępnych endpointach.
        """
        return {
            "message": f"{settings.app_name} działa!",
            "version": "0.1.0",
            "status": "online",
            "environment": settings.environment,
            "docs": "/docs",
            "endpoints": {
                "auth": "/api/auth",
                "files": "/api/files",
                "awards": "/api/awards"
            },
            "note": "Frontend nie jest zbudowany. Uruchom: cd frontend && npm run build"
        }


    @app.get("/health", tags=["Status"])
    async def health_check_fallback():
        """Health check (simplified fallback)"""
        return {
            "status": "healthy",
            "api": "online",
            "version": "0.1.0",
            "environment": settings.environment
        }

# ───────────────────────────────────────────────────────────────────────────────
# DEV SERVER - uruchomienie bezpośrednio (python main.py)
# Lepiej użyj uvicorn: python -m uvicorn app.main:app --reload
# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    # Konfiguracja Uvicorn dla Cloudflare Tunnel:
    #
    # Cloudflare Tunnel automatycznie obsługuje:
    # ✅ SSL/TLS (HTTPS) - między użytkownikiem a Cloudflare
    # ✅ HTTP/2 - między użytkownikiem a Cloudflare
    # ✅ Certyfikaty SSL - auto-renew co 90 dni
    # ✅ DDoS protection, CDN, cache
    #
    # Lokalnie (RPi) używamy:
    # ✅ Prosty HTTP (bez SSL) na localhost:8001
    # ✅ Cloudflare Tunnel tuneluje to bezpiecznie do internetu
    #
    # NIE POTRZEBUJEMY:
    # ❌ Certyfikatów SSL na RPi
    # ❌ http="h2" flag (wymaga SSL)
    # ❌ ssl_keyfile/ssl_certfile

    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",  # Słuchaj na wszystkich interfejsach
        "port": 8001,  # Port dla produkcji (zgodny z systemd i Cloudflare Tunnel config)
    }

    # Development mode - dodatkowe opcje
    if settings.environment == "development":
        config["reload"] = True  # Auto-reload przy zmianach w kodzie
        config["port"] = 8000  # Inny port dla dev (żeby nie kolidować z prod)
        config["log_level"] = "debug"  # Więcej logów

    # Uruchom server
    uvicorn.run(**config)
