"""
TamteKlipy — Główny plik aplikacji FastAPI
"""
import logging
import time
from pathlib import Path

from app.core.config import settings
from app.routers import auth, files, awards  # DODANE: awards
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Prywatna platforma do zarządzania klipami z gier i screenshotami",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    logger.info(f"🔵 Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"✅ Response: {request.method} {request.url.path} "
        f"[Status: {response.status_code}] [Time: {process_time:.3f}s]"
    )
    return response


# Startup event
@app.on_event("startup")
async def startup_event():
    """Wykonywane przy starcie aplikacji"""
    logger.info(f"🚀 {settings.app_name} startuje...")
    logger.info(f"🌍 Environment: {settings.environment}")
    logger.info("📚 Dokumentacja dostępna na: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Wykonywane przy zamykaniu aplikacji"""
    logger.info(f"🛑 {settings.app_name} wyłącza się...")


# Root endpoint
@app.get("/", tags=["📊 Status"])
async def root():
    """Podstawowy endpoint do sprawdzenia, czy API działa"""
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
@app.get("/health", tags=["📊 Status"])
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
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 Autoryzacja"])
app.include_router(files.router, prefix="/api/files", tags=["📁 Pliki"])
app.include_router(awards.router, prefix="/api/awards", tags=["🏆 Nagrody"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
