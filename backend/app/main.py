"""
NoorAI Backend - Main Application Entry Point

This is the front door of our backend. Starting this file with uvicorn
brings the whole API to life.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events run code on startup and shutdown.

    Right now we just print messages so we can see it working.
    In Step 3, we will add a real database connection test here.
    """
    print("NoorAI backend is starting up...")
    yield
    print("NoorAI backend is shutting down...")


app = FastAPI(
    title="NoorAI API",
    description="Backend API for the NoorAI Islamic companion app",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - lets our frontend talk to this backend.
# In development, our React frontend runs on localhost:5173 (Vite default port).
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
    """
    Simple health check endpoint.

    Returns a small JSON object confirming the API is alive.
    Useful for testing, and later for deployment platforms (like Railway)
    to check whether our app is running correctly.
    """
    return {"status": "ok", "app": "NoorAI"}