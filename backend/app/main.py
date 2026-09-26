"""
main.py
-------
FastAPI application entry point.
Registers CORS middleware, imports the database models so Alembic can detect them,
and defines the /health endpoint to verify the server and DB are reachable.
All deviation-specific routes will be added here in Phase 3.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
# Import models so Alembic's env.py can discover them via Base.metadata
import app.models  # noqa: F401

app = FastAPI(
    title="AIVOA.AI — Deviation Intake Module",
    description="AI-powered deviation intake for API manufacturing QA teams.",
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins during development so the React dev server can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """
    Returns 200 if the server is running and the database is reachable.
    Run this first after setup to confirm everything is wired correctly.
    """
    db.execute(text("SELECT 1"))   # lightweight DB ping
    return {"status": "ok", "database": "connected"}
