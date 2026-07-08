"""
FinAgent — Goals Router
CRUD for savings goals with progress tracking and AI recommendations.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models, schemas

router = APIRouter(prefix="/goals", tags=["goals"])


def _enrich_goal(goal: models.Goal) -> schemas.GoalOut:
    progress_pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    remaining = goal.target_amount - goal.current_amount

    if goal.monthly_contribution > 0 and remaining > 0:
        months_to_goal = remaining / goal.monthly_contribution
    else:
        months_to_goal = None

    return schemas.GoalOut(
        id=goal.id,
        name=goal.name,
        description=goal.description,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        monthly_contribution=goal.monthly_contribution,
        is_completed=goal.is_completed,
        progress_pct=round(progress_pct, 1),
        months_to_goal=round(months_to_goal, 1) if months_to_goal else None,
        created_at=goal.created_at,
    )


@router.get("", response_model=List[schemas.GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goals = (
        db.query(models.Goal)
        .filter(models.Goal.user_id == current_user.id)
        .order_by(models.Goal.created_at.desc())
        .all()
    )
    return [_enrich_goal(g) for g in goals]


@router.post("", response_model=schemas.GoalOut, status_code=201)
def create_goal(
    data: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = models.Goal(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        target_amount=data.target_amount,
        current_amount=data.current_amount or 0,
        target_date=data.target_date,
        monthly_contribution=data.monthly_contribution or 0,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _enrich_goal(goal)


@router.put("/{goal_id}", response_model=schemas.GoalOut)
def update_goal(
    goal_id: int,
    data: schemas.GoalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(goal, field, value)

    # Auto-mark complete if target reached
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    db.commit()
    db.refresh(goal)
    return _enrich_goal(goal)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()


class ContributionIn(BaseModel):
    amount: float


@router.post("/{goal_id}/contribute")
def contribute_to_goal(
    goal_id: int,
    data: ContributionIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a contribution to a goal."""
    amount = data.amount
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.current_amount = min(goal.current_amount + amount, goal.target_amount)
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    db.commit()
    db.refresh(goal)
    return {
        "message": f"Added ₹{amount:,.0f} to '{goal.name}'",
        "new_total": goal.current_amount,
        "progress_pct": round(goal.current_amount / goal.target_amount * 100, 1),
        "completed": goal.is_completed,
    }
