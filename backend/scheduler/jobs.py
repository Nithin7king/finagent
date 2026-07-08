"""
FinAgent — APScheduler Background Jobs
Weekly digest, bill reminders, and anomaly scanning.
"""
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database import SessionLocal
from backend import models

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def _run_anomaly_scan():
    """
    Every 6 hours: scan latest transactions for anomalies.
    Creates alerts for newly flagged transactions.
    """
    db = SessionLocal()
    try:
        from backend.ml.anomaly_detector import get_detector
        import pandas as pd

        detector = get_detector()
        if detector.model is None:
            return

        cutoff = datetime.now() - timedelta(hours=6)
        recent_txns = (
            db.query(models.Transaction)
            .filter(
                models.Transaction.created_at >= cutoff,
                models.Transaction.anomaly_label.is_(None),  # Not yet scored
                models.Transaction.amount < 0,
            )
            .all()
        )

        for t in recent_txns:
            score, severity, explanation = detector.score_transaction(
                amount=t.amount,
                date=t.date,
                category=t.category or "Other",
                description=t.description,
            )
            t.anomaly_score = score
            t.anomaly_label = severity in ("medium", "high")
            t.anomaly_explanation = explanation if t.anomaly_label else None

            if t.anomaly_label:
                alert = models.Alert(
                    user_id=t.user_id,
                    transaction_id=t.id,
                    alert_type="anomaly",
                    severity=severity,
                    title=f"Unusual transaction: {t.description}",
                    message=explanation,
                )
                db.add(alert)

        db.commit()
        logger.info(f"[Scheduler] Anomaly scan complete: {len(recent_txns)} transactions scanned")
    except Exception as e:
        logger.error(f"[Scheduler] Anomaly scan error: {e}")
    finally:
        db.close()


def _run_bill_reminders():
    """
    Daily: check for upcoming subscription charges in next 3 days.
    Creates bill reminder alerts.
    """
    db = SessionLocal()
    try:
        from backend.ml.subscription_detector import get_subscription_detector
        import pandas as pd

        users = db.query(models.User).filter(models.User.is_active == True).all()
        detector = get_subscription_detector()

        for user in users:
            # Get recent transactions
            cutoff = datetime.now() - timedelta(days=180)
            txns = (
                db.query(models.Transaction)
                .filter(
                    models.Transaction.user_id == user.id,
                    models.Transaction.date >= cutoff,
                    models.Transaction.amount < 0,
                )
                .all()
            )

            if not txns:
                continue

            df = pd.DataFrame([{
                "date": t.date, "description": t.description,
                "amount": t.amount, "category": t.category or "Other",
            } for t in txns])

            subscriptions = detector.detect(df)
            upcoming = detector.upcoming_bills(subscriptions, days_ahead=3)

            for bill in upcoming:
                # Check if alert already exists
                existing = (
                    db.query(models.Alert)
                    .filter(
                        models.Alert.user_id == user.id,
                        models.Alert.alert_type == "bill",
                        models.Alert.title.contains(bill["merchant"]),
                        models.Alert.created_at >= datetime.now() - timedelta(days=1),
                    )
                    .first()
                )
                if not existing:
                    alert = models.Alert(
                        user_id=user.id,
                        alert_type="bill",
                        severity="low",
                        title=f"Upcoming bill: {bill['merchant']}",
                        message=(
                            f"₹{bill['amount']:,.0f} charge from {bill['merchant']} "
                            f"expected in {bill['due_in_days']} day(s) (on {bill['due_date']})."
                        ),
                    )
                    db.add(alert)

            db.commit()

        logger.info("[Scheduler] Bill reminders complete")
    except Exception as e:
        logger.error(f"[Scheduler] Bill reminder error: {e}")
    finally:
        db.close()


def _run_weekly_digest():
    """
    Every Monday at 9am: generate weekly digest for all active users.
    Stores as alert for display in UI.
    """
    db = SessionLocal()
    try:
        users = db.query(models.User).filter(models.User.is_active == True).all()

        for user in users:
            from backend.agent.planner import AgentPlanner
            import uuid

            agent = AgentPlanner(db=db, user_id=user.id, session_id=f"digest_{uuid.uuid4()}")
            digest_text = agent.generate_weekly_digest()

            alert = models.Alert(
                user_id=user.id,
                alert_type="digest",
                severity="low",
                title="📊 Your Weekly Financial Digest",
                message=digest_text,
                is_read=False,
            )
            db.add(alert)

        db.commit()
        logger.info(f"[Scheduler] Weekly digest generated for {len(users)} users")
    except Exception as e:
        logger.error(f"[Scheduler] Weekly digest error: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start all APScheduler jobs."""
    # Anomaly scan — every 6 hours
    scheduler.add_job(
        _run_anomaly_scan,
        CronTrigger(hour="*/6"),
        id="anomaly_scan",
        replace_existing=True,
    )

    # Bill reminders — daily at 8am IST
    scheduler.add_job(
        _run_bill_reminders,
        CronTrigger(hour=8, minute=0),
        id="bill_reminders",
        replace_existing=True,
    )

    # Weekly digest — every Monday at 9am IST
    scheduler.add_job(
        _run_weekly_digest,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_digest",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] APScheduler started with 3 jobs")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
