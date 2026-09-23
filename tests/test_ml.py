import pytest
import pandas as pd
from datetime import datetime, timedelta

from backend.ml.anomaly_detector import get_detector
from backend.ml.subscription_detector import get_subscription_detector


def test_anomaly_detector_scoring():
    """Verify IsolationForest anomaly detector scores transactions correctly."""
    detector = get_detector()
    score, severity, explanation = detector.score_transaction(
        amount=-150.0,
        date=datetime.utcnow(),
        category="Food & Dining",
        description="Chai Point"
    )
    assert isinstance(score, float)
    assert severity in ("low", "medium", "high")
    assert isinstance(explanation, str)


def test_subscription_detector_and_creep():
    """Verify recurring subscription detection and subscription creep scoring."""
    sub_detector = get_subscription_detector()
    now = datetime.utcnow()
    
    # Create sample recurring transactions
    data = [
        {"date": now - timedelta(days=60), "description": "Netflix Subscription", "amount": -499.0, "category": "Entertainment"},
        {"date": now - timedelta(days=30), "description": "Netflix Subscription", "amount": -499.0, "category": "Entertainment"},
        {"date": now, "description": "Netflix Subscription", "amount": -499.0, "category": "Entertainment"},
        {"date": now - timedelta(days=40), "description": "Gym Membership", "amount": -2000.0, "category": "Health"},
        {"date": now - timedelta(days=10), "description": "Gym Membership", "amount": -2000.0, "category": "Health"},
    ]
    df = pd.DataFrame(data)
    subs = sub_detector.detect(df)
    assert isinstance(subs, list)
    
    creep = sub_detector.subscription_creep_score(subs, monthly_income=50000.0)
    assert "total_monthly_subscriptions" in creep
    assert "risk_level" in creep
    assert "insight" in creep
