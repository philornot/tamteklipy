"""
TamteKlipy — Główny plik aplikacji FastAPI
"""
import logging
import time
from pathlib import Path

from app.core.cache import init_cache  # NOWE
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
from app.routers import auth, files, awards, admin, my_awards
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

# Konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Prywatna platforma do zarządzania klipami z gier i screenshotami",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rejestracja exception handlers
app.add_exception_handler(TamteKlipyException, tamteklipy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)


# Custom Middleware - Request Timing & Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware do logowania requestów i mierzenia czasu odpowiedzi"""
    start_time = time.time()

    # Loguj cache-related headers
    cache_headers = {
        "if-none-match": request.headers.get("if-none-match"),
        "if-modified-since": request.headers.get("if-modified-since"),
        "cache-control": request.headers.get("cache-control"),
    }
    logger.debug(f"📨 Cache headers: {cache_headers}")

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Sprawdź czy response ma cache headers
    response_cache_headers = {
        "etag": response.headers.get("etag"),
        "cache-control": response.headers.get("cache-control"),
        "expires": response.headers.get("expires"),
    }
    logger.debug(f"📤 Response cache headers: {response_cache_headers}")

    # Dodaj header X-Cache dla debugowania
    cache_status = response.headers.get("X-Cache", "MISS")
    logger.debug(f"🏷️ Cache status: {cache_status}")

    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"[Status: {response.status_code}] [Time: {process_time:.3f}s] [Cache: {cache_status}]"
    )

    return response


# Startup event
@app.on_event("startup")
async def startup_event():
    """Wykonywane przy starcie aplikacji"""
    logger.info(f"{settings.app_name} startuje...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"CORS Allowed Origins: {settings.allowed_origins}")
    logger.info(f"CORS Origins List: {settings.origins_list}")

    # Inicjalizuj bazę danych
    try:
        init_db()
        logger.info("Baza danych gotowa")
    except Exception as e:
        logger.error(f"Błąd inicjalizacji bazy danych: {e}")

    # Inicjalizuj cache z Redis
    try:
        redis_url = settings.redis_url
        init_cache(redis_url=redis_url)
        logger.info(f"Cache initialized with Redis: {redis_url}")
    except Exception as e:
        logger.error(f"Redis cache init failed: {e}, falling back to InMemory")
        init_cache(redis_url=None)

    # Utwórz katalog ikon nagród
    try:
        icons_dir = Path(settings.award_icons_path)
        if settings.environment == "development":
            icons_dir = Path("uploads/award_icons")

        icons_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Award icons directory: {icons_dir}")
    except Exception as e:
        logger.error(f"Błąd tworzenia katalogu ikon nagród: {e}")

    logger.info("Dokumentacja dostępna na: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Wykonywane przy zamykaniu aplikacji"""
    logger.info(f"{settings.app_name} wyłącza się...")


# Root endpoint
@app.get("/", tags=["Status"])
async def root():
    """Podstawowy endpoint do sprawdzenia czy API działa"""
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
        }
    }


# Health check endpoint
@app.get("/health", tags=["Status"])
async def health_check():
    """
    Health check dla monitoringu
    Sprawdza status API, dostęp do storage i bazę danych
    """
    health_status = {
        "status": "healthy",
        "api": "online",
        "version": "0.1.0",
        "environment": settings.environment,
        "checks": {}
    }

    # Sprawdź bazę danych
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Sprawdź cache
    try:
        from fastapi_cache import FastAPICache
        backend = FastAPICache.get_backend()
        health_status["checks"]["cache"] = {
            "status": "ok",
            "backend": type(backend).__name__
        }
    except Exception as e:
        logger.error(f"Cache check failed: {e}")
        health_status["checks"]["cache"] = {
            "status": "error",
            "error": str(e)
        }

    # Sprawdź dostęp do storage (tylko w produkcji/na RPi)
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
        health_status["checks"]["storage"] = {
            "status": "skipped",
            "reason": "Development environment"
        }

    return health_status


# Rejestracja routerów
app.include_router(auth.router, prefix="/api/auth", tags=["Autoryzacja"])
app.include_router(files.router, prefix="/api/files", tags=["Pliki"])
app.include_router(awards.router, prefix="/api/awards", tags=["Nagrody"])
app.include_router(my_awards.router, prefix="/api/my-awards", tags=["My Custom Awards"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

frontend_dist = Path("../frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API routes już są obsłużone wyżej
        if full_path.startswith("api/"):
            return {"error": "Not found"}

        # Próbuj zwrócić plik
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Fallback do index.html (dla React Router)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn

    # HTTP/2 wymaga SSL/TLS
    # W produkcji Cloudflare Tunnel obsługuje SSL
    # W dev można użyć self-signed certificates

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        http="h2",  # Włącz HTTP/2
        reload=True,
        # Dla produkcji z Cloudflare Tunnel:
        # ssl_keyfile="/path/to/key.pem",
        # ssl_certfile="/path/to/cert.pem",
    )
