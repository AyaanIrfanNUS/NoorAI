"""
NoorAI Backend - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "NoorAI"}