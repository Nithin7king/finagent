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
        print(f"[Database] Configured for SQLite: {DATABASE_URL}")
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

    try:
        from sqlalchemy import text
        test_engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        with test_engine.connect() as conn:
            res = conn.execute(text("SELECT current_database(), current_user;")).fetchone()
            db_name = res[0] if res else test_engine.url.database
            db_user = res[1] if res else test_engine.url.username
            print(f"[Database] [SUCCESS] Connected to PostgreSQL successfully!")
            print(f"[Database] Host: {test_engine.url.host}:{test_engine.url.port} | Database: '{db_name}' | User: '{db_user}'")
        return test_engine
    except Exception as e:
        print(f"[Database] [WARNING] PostgreSQL at {DATABASE_URL.split('@')[-1]} not reachable ({e}).")
        print("[Database] Falling back to local SQLite database (sqlite:///./finagent.db) for offline operation.")
        return create_engine("sqlite:///./finagent.db", connect_args={"check_same_thread": False}, echo=False)


engine = create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_status():
    """Returns database connection status and dialect details."""
    from sqlalchemy import text
    dialect_name = engine.dialect.name
    is_pg = dialect_name == "postgresql"
    try:
        with engine.connect() as conn:
            if is_pg:
                res = conn.execute(text("SELECT current_database(), current_user, version();")).fetchone()
                return {
                    "connected": True,
                    "engine": "postgresql",
                    "database": res[0] if res else str(engine.url.database),
                    "user": res[1] if res else str(engine.url.username),
                    "host": f"{engine.url.host}:{engine.url.port}",
                    "is_postgres": True,
                    "version": res[2].split(",")[0] if res else "unknown",
                }
            else:
                return {
                    "connected": True,
                    "engine": "sqlite",
                    "database": str(engine.url.database),
                    "is_postgres": False,
                    "notice": "Running on SQLite fallback. PostgreSQL is not connected.",
                }
    except Exception as e:
        return {
            "connected": False,
            "engine": dialect_name,
            "error": str(e),
            "is_postgres": False,
        }


def get_db():
    """Dependency: yields a DB session, closes it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables on startup and apply column migrations."""
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safe migration for newly added user KYC columns
    from sqlalchemy import text
    columns_to_add = [
        ("pan_number", "VARCHAR"),
        ("pan_verified", "BOOLEAN DEFAULT FALSE"),
        ("aadhaar_last4", "VARCHAR(4)"),
        ("digilocker_id", "VARCHAR"),
        ("digilocker_verified", "BOOLEAN DEFAULT FALSE"),
        ("kyc_status", "VARCHAR DEFAULT 'pending'"),
        ("kyc_completed_at", "TIMESTAMP"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                if engine.dialect.name == "postgresql":
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS "{col_name}" {col_type};'))
                else:
                    # SQLite fallback
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN "{col_name}" {col_type};'))
                conn.commit()
            except Exception:
                # Column might already exist in SQLite or failed gracefully
                pass


