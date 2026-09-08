from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from . import models  # noqa: F401 — needed to register models with Base

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Earnings Call Analyzer",
    description="AI-powered earnings call sentiment analysis using Google Gemini",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check — confirms app is running and keys are loaded."""
    return {
        "status": "ok",
        "env": settings.app_env,
        "alpha_vantage_set": bool(settings.alpha_vantage_api_key),
        "gemini_set": bool(settings.google_gemini_api_key),
        "database": "connected"
    }