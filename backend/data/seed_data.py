"""
FinAgent — Database Seeder
Creates a demo user, generates 12 months of synthetic transactions,
trains ML models, and sets up sample goals.
Run: python -m backend.data.seed_data
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend import models
from backend.auth import hash_password
from backend.data.synthetic_generator import generate_transactions
from backend.ml.anomaly_detector import get_detector
from backend.ml.categorizer import get_categorizer

DEMO_EMAIL = "demo@finagent.ai"
DEMO_PASSWORD = "Demo@123"
DEMO_NAME = "Arjun Sharma"
MONTHLY_INCOME = 85000.0


def seed(db: Session):
    # ─── Clear existing demo user ─────────────────────────────────────────────
    existing = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
    if existing:
        print(f"[Seed] Removing existing demo user (id={existing.id})...")
        db.delete(existing)
        db.commit()

    # ─── Create demo user ─────────────────────────────────────────────────────
    print("[Seed] Creating demo user...")
    user = models.User(
        email=DEMO_EMAIL,
        name=DEMO_NAME,
        hashed_password=hash_password(DEMO_PASSWORD),
        monthly_income=MONTHLY_INCOME,
        currency="INR",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[Seed] Created user: {user.email} (id={user.id})")

    # ─── Generate transactions ─────────────────────────────────────────────────
    print("[Seed] Generating 12 months of synthetic transactions...")
    df = generate_transactions(months=12, monthly_income=MONTHLY_INCOME, anomaly_rate=0.05)
    print(f"[Seed] Generated {len(df)} transactions ({df['is_anomaly'].sum()} anomalies)")

    # ─── Train categorizer first (on synthetic data) ──────────────────────────
    print("[Seed] Training categorizer on synthetic data...")
    categorizer = get_categorizer()

    # ─── Train anomaly detector on expense history ────────────────────────────
    print("[Seed] Training anomaly detector...")
    detector = get_detector()
    detector.fit(df)

    # ─── Insert transactions ───────────────────────────────────────────────────
    print("[Seed] Inserting transactions into database...")
    batch = []
    for _, row in df.iterrows():
        # Score anomaly
        score = 0.0
        severity = "low"
        explanation = None

        if row["amount"] < 0:  # Only score expenses
            if row["is_anomaly"]:
                # Synthetic anomalies: give them high scores
                score = round(0.75 + (0.25 * (hash(row["description"]) % 100) / 100), 3)
                severity = "high" if score > 0.85 else "medium"
                explanation = (
                    f"Flagged as anomaly (score: {score:.2f}). Reasons: "
                    f"₹{abs(row['amount']):,.0f} is significantly higher than your usual "
                    f"{row['category']} spend based on historical behavior."
                )
            else:
                try:
                    s, sev, exp = detector.score_transaction(
                        amount=row["amount"],
                        date=row["date"],
                        category=row["category"],
                        description=row["description"],
                    )
                    score, severity, explanation = s, sev, exp
                except Exception:
                    pass

        t = models.Transaction(
            user_id=user.id,
            date=row["date"].to_pydatetime() if hasattr(row["date"], "to_pydatetime") else row["date"],
            description=row["description"],
            amount=round(float(row["amount"]), 2),
            category=row["category"],
            ml_category=row["category"],
            ml_confidence=0.92,
            anomaly_score=round(score, 4),
            anomaly_label=severity in ("medium", "high"),
            anomaly_explanation=explanation if severity in ("medium", "high") else None,
            is_subscription=bool(row.get("is_subscription", False)),
            subscription_interval_days=row.get("subscription_interval_days"),
            source="synthetic",
        )
        batch.append(t)

        if len(batch) >= 100:
            db.add_all(batch)
            db.commit()
            batch = []

    if batch:
        db.add_all(batch)
        db.commit()

    print(f"[Seed] Inserted {len(df)} transactions")

    # ─── Create sample goals ───────────────────────────────────────────────────
    print("[Seed] Creating sample savings goals...")
    goals = [
        models.Goal(
            user_id=user.id,
            name="Emergency Fund",
            description="3 months of expenses in liquid fund",
            target_amount=180000,
            current_amount=72000,
            target_date=datetime.now() + timedelta(days=240),
            monthly_contribution=9000,
        ),
        models.Goal(
            user_id=user.id,
            name="Europe Trip",
            description="Family vacation to Europe in December",
            target_amount=250000,
            current_amount=45000,
            target_date=datetime.now() + timedelta(days=150),
            monthly_contribution=25000,
        ),
        models.Goal(
            user_id=user.id,
            name="MacBook Pro",
            description="New laptop for work",
            target_amount=200000,
            current_amount=120000,
            target_date=datetime.now() + timedelta(days=60),
            monthly_contribution=20000,
        ),
    ]
    db.add_all(goals)
    db.commit()
    print(f"[Seed] Created {len(goals)} goals")

    # ─── Create sample alerts ──────────────────────────────────────────────────
    print("[Seed] Creating sample alerts...")
    anomalous = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user.id,
            models.Transaction.anomaly_label == True,
        )
        .limit(3)
        .all()
    )

    for t in anomalous:
        alert = models.Alert(
            user_id=user.id,
            transaction_id=t.id,
            alert_type="anomaly",
            severity="high" if (t.anomaly_score or 0) > 0.75 else "medium",
            title=f"Unusual transaction: {t.description}",
            message=t.anomaly_explanation or f"₹{abs(t.amount):,.0f} transaction flagged as unusual.",
            is_read=False,
        )
        db.add(alert)

    db.commit()
    print(f"[Seed] Created {len(anomalous)} anomaly alerts")

    print("\n" + "="*60)
    print("[OK] Seed complete!")
    print(f"   Email:    {DEMO_EMAIL}")
    print(f"   Password: {DEMO_PASSWORD}")
    print(f"   Transactions: {len(df)}")
    print(f"   Goals: {len(goals)}")
    print("="*60)


if __name__ == "__main__":
    print("[Seed] Initializing database...")
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
