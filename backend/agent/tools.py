"""
FinAgent — Agent Tools
Six tools the autonomous agent can use during plan→act→observe cycles.
Each tool returns a structured result dict.
"""
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend import models


def _get_user_transactions_df(db: Session, user_id: int, days: int = 90) -> pd.DataFrame:
    """Helper to load recent transactions into DataFrame."""
    cutoff = datetime.now() - timedelta(days=days)
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.date >= cutoff,
        )
        .order_by(models.Transaction.date.desc())
        .all()
    )
    if not txns:
        # Fallback to the latest available transactions for this user if cutoff returns nothing
        txns = (
            db.query(models.Transaction)
            .filter(models.Transaction.user_id == user_id)
            .order_by(models.Transaction.date.desc())
            .limit(200)
            .all()
        )
        if not txns:
            return pd.DataFrame()

    return pd.DataFrame([{
        "id": t.id,
        "date": t.date,
        "description": t.description,
        "amount": t.amount,
        "category": t.category or t.ml_category or "Other",
        "anomaly_score": t.anomaly_score or 0,
        "anomaly_label": t.anomaly_label,
        "anomaly_explanation": t.anomaly_explanation,
        "is_subscription": t.is_subscription,
    } for t in txns])


# ─── Tool 1: Get Transactions ─────────────────────────────────────────────────

def get_transactions(
    db: Session,
    user_id: int,
    days: int = 30,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve and summarize transaction data.

    Args:
        db: DB session
        user_id: Current user's ID
        days: Number of days to look back
        category: Optional category filter

    Returns:
        Dict with summary stats and top transactions
    """
    df = _get_user_transactions_df(db, user_id, days=days)
    if df.empty:
        return {"error": "No transactions found", "days": days}

    if category:
        df = df[df["category"].str.lower() == category.lower()]
        if df.empty:
            return {"error": f"No transactions found in category: {category}", "days": days}

    expenses = df[df["amount"] < 0]
    income = df[df["amount"] > 0]

    top_expenses = expenses.nsmallest(5, "amount")[["date", "description", "amount", "category"]].copy()
    top_expenses["amount"] = top_expenses["amount"].apply(lambda x: f"₹{abs(x):,.2f}")
    top_expenses["date"] = top_expenses["date"].apply(lambda d: d.strftime("%b %d") if hasattr(d, "strftime") else str(d))

    by_category = expenses.groupby("category")["amount"].sum().abs().sort_values(ascending=False)

    return {
        "period": f"Last {days} days",
        "total_income": round(income["amount"].sum(), 2),
        "total_expenses": round(expenses["amount"].abs().sum(), 2),
        "net_savings": round(income["amount"].sum() + expenses["amount"].sum(), 2),
        "savings_rate": round(
            (income["amount"].sum() + expenses["amount"].sum()) / income["amount"].sum() * 100
            if income["amount"].sum() > 0 else 0, 1
        ),
        "transaction_count": len(df),
        "top_expenses": top_expenses.to_dict("records"),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "category_filter": category,
    }


# ─── Tool 2: Get Anomalies ────────────────────────────────────────────────────

def get_anomalies(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Return recent anomalous transactions with explanations.
    """
    df = _get_user_transactions_df(db, user_id, days=days)
    if df.empty:
        return {"anomalies": [], "count": 0}

    anomalies = df[df["anomaly_label"] == True].copy()
    if anomalies.empty:
        return {"anomalies": [], "count": 0, "message": "No anomalies detected in this period. ✅"}

    result = []
    for _, row in anomalies.iterrows():
        result.append({
            "date": row["date"].strftime("%b %d, %Y") if hasattr(row["date"], "strftime") else str(row["date"]),
            "merchant": row["description"],
            "amount": f"₹{abs(row['amount']):,.2f}",
            "category": row["category"],
            "anomaly_score": round(row["anomaly_score"], 2),
            "explanation": row["anomaly_explanation"] or "Unusual transaction pattern.",
        })

    return {
        "anomalies": result,
        "count": len(result),
        "period": f"Last {days} days",
    }


# ─── Tool 3: Forecast Spending ────────────────────────────────────────────────

def forecast_spending(db: Session, user_id: int, horizon_days: int = 30) -> Dict[str, Any]:
    """
    Forecast spending for next N days.
    """
    df = _get_user_transactions_df(db, user_id, days=90)
    if df.empty:
        return {"error": "Not enough data to forecast"}

    from backend.ml.forecaster import get_forecaster
    forecaster = get_forecaster()
    forecast = forecaster.forecast(df, horizon_days=horizon_days)
    return forecast


# ─── Tool 4: Check Goal ───────────────────────────────────────────────────────

def check_goal(db: Session, user_id: int, goal_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Check progress toward savings goals.
    Returns all goals or a specific one.
    """
    query = db.query(models.Goal).filter(models.Goal.user_id == user_id)
    if goal_id:
        query = query.filter(models.Goal.id == goal_id)
    goals = query.all()

    if not goals:
        return {"goals": [], "message": "No savings goals set up yet."}

    result = []
    for g in goals:
        progress_pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
        remaining = g.target_amount - g.current_amount

        if g.monthly_contribution > 0 and remaining > 0:
            months_to_goal = remaining / g.monthly_contribution
        else:
            months_to_goal = None

        result.append({
            "id": g.id,
            "name": g.name,
            "target": f"₹{g.target_amount:,.0f}",
            "saved": f"₹{g.current_amount:,.0f}",
            "progress_pct": round(progress_pct, 1),
            "remaining": f"₹{max(0, remaining):,.0f}",
            "monthly_contribution": f"₹{g.monthly_contribution:,.0f}",
            "months_to_goal": round(months_to_goal, 1) if months_to_goal else "N/A",
            "target_date": g.target_date.strftime("%b %Y") if g.target_date else None,
            "is_completed": g.is_completed,
        })

    return {"goals": result, "count": len(result)}


# ─── Tool 5: Calculate ────────────────────────────────────────────────────────

def calculate(expression: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Safe financial calculator.
    Supports: basic arithmetic, percentage calculations.
    Context can contain named variables (e.g., {"income": 85000}).
    """
    import re
    allowed_pattern = r'^[\d\s\+\-\*\/\.\(\)\%]+$'
    
    # Substitute named variables from context
    expr = expression
    if context:
        for key, val in context.items():
            expr = expr.replace(key, str(val))

    # Remove % by dividing by 100
    expr = re.sub(r'(\d+(?:\.\d+)?)\%', r'(\1/100)', expr)

    if not re.match(allowed_pattern.replace(r'\%', ''), expr.replace(' ', '').replace('(', '').replace(')', '')):
        return {"error": "Invalid expression. Only arithmetic operators allowed."}

    try:
        result = eval(expr, {"__builtins__": {}})
        return {
            "expression": expression,
            "result": round(float(result), 2),
            "formatted": f"₹{result:,.2f}" if result > 100 else str(round(result, 4)),
        }
    except Exception as e:
        return {"error": f"Calculation error: {str(e)}"}


# ─── Tool 6: Search Knowledge ─────────────────────────────────────────────────

def search_knowledge(query: str, n_results: int = 3) -> Dict[str, Any]:
    """
    Search the financial knowledge base (tax rules, budgeting, investing, etc.)
    Returns relevant text chunks with sources.
    """
    from backend.rag.knowledge_loader import retrieve
    results = retrieve(query, n_results=n_results)

    if not results:
        return {"chunks": [], "message": "No relevant knowledge found. Answering from general knowledge."}

    return {
        "chunks": [
            {"text": text[:400], "source": source, "relevance": round(score, 3)}
            for text, source, score in results
        ],
        "count": len(results),
    }


# ─── Tool 7: Get Subscriptions ───────────────────────────────────────────────

def get_subscriptions(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Retrieve recurring subscriptions, bills, and monthly recurring impact.
    """
    from backend.ml.subscription_detector import get_subscription_detector
    df = _get_user_transactions_df(db, user_id, days=180)
    if df.empty:
        return {"subscriptions": [], "count": 0, "message": "No transactions available to detect subscriptions."}

    detector = get_subscription_detector()
    subs = detector.detect(df)

    # Also check if any transactions are marked with is_subscription == True
    explicit_subs = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id, models.Transaction.is_subscription == True)
        .all()
    )
    seen_merchants = {s["merchant"].strip().lower() for s in subs}
    for es in explicit_subs:
        m_key = es.description.strip().lower()
        if m_key not in seen_merchants:
            seen_merchants.add(m_key)
            interval = es.subscription_interval_days or 30
            subs.append({
                "merchant": es.description,
                "category": es.category or "Utilities & Bills",
                "amount": round(abs(es.amount), 2),
                "interval_days": interval,
                "monthly_cost": round(abs(es.amount) * (30 / interval), 2),
                "occurrences": 1,
                "last_charge": es.date,
                "next_expected": es.date + timedelta(days=interval),
                "confidence": "high",
            })

    user_obj = db.query(models.User).filter(models.User.id == user_id).first()
    income = user_obj.monthly_income if user_obj and user_obj.monthly_income else 50000.0
    creep = detector.subscription_creep_score(subs, income)

    return {
        "subscriptions": subs,
        "count": len(subs),
        "total_monthly": creep.get("total_monthly_subscriptions", sum(s["monthly_cost"] for s in subs)),
        "creep_analysis": creep,
    }


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "get_transactions": {
        "fn": get_transactions,
        "description": "Get spending summary and transaction data for a given period",
        "params": ["days (int, default 30)", "category (str, optional)"],
        "requires_db": True,
    },
    "get_subscriptions": {
        "fn": get_subscriptions,
        "description": "Get list of recurring subscriptions and auto-debit bills",
        "params": [],
        "requires_db": True,
    },
    "get_anomalies": {
        "fn": get_anomalies,
        "description": "Get list of anomalous/suspicious transactions with explanations",
        "params": ["days (int, default 30)"],
        "requires_db": True,
    },
    "forecast_spending": {
        "fn": forecast_spending,
        "description": "Forecast future spending for next N days",
        "params": ["horizon_days (int, default 30)"],
        "requires_db": True,
    },
    "check_goal": {
        "fn": check_goal,
        "description": "Check progress toward savings goals",
        "params": ["goal_id (int, optional)"],
        "requires_db": True,
    },
    "calculate": {
        "fn": calculate,
        "description": "Perform financial calculations (arithmetic, percentages)",
        "params": ["expression (str)", "context (dict, optional)"],
        "requires_db": False,
    },
    "search_knowledge": {
        "fn": search_knowledge,
        "description": "Search financial knowledge base for tax rules, budgeting strategies, etc.",
        "params": ["query (str)", "n_results (int, default 3)"],
        "requires_db": False,
    },
}
