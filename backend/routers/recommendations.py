"""
FinAgent — Recommendations Router
Retrieve, action, and delete recommendations.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def list_recommendations(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List recommendations for the current user."""
    recs = (
        db.query(models.Recommendation)
        .filter(models.Recommendation.user_id == current_user.id)
        .order_by(models.Recommendation.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "message": r.message,
                "priority": r.priority,
                "is_actioned": r.is_actioned,
                "created_at": r.created_at.isoformat(),
                "alert_id": r.alert_id,
            }
            for r in recs
        ],
        "total": len(recs),
        "unactioned_count": sum(1 for r in recs if not r.is_actioned),
    }


@router.post("/{rec_id}/action")
def mark_actioned(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark a recommendation as actioned/read."""
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id,
        models.Recommendation.user_id == current_user.id,
    ).first()
    
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found."
        )
        
    rec.is_actioned = True
    db.commit()
    return {"success": True}


@router.delete("/{rec_id}")
def delete_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a recommendation."""
    rec = db.query(models.Recommendation).filter(
        models.Recommendation.id == rec_id,
        models.Recommendation.user_id == current_user.id,
    ).first()
    
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found."
        )
        
    db.delete(rec)
    db.commit()
    return {"success": True}
