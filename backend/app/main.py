"""
TamteKlipy — Główny plik aplikacji FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    # Dodamy Cloudflare URL później
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Podstawowy endpoint do sprawdzenia, czy API działa"""
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
