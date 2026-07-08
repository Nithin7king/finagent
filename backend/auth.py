"""
FinAgent — JWT Auth + bcrypt Password Hashing
Provides: register, login, token verification, user dependency
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import get_db
from backend import models, schemas

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "finagent-jwt-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

security = HTTPBearer()


# ─── Password Utils ───────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password with bcrypt (cost=12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ─── JWT Utils ────────────────────────────────────────────────────────────────

def create_token(user_id: int, email: str) -> str:
    """Create a signed JWT with 24-hour expiry."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


# ─── FastAPI Dependencies ─────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency: verify JWT and return the current User model."""
    payload = decode_token(credentials.credentials)
    user_id = int(payload["sub"])
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


# ─── Auth Operations ──────────────────────────────────────────────────────────

def register_user(data: schemas.UserRegister, db: Session) -> schemas.TokenResponse:
    """Register a new user. Raises 400 if email already exists."""
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    user = models.User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
        monthly_income=data.monthly_income or 0.0,
        currency=data.currency or "INR",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    return schemas.TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )


def login_user(data: schemas.UserLogin, db: Session) -> schemas.TokenResponse:
    """Login a user. Raises 401 on bad credentials."""
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = create_token(user.id, user.email)
    return schemas.TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )
