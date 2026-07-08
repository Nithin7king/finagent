"""
FinAgent — Anomaly Detector
IsolationForest on behavioral features with rule-based SHAP-style explanations.
Outputs: anomaly_score (0–1), severity (low/medium/high), explanation string.
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from datetime import datetime, timedelta

MODEL_PATH = os.path.join(os.path.dirname(__file__), "anomaly_model.joblib")
STATS_PATH = os.path.join(os.path.dirname(__file__), "anomaly_stats.joblib")

SEVERITY_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25,
}


def _extract_features(df: pd.DataFrame) -> np.ndarray:
    """
    Engineer features for anomaly detection:
    - amount_abs: absolute value of transaction amount
    - day_of_week: 0-6
    - hour: hour of day (0-23)
    - is_weekend: 1 if Sat/Sun
    - amount_log: log1p of absolute amount (handles skew)
    """
    features = pd.DataFrame()
    features["amount_abs"] = df["amount"].abs()
    features["amount_log"] = np.log1p(df["amount"].abs())
    features["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
    features["is_weekend"] = (features["day_of_week"] >= 5).astype(int)
    features["hour"] = pd.to_datetime(df["date"]).dt.hour
    return features.values


class AnomalyDetector:
    """
    Detects anomalous transactions using Isolation Forest.
    Provides rule-based explanations (why was this flagged?).
    """

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model: Optional[Pipeline] = None
        self.stats: Optional[Dict] = None  # per-category stats for explanation
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        if os.path.exists(STATS_PATH):
            self.stats = joblib.load(STATS_PATH)

    def fit(self, transactions_df: pd.DataFrame):
        """
        Train the Isolation Forest on a user's transaction history.
        Args:
            transactions_df: DataFrame with columns [date, amount, category, description]
        """
        expenses = transactions_df[transactions_df["amount"] < 0].copy()
        if len(expenses) < 20:
            return  # Not enough data

        X = _extract_features(expenses)

        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("iso", IsolationForest(
                contamination=self.contamination,
                n_estimators=200,
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self.model.fit(X)

        # Compute per-category amount statistics for explanations
        self.stats = {}
        for cat in expenses["category"].unique():
            cat_data = expenses[expenses["category"] == cat]["amount"].abs()
            self.stats[cat] = {
                "mean": cat_data.mean(),
                "std": cat_data.std() or 1.0,
                "p75": cat_data.quantile(0.75),
                "p95": cat_data.quantile(0.95),
                "max": cat_data.max(),
            }

        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.stats, STATS_PATH)

    def score_transaction(
        self,
        amount: float,
        date: datetime,
        category: str,
        description: str,
    ) -> Tuple[float, str, str]:
        """
        Score a single transaction for anomaly.

        Returns:
            (anomaly_score 0-1, severity str, explanation str)
        """
        if self.model is None:
            return 0.0, "low", "No model trained yet."

        # Feature vector for single transaction
        row = pd.DataFrame([{"date": date, "amount": amount}])
        X = _extract_features(row)

        # IsolationForest decision_function: negative = anomalous
        raw_score = self.model.decision_function(X)[0]

        # Normalize to 0–1 (lower decision_function = higher anomaly)
        # Typical range: -0.5 to 0.5
        anomaly_score = float(np.clip(0.5 - raw_score, 0, 1))

        severity = "low"
        if anomaly_score >= SEVERITY_THRESHOLDS["high"]:
            severity = "high"
        elif anomaly_score >= SEVERITY_THRESHOLDS["medium"]:
            severity = "medium"

        explanation = self._explain(amount, date, category, description, anomaly_score)
        return anomaly_score, severity, explanation

    def _explain(
        self,
        amount: float,
        date: datetime,
        category: str,
        description: str,
        score: float,
    ) -> str:
        """
        Generate a human-readable explanation for why this was flagged.
        Uses per-category statistics to compute relative unusualness.
        """
        reasons = []
        amt_abs = abs(amount)

        # Category-based amount check
        if self.stats and category in self.stats:
            cat_stats = self.stats[category]
            z_score = (amt_abs - cat_stats["mean"]) / cat_stats["std"]
            if z_score > 2.5:
                multiplier = amt_abs / cat_stats["mean"]
                reasons.append(
                    f"₹{amt_abs:,.0f} is {multiplier:.1f}× your usual {category} spend "
                    f"(avg ₹{cat_stats['mean']:,.0f})"
                )
            if amt_abs > cat_stats["p95"]:
                reasons.append(
                    f"This amount exceeds your 95th percentile {category} transaction "
                    f"(₹{cat_stats['p95']:,.0f})"
                )

        # Time-based check
        if isinstance(date, datetime):
            hour = date.hour
            if hour >= 0 and hour <= 5:
                reasons.append(f"Transaction occurred at an unusual time ({hour}:00 AM)")
            if date.weekday() >= 5:
                reasons.append("Transaction on a weekend (less common for this category)")

        # Generic if nothing specific found
        if not reasons:
            reasons.append(
                f"Unusual transaction pattern for '{description}' "
                f"based on your historical behavior"
            )

        explanation = f"Flagged as anomaly (score: {score:.2f}). Reasons: {'; '.join(reasons)}."
        return explanation

    def detect_batch(self, transactions: List[Dict]) -> List[Dict]:
        """
        Run anomaly detection on a list of transactions.
        Returns same list with added: anomaly_score, anomaly_label, anomaly_explanation, severity fields.
        """
        results = []
        for t in transactions:
            if t.get("amount", 0) > 0:  # Skip income
                results.append({
                    **t,
                    "anomaly_score": 0.0,
                    "anomaly_label": False,
                    "anomaly_explanation": None,
                    "severity": "low",
                })
                continue

            score, severity, explanation = self.score_transaction(
                amount=t["amount"],
                date=t.get("date", datetime.now()),
                category=t.get("category", "Other"),
                description=t.get("description", ""),
            )
            is_anomaly = severity in ("medium", "high")
            results.append({
                **t,
                "anomaly_score": round(score, 4),
                "anomaly_label": is_anomaly,
                "anomaly_explanation": explanation if is_anomaly else None,
                "severity": severity,
            })
        return results


# Singleton instance
_detector: Optional[AnomalyDetector] = None


def get_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector
