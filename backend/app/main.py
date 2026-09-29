from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .database import Base, engine
from . import models  # noqa: F401 — needed to register models with Base
from .routers import calls, analyses, companies
from .services.claude_client import ClaudeAnalysisError
from .transcript_client import ProviderUnavailableError

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Earnings Call Analyzer",
    description="AI-powered earnings call sentiment analysis using Claude",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Vite dev server + deployed frontend(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(calls.router)
app.include_router(analyses.router)
app.include_router(companies.router)

def _status_code_for(message: str) -> int:
    lowered = message.lower()
    if "api limit reached" in lowered:
        return 429      # Too Many Requests
    if "invalid ticker" in lowered:
        return 400      # Bad Request
    if "no transcript found" in lowered:
        return 404      # Not Found
    return 400

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=_status_code_for(str(exc)),
        content={"detail": str(exc)},
    )


@app.exception_handler(ClaudeAnalysisError)
async def claude_error_handler(request: Request, exc: ClaudeAnalysisError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ProviderUnavailableError)
async def provider_error_handler(request: Request, exc: ProviderUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

@app.get("/health")
async def health():
    """Health check — confirms app is running and keys are loaded."""
    return {
        "status": "ok",
        "env": settings.app_env,
        "anthropic_set": bool(settings.anthropic_api_key),
        "equibles_set": bool(settings.equibles_api_key),
        "database": "connected"
    }