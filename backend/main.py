"""
FinAgent — FastAPI Application Entry Point
Wires up all routers, CORS, startup events, and auth endpoints.
"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import get_db, init_db, get_db_status
from backend.auth import register_user, login_user, get_current_user
from backend import schemas, models
from backend.routers import transactions, analytics, chat, goals, alerts, profile, recommendations, kyc
from backend.rag.knowledge_loader import load_knowledge_base

load_dotenv()

app = FastAPI(
    title="MYFY.AI API",

    description="AI-Powered Personal Finance Assistant — ML, RAG, and Autonomous Agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(goals.router)
app.include_router(alerts.router)
app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(kyc.router)



# ─── Auth Endpoints ───────────────────────────────────────────────────────────
@app.post("/auth/register", response_model=schemas.TokenResponse, tags=["auth"])
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    return register_user(data, db)


@app.post("/auth/login", response_model=schemas.TokenResponse, tags=["auth"])
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and receive a JWT token."""
    return login_user(data, db)


@app.get("/auth/me", response_model=schemas.UserOut, tags=["auth"])
def me(current_user: models.User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    """Initialize DB tables, load knowledge base, and start background jobs."""
    print("[FinAgent] Initializing database...")
    init_db()
    print("[FinAgent] Loading knowledge base into Chroma...")
    try:
        load_knowledge_base()
    except Exception as e:
        print(f"[FinAgent] Warning: Knowledge base load failed: {e}")
    print("[FinAgent] Starting background scheduler...")
    try:
        from backend.scheduler.jobs import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[FinAgent] Warning: Scheduler failed to start: {e}")
    print("[FinAgent] Ready! Visit http://localhost:8000/docs")


@app.on_event("shutdown")
def shutdown():
    """Stop APScheduler gracefully."""
    try:
        from backend.scheduler.jobs import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    db_status = get_db_status()
    is_healthy = db_status.get("connected", False)
    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "FinAgent API",
        "version": "1.0.0",
        "database": db_status,
    }


@app.get("/", tags=["system"])
def root():
    return {
        "message": "Welcome to FinAgent API",
        "docs": "/docs",
        "health": "/health",
    }
