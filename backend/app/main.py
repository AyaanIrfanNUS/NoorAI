"""
NoorAI Backend - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.api import prayers
from app.api import zakat
from app.api import users
from app.api import prayer_times
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    On startup, tests the database connection.
    """
    from sqlalchemy import text
    from app.core.database import engine

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

app.include_router(auth.router)
app.include_router(prayers.router)
app.include_router(zakat.router)
app.include_router(users.router)
app.include_router(prayer_times.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "NoorAI"}