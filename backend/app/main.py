"""
TamteKlipy — Główny plik aplikacji FastAPI
"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routerów (na razie zakomentowane, dodamy później)
# from app.routers import auth, clips, awards

app = FastAPI(
    title="TamteKlipy API",
    description="Prywatna platforma do zarządzania klipami z gier i screenshotami",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Konfiguracja CORS (Frontend będzie na innym porcie)
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternatywny port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # Cloudflare URL dodamy później przez zmienne środowiskowe
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware (ochrona przed Host Header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # W produkcji ograniczymy do konkretnych hostów
)


# Custom Middleware - Request Timing & Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware do logowania requestów i mierzenia czasu odpowiedzi"""
    start_time = time.time()

    # Loguj przychodzące requesty
    logger.info(f"🔵 Request: {request.method} {request.url.path}")

    # Wykonaj request
    response = await call_next(request)

    # Oblicz czas wykonania
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Loguj odpowiedź
    logger.info(
        f"✅ Response: {request.method} {request.url.path} "
        f"[Status: {response.status_code}] [Time: {process_time:.3f}s]"
    )

    return response


# Startup event
@app.on_event("startup")
async def startup_event():
    """Wykonywane przy starcie aplikacji"""
    logger.info("🚀 TamteKlipy API startuje...")
    logger.info("📚 Dokumentacja dostępna na: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Wykonywane przy zamykaniu aplikacji"""
    logger.info("🛑 TamteKlipy API wyłącza się...")


# Health check endpoint
@app.get("/")
async def root():
    """Podstawowy endpoint do sprawdzenia czy API działa"""
    return {
        "message": "TamteKlipy API działa!",
        "version": "0.1.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check dla monitoringu"""
    return {"status": "healthy"}


# Rejestracja routerów (odkomentujemy jak będą gotowe)
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(clips.router, prefix="/api/clips", tags=["clips"])
# app.include_router(awards.router, prefix="/api/awards", tags=["awards"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload podczas developmentu
    )
