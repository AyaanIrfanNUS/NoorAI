"""
NoorAI Backend - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import auth
from app.api import prayers
from app.api import zakat
from app.api import users
from app.api import prayer_times
from app.api import chat
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
import sentry_sdk
from app.api import finder


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    On startup, tests the database connection.
    """
    from sqlalchemy import text
    from app.core.database import engine

    if settings.APP_ENV == "production":
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )

    print("NoorAI backend is starting up...")

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Database connection test result:", result.scalar())

    yield
    print("NoorAI backend is shutting down...")


app = FastAPI(
    title="NoorAI API",
    description="Backend API for the NoorAI Islamic companion app",
    version="0.1.0",
    lifespan=lifespan,
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.APP_ENV == "production":
        sentry_sdk.capture_exception(exc)
    else:
        # In development, raise as normal so the full traceback
        # appears in the terminal for debugging.
        raise exc

    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again later."},
    )

if settings.APP_ENV == "production":
    cors_origins = [settings.FRONTEND_URL]
else:
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(prayers.router)
app.include_router(zakat.router)
app.include_router(users.router)
app.include_router(prayer_times.router)
app.include_router(chat.router)
app.include_router(finder.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "NoorAI"}