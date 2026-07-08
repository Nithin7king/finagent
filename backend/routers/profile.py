"""
FinAgent — Profile/Settings Router
Update user profile: name, income, currency, password.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from backend.database import get_db
from backend.auth import get_current_user, hash_password, verify_password
from backend import models

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    monthly_income: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


@router.put("")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update user profile fields."""
    if data.name is not None:
        current_user.name = data.name
    if data.monthly_income is not None:
        current_user.monthly_income = data.monthly_income
    if data.currency is not None:
        current_user.currency = data.currency

    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "monthly_income": current_user.monthly_income,
        "currency": current_user.currency,
    }


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Change the current user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"success": True, "message": "Password changed successfully"}


@router.get("/stats")
def user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return account statistics for the settings page."""
    from datetime import datetime, timedelta

    txn_count = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).count()

    goal_count = db.query(models.Goal).filter(
        models.Goal.user_id == current_user.id
    ).count()

    alert_count = db.query(models.Alert).filter(
        models.Alert.user_id == current_user.id
    ).count()

    # Member since
    days_member = (datetime.utcnow() - current_user.created_at).days

    return {
        "transaction_count": txn_count,
        "goal_count": goal_count,
        "alert_count": alert_count,
        "days_member": days_member,
        "member_since": current_user.created_at.strftime("%b %Y"),
    }
