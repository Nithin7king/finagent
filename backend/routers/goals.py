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


@router.get("/{goal_id}/recommendations")
def get_goal_recommendations(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Recommender Agent: Generate transaction-grounded recommendations
    to reach this specific goal as early as possible.
    """
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id,
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    target = float(goal.target_amount)
    current = float(goal.current_amount)
    remaining = max(0.0, target - current)

    if remaining <= 0:
        return {
            "goal_id": goal.id,
            "goal_name": goal.name,
            "remaining_amount": 0.0,
            "is_completed": True,
            "current_timeline_months": 0.0,
            "optimized_timeline_months": 0.0,
            "months_saved": 0.0,
            "acceleration_pct": 100.0,
            "recommendations": [
                {
                    "id": "completed",
                    "type": "completion",
                    "title": "🎉 Goal Already Achieved!",
                    "message": f"You have already reached the target of ₹{target:,.0f} for '{goal.name}'. Time to set your next milestone!",
                    "impact": "100% Complete",
                    "monthly_savings": 0.0,
                    "priority": "low",
                    "badge": "Completed",
                }
            ],
        }

    # Fetch recent transactions
    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.date.desc())
        .limit(200)
        .all()
    )

    income = current_user.monthly_income if current_user.monthly_income and current_user.monthly_income > 0 else 60000.0

    # Categorize expenses
    cat_spend = {}
    total_expenses = 0.0
    for t in txns:
        if t.amount < 0:
            amt = abs(float(t.amount))
            cat = t.category or "Others"
            cat_spend[cat] = cat_spend.get(cat, 0.0) + amt
            total_expenses += amt

    # Baseline monthly contribution
    base_monthly = float(goal.monthly_contribution) if goal.monthly_contribution and goal.monthly_contribution > 0 else max(1500.0, income * 0.08)
    current_months = round(remaining / base_monthly, 1)

    # Discretionary analysis (Food & Dining, Shopping, Entertainment)
    discretionary_categories = ["Food & Dining", "Food", "Shopping", "Entertainment", "Dining"]
    top_cat = "Food & Dining"
    top_spend = 0.0
    for c in discretionary_categories:
        if cat_spend.get(c, 0.0) > top_spend:
            top_spend = cat_spend[c]
            top_cat = c

    if top_spend == 0.0:
        top_cat = "Discretionary"
        top_spend = max(5000.0, income * 0.15)

    # 1. Discretionary trim recommendation (15-20%)
    cut_rate = 0.20
    savings_1 = round(top_spend * cut_rate, -1)
    if savings_1 < 500.0:
        savings_1 = 1200.0
    new_timeline_1 = round(remaining / (base_monthly + savings_1), 1)
    months_saved_1 = round(max(0.2, current_months - new_timeline_1), 1)

    # 2. Subscription audit recommendation
    total_sub_spend = 0.0
    sub_count = 0
    try:
        from backend.ml.subscription_detector import get_subscription_detector
        import pandas as pd
        if txns:
            df = pd.DataFrame([{
                "date": t.date,
                "description": t.description,
                "amount": t.amount,
                "category": t.category or "Other"
            } for t in txns])
            sub_detector = get_subscription_detector()
            subs = sub_detector.detect(df)
            sub_count = len(subs)
            total_sub_spend = sum(abs(s.get("amount", 0.0)) for s in subs)
    except Exception:
        pass

    if total_sub_spend > 0:
        sub_savings = round(total_sub_spend * 0.5, -1)
        if sub_savings < 400.0:
            sub_savings = total_sub_spend
    else:
        sub_savings = 1000.0

    new_timeline_2 = round(remaining / (base_monthly + sub_savings), 1)
    months_saved_2 = round(max(0.2, current_months - new_timeline_2), 1)

    # 3. Salary day automated sweep (1st of month)
    monthly_surplus = max(0.0, income - (total_expenses / max(1, len(txns)/30)))
    sweep_amount = round(max(2000.0, min(income * 0.15, monthly_surplus * 0.4)), -2)
    new_timeline_3 = round(remaining / (base_monthly + sweep_amount), 1)
    months_saved_3 = round(max(0.2, current_months - new_timeline_3), 1)

    # Combined acceleration
    total_boost = savings_1 + (sub_savings * 0.6) + (sweep_amount * 0.5)
    optimized_months = round(remaining / (base_monthly + total_boost), 1)
    total_months_saved = round(max(0.3, current_months - optimized_months), 1)
    accel_pct = round(min(80.0, (total_months_saved / current_months) * 100), 1) if current_months > 0 else 0.0

    recommendations_list = [
        {
            "id": f"rec_{goal_id}_discretionary",
            "type": "spending_cut",
            "title": f"Trim {top_cat} by 20%",
            "message": f"Your recent {top_cat} spending was ~₹{top_spend:,.0f}. Trimming non-essential orders by 20% frees up ₹{savings_1:,.0f}/month to direct here.",
            "impact": f"Reaches goal {months_saved_1} months sooner",
            "monthly_savings": savings_1,
            "priority": "high",
            "badge": "⚡ High Impact",
        },
        {
            "id": f"rec_{goal_id}_subscriptions",
            "type": "subscription_audit",
            "title": f"Audit {sub_count if sub_count > 0 else 'Recurring'} Subscriptions",
            "message": f"{f'You have {sub_count} recurring subscriptions totaling ₹{total_sub_spend:,.0f}/month.' if total_sub_spend > 0 else 'Reviewing recurring app & media memberships'} Pausing 1 or 2 unused services redirects ₹{sub_savings:,.0f}/month toward this milestone.",
            "impact": f"Saves {months_saved_2} months",
            "monthly_savings": sub_savings,
            "priority": "medium",
            "badge": "🔄 Recurring",
        },
        {
            "id": f"rec_{goal_id}_salary_sweep",
            "type": "salary_sweep",
            "title": "Automate Salary Day Sweep on 1st",
            "message": f"Schedule an automatic transfer of ₹{sweep_amount:,.0f} directly on salary day before discretionary expenses begin. Paying your goal first guarantees on-time arrival.",
            "impact": f"Saves {months_saved_3} months",
            "monthly_savings": sweep_amount,
            "priority": "high",
            "badge": "🎯 Recommended",
        },
    ]

    return {
        "goal_id": goal.id,
        "goal_name": goal.name,
        "target_amount": target,
        "current_amount": current,
        "remaining_amount": remaining,
        "base_monthly_contribution": base_monthly,
        "current_timeline_months": current_months,
        "optimized_timeline_months": optimized_months,
        "months_saved": total_months_saved,
        "acceleration_pct": accel_pct,
        "recommendations": recommendations_list,
    }
