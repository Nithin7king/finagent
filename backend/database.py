"""
FinAgent — Database setup
SQLAlchemy with PostgreSQL support and automatic local SQLite fallback.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finagent")


def create_resilient_engine():
    """Attempt connection to configured database; fallback to SQLite if unreachable."""
    if DATABASE_URL.startswith("sqlite"):
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

    try:
        test_engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        with test_engine.connect() as conn:
            pass
        return test_engine
    except Exception as e:
        print(f"[Database] Notice: PostgreSQL at {DATABASE_URL.split('@')[-1]} not reachable ({e}).")
        print("[Database] Using local SQLite database (sqlite:///./finagent.db) for offline operation.")
        return create_engine("sqlite:///./finagent.db", connect_args={"check_same_thread": False}, echo=False)


engine = create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency: yields a DB session, closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables on startup."""
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
