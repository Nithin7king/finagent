"""
ml_models.py
- Transaction categorization (text classifier on merchant name)
- Anomaly / fraud detection (Isolation Forest, per-category z-score explanation)
- Spending forecasting (simple weighted moving average per category)
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.ensemble import IsolationForest


# ---------------------------------------------------------------------------
# 1. CATEGORIZATION MODEL
# ---------------------------------------------------------------------------
class CategorizationModel:
    """Learns to predict a transaction's category from its merchant name."""

    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))),
            ("clf", LogisticRegression(max_iter=1000)),
        ])
        self.is_fitted = False

    def fit(self, df):
        X = df["merchant"]
        y = df["category"]
        self.pipeline.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, merchants):
        if not self.is_fitted:
            raise RuntimeError("Model not fitted yet.")
        preds = self.pipeline.predict(merchants)
        probs = self.pipeline.predict_proba(merchants)
        confidences = probs.max(axis=1)
        return preds, confidences

    def explain(self, merchant, top_k=3):
        """Return top matching categories with confidence - a simple explainability layer."""
        probs = self.pipeline.predict_proba([merchant])[0]
        classes = self.pipeline.classes_
        ranked = sorted(zip(classes, probs), key=lambda x: -x[1])[:top_k]
        return ranked


# ---------------------------------------------------------------------------
# 2. ANOMALY / FRAUD DETECTION
# ---------------------------------------------------------------------------
class AnomalyDetector:
    """
    Detects unusual transactions using Isolation Forest on amount (scaled per category),
    plus a z-score based explanation for why something was flagged.
    """

    def __init__(self, contamination=0.03):
        self.contamination = contamination
        self.category_stats = {}   # {category: (mean, std)}
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False

    def fit(self, df):
        # store per-category mean/std for explainability
        for cat, group in df.groupby("category"):
            self.category_stats[cat] = (group["amount"].mean(), group["amount"].std() or 1.0)

        # build a feature: how many std-devs away from the category mean
        z_scores = df.apply(
            lambda r: (r["amount"] - self.category_stats[r["category"]][0])
            / self.category_stats[r["category"]][1],
            axis=1,
        ).values.reshape(-1, 1)

        self.model.fit(z_scores)
        self.is_fitted = True
        return self

    def _zscore(self, category, amount):
        mean, std = self.category_stats.get(category, (amount, 1.0))
        return (amount - mean) / std

    def detect(self, df):
        if not self.is_fitted:
            raise RuntimeError("Model not fitted yet.")
        results = []
        for _, row in df.iterrows():
            z = self._zscore(row["category"], row["amount"])
            pred = self.model.predict([[z]])[0]  # -1 = anomaly, 1 = normal
            is_anomaly = pred == -1
            mean, std = self.category_stats.get(row["category"], (row["amount"], 1.0))
            explanation = (
                f"This ₹{row['amount']:.0f} charge in '{row['category']}' is "
                f"{abs(z):.1f}x standard deviations away from your usual spend "
                f"(avg ₹{mean:.0f}) for this category."
                if is_anomaly else "Within normal spending pattern."
            )
            results.append({
                "transaction_id": row["transaction_id"],
                "is_anomaly": bool(is_anomaly),
                "z_score": round(float(z), 2),
                "explanation": explanation,
            })
        return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# 3. SPENDING FORECAST
# ---------------------------------------------------------------------------
def forecast_next_month(df, category=None):
    """
    Simple, explainable forecast: weighted average of last 3 months' spend per category,
    weighted toward the most recent month. (Kept simple/interpretable for a portfolio project;
    swap in Prophet/ARIMA for a more advanced version.)
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    if category:
        df = df[df["category"] == category]

    monthly = df.groupby(["month", "category"])["amount"].sum().reset_index()

    forecasts = {}
    for cat in monthly["category"].unique():
        cat_data = monthly[monthly["category"] == cat].sort_values("month")
        last_3 = cat_data.tail(3)["amount"].values
        if len(last_3) == 0:
            continue
        weights = np.linspace(1, 2, len(last_3))  # more recent months weighted higher
        forecast = float(np.average(last_3, weights=weights))
        forecasts[cat] = round(forecast, 2)

    return forecasts


def detect_subscriptions(df):
    """Flags merchants that recur monthly with a near-identical amount - subscription creep detector."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    subs = []
    for merchant, group in df.groupby("merchant"):
        if len(group) >= 2:
            amounts = group["amount"].values
            if np.std(amounts) < (0.05 * np.mean(amounts) + 1):  # near-constant amount
                subs.append({
                    "merchant": merchant,
                    "category": group["category"].iloc[0],
                    "avg_amount": round(float(np.mean(amounts)), 2),
                    "occurrences": len(group),
                })
    return pd.DataFrame(subs).sort_values("occurrences", ascending=False) if subs else pd.DataFrame(
        columns=["merchant", "category", "avg_amount", "occurrences"]
    )


if __name__ == "__main__":
    from data_gen import generate_transactions, inject_anomalies

    df = generate_transactions(500, seed=42)
    df = inject_anomalies(df, n_anomalies=8, seed=7)

    print("=== Categorization ===")
    cat_model = CategorizationModel().fit(df)
    preds, conf = cat_model.predict(df["merchant"].iloc[:5])
    for m, p, c in zip(df["merchant"].iloc[:5], preds, conf):
        print(f"{m:30s} -> {p:15s} (confidence {c:.2f})")

    print("\n=== Anomaly Detection ===")
    anomaly_model = AnomalyDetector().fit(df)
    anomaly_results = anomaly_model.detect(df)
    flagged = anomaly_results[anomaly_results["is_anomaly"]]
    print(f"Flagged {len(flagged)} anomalies out of {len(df)} transactions")
    print(flagged.head())

    print("\n=== Forecast ===")
    forecasts = forecast_next_month(df)
    for cat, amt in forecasts.items():
        print(f"{cat:15s}: predicted next month spend ~ ₹{amt}")

    print("\n=== Subscriptions ===")
    subs = detect_subscriptions(df)
    print(subs)
