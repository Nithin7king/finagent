"""
FinAgent — Analytics Router
ML-powered insights: spending summary, anomalies, forecasts, subscriptions.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models
from backend.ml.forecaster import get_forecaster
from backend.ml.anomaly_detector import get_detector
from backend.ml.subscription_detector import get_subscription_detector
from backend.rag.engine import get_rag_engine

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_transactions_df(db: Session, user_id: int, days: int = 90) -> pd.DataFrame:
    cutoff = datetime.now() - timedelta(days=days)
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.date >= cutoff,
        )
        .order_by(models.Transaction.date.asc())
        .all()
    )
    if not txns:
        return pd.DataFrame()

    return pd.DataFrame([{
        "date": t.date,
        "description": t.description,
        "amount": t.amount,
        "category": t.category or t.ml_category or "Other",
        "anomaly_score": t.anomaly_score or 0,
        "anomaly_label": t.anomaly_label or False,
        "anomaly_explanation": t.anomaly_explanation,
        "is_subscription": t.is_subscription or False,
    } for t in txns])


@router.get("/summary")
def get_spending_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get spending summary: income, expenses, savings rate, by-category breakdown."""
    df = _get_transactions_df(db, current_user.id, days=days)

    if df.empty:
        return {
            "total_income": 0, "total_expenses": 0, "net_savings": 0,
            "savings_rate": 0, "by_category": {}, "period_days": days,
        }

    expenses = df[df["amount"] < 0]
    income = df[df["amount"] > 0]

    total_income = round(income["amount"].sum(), 2)
    total_expenses = round(expenses["amount"].abs().sum(), 2)
    net_savings = round(total_income - total_expenses, 2)
    savings_rate = round((net_savings / total_income * 100) if total_income > 0 else 0, 1)

    by_category = (
        expenses.groupby("category")["amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .round(2)
        .to_dict()
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "by_category": by_category,
        "period_days": days,
        "transaction_count": len(df),
    }


@router.get("/forecast")
def get_forecast(
    horizon_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Forecast spending for next N days."""
    df = _get_transactions_df(db, current_user.id, days=90)
    forecaster = get_forecaster()
    return forecaster.forecast(df, horizon_days=horizon_days)


@router.get("/spending-trend")
def get_spending_trend(
    months: int = Query(6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get month-by-month spending trend."""
    df = _get_transactions_df(db, current_user.id, days=months * 31)
    forecaster = get_forecaster()
    return {
        "trend": forecaster.spending_trend(df, months=months),
        "savings_rate_history": forecaster.savings_rate_history(df, months=months),
    }


@router.get("/anomalies")
def get_anomalies(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get all flagged anomalous transactions with explanations."""
    cutoff = datetime.now() - timedelta(days=days)
    anomalies = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.anomaly_label == True,
            models.Transaction.date >= cutoff,
        )
        .order_by(models.Transaction.anomaly_score.desc())
        .all()
    )

    return {
        "anomalies": [
            {
                "id": t.id,
                "date": t.date.strftime("%Y-%m-%d"),
                "description": t.description,
                "amount": t.amount,
                "category": t.category or "Other",
                "anomaly_score": round(t.anomaly_score or 0, 3),
                "explanation": t.anomaly_explanation or "Unusual transaction pattern.",
                "severity": (
                    "high" if (t.anomaly_score or 0) >= 0.75
                    else "medium" if (t.anomaly_score or 0) >= 0.50
                    else "low"
                ),
            }
            for t in anomalies
        ],
        "count": len(anomalies),
        "period_days": days,
    }


@router.get("/subscriptions")
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Detect recurring subscriptions and compute creep score."""
    df = _get_transactions_df(db, current_user.id, days=180)
    detector = get_subscription_detector()

    subscriptions = detector.detect(df)
    creep = detector.subscription_creep_score(subscriptions, current_user.monthly_income or 0)
    upcoming = detector.upcoming_bills(subscriptions, days_ahead=7)

    # Serialize datetimes
    for s in subscriptions:
        s["last_charge"] = s["last_charge"].strftime("%Y-%m-%d") if s.get("last_charge") else None
        s["next_expected"] = s["next_expected"].strftime("%Y-%m-%d") if s.get("next_expected") else None

    return {
        "subscriptions": subscriptions,
        "creep_analysis": creep,
        "upcoming_bills": upcoming,
    }


@router.post("/train-models")
def train_models(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger ML model training on user's transaction history.
    Call this after initial data load to personalize anomaly detection.
    """
    df = _get_transactions_df(db, current_user.id, days=365)

    if df.empty or len(df) < 20:
        return {"message": "Not enough data to train models. Add more transactions first.", "trained": False}

    detector = get_detector()
    detector.fit(df)

    return {
        "message": f"Models trained on {len(df)} transactions.",
        "trained": True,
        "expense_count": len(df[df["amount"] < 0]),
    }


@router.get("/what-if")
def what_if_simulator(
    category: str = Query(...),
    reduction_pct: float = Query(..., ge=0, le=100),
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    What-if simulator: How much would I save if I cut spending in a category by X%?
    """
    df = _get_transactions_df(db, current_user.id, days=90)

    if df.empty:
        return {"error": "No transaction data available"}

    expenses = df[df["amount"] < 0]
    cat_data = expenses[expenses["category"].str.lower() == category.lower()]

    if cat_data.empty:
        return {"error": f"No expenses found in category: {category}"}

    # Compute monthly equivalent (normalize to 30 days)
    period_factor = days / 30
    monthly_spend = cat_data["amount"].abs().sum() / period_factor

    savings = monthly_spend * (reduction_pct / 100)
    annual_savings = savings * 12

    return {
        "category": category,
        "current_monthly_spend": round(monthly_spend, 2),
        "reduction_pct": reduction_pct,
        "monthly_savings": round(savings, 2),
        "annual_savings": round(annual_savings, 2),
        "insight": (
            f"Cutting {category} by {reduction_pct:.0f}% saves ₹{savings:,.0f}/month "
            f"(₹{annual_savings:,.0f}/year). "
            f"That's enough to build an emergency fund of ₹{savings * 6:,.0f} in 6 months "
            f"or invest ₹{savings:,.0f}/month in SIPs."
        ),
    }
