"""
FinAgent — Alerts Router
Retrieve, mark-as-read, and delete alerts/notifications.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List alerts/notifications for the current user."""
    q = (
        db.query(models.Alert)
        .filter(models.Alert.user_id == current_user.id)
        .order_by(models.Alert.created_at.desc())
    )
    if unread_only:
        q = q.filter(models.Alert.is_read == False)

    alerts = q.limit(limit).all()

    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
                "transaction_id": a.transaction_id,
            }
            for a in alerts
        ],
        "total": len(alerts),
        "unread_count": sum(1 for a in alerts if not a.is_read),
    }


@router.post("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark a single alert as read."""
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == current_user.id,
    ).first()
    if alert:
        alert.is_read = True
        db.commit()
    return {"success": True}


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark all alerts as read."""
    db.query(models.Alert).filter(
        models.Alert.user_id == current_user.id,
        models.Alert.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"success": True}


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete an alert."""
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == current_user.id,
    ).first()
    if alert:
        db.delete(alert)
        db.commit()
    return {"success": True}


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Fast endpoint for the sidebar badge."""
    count = db.query(models.Alert).filter(
        models.Alert.user_id == current_user.id,
        models.Alert.is_read == False,
    ).count()
    return {"unread_count": count}
