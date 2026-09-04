import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.database import init_db
from server.routers import events


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Calendar Service",
    description="Microservice for managing calendar events",
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS Configuration ────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────

app.include_router(events.router)


# ── Root Endpoint ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "Calendar Service is running",
        "service": "calendar",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Global health check."""
    return {"status": "ok", "service": "calendar"}
