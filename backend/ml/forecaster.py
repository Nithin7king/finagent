"""
FinAgent — Spending Forecaster
Rolling-mean + linear trend extrapolation for 30/60/90-day spending forecasts.
Also computes savings rate prediction and income trend.
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class SpendingForecaster:
    """
    Forecasts future spending based on historical transaction data.
    Uses rolling mean + linear trend (no external dependencies like Prophet).
    """

    def __init__(self, lookback_days: int = 90):
        self.lookback_days = lookback_days

    def forecast(
        self,
        transactions_df: pd.DataFrame,
        horizon_days: int = 30,
    ) -> Dict:
        """
        Forecast spending for next `horizon_days` days.

        Args:
            transactions_df: DataFrame with columns [date, amount, category]
            horizon_days: Number of days to forecast (30, 60, or 90)

        Returns:
            Dict with total forecast, by-category breakdown, and savings forecast
        """
        if transactions_df.empty:
            return self._empty_forecast(horizon_days)

        df = transactions_df.copy()
        df["date"] = pd.to_datetime(df["date"])

        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        recent = df[df["date"] >= cutoff].copy()

        if recent.empty:
            return self._empty_forecast(horizon_days)

        expenses = recent[recent["amount"] < 0].copy()
        income = recent[recent["amount"] > 0].copy()

        # ── Per-category forecast ──
        category_forecast = {}
        for category in expenses["category"].unique():
            cat_data = expenses[expenses["category"] == category].copy()
            cat_forecast = self._forecast_category(cat_data, horizon_days)
            category_forecast[category] = round(cat_forecast, 2)

        total_expense_forecast = sum(category_forecast.values())

        # ── Income forecast ──
        if not income.empty:
            avg_monthly_income = income["amount"].sum() / (self.lookback_days / 30)
            income_forecast = avg_monthly_income * (horizon_days / 30)
        else:
            income_forecast = 0.0

        # ── Savings forecast ──
        net_savings_forecast = income_forecast - total_expense_forecast
        savings_rate = (net_savings_forecast / income_forecast * 100) if income_forecast > 0 else 0

        # ── Daily average breakdown ──
        daily_avg_expense = total_expense_forecast / horizon_days

        return {
            "period_days": horizon_days,
            "predicted_total_expense": round(total_expense_forecast, 2),
            "predicted_income": round(income_forecast, 2),
            "predicted_net_savings": round(net_savings_forecast, 2),
            "predicted_savings_rate": round(savings_rate, 1),
            "daily_avg_expense": round(daily_avg_expense, 2),
            "by_category": category_forecast,
            "confidence": self._confidence_level(len(expenses)),
            "forecast_end_date": (datetime.now() + timedelta(days=horizon_days)).strftime("%Y-%m-%d"),
        }

    def _forecast_category(self, cat_df: pd.DataFrame, horizon_days: int) -> float:
        """
        Forecast total spend for a single category over horizon_days.
        Uses rolling 30-day average + linear trend adjustment.
        """
        cat_df = cat_df.copy()
        cat_df["amount_abs"] = cat_df["amount"].abs()
        cat_df["date"] = pd.to_datetime(cat_df["date"])
        cat_df = cat_df.set_index("date").sort_index()

        # Daily aggregation
        daily = cat_df["amount_abs"].resample("D").sum().fillna(0)

        if len(daily) < 7:
            # Not enough data: use simple average
            return daily.mean() * horizon_days

        # Rolling 30-day average
        rolling_avg = daily.rolling(window=min(30, len(daily)), min_periods=1).mean()
        recent_avg = float(rolling_avg.iloc[-1])

        # Linear trend: fit OLS on daily totals
        x = np.arange(len(daily))
        y = daily.values
        if len(x) > 5:
            coeffs = np.polyfit(x, y, 1)
            trend_per_day = coeffs[0]
        else:
            trend_per_day = 0
            coeffs = np.array([0.0, float(recent_avg)])

        # Forecast: recent average + trend adjustment
        # Trend-adjusted daily spend for forecast period
        last_x = len(daily)
        forecast_days_x = np.arange(last_x, last_x + horizon_days)
        trend_adjustment = np.polyval(coeffs, forecast_days_x)
        total_forecast = float(np.clip(trend_adjustment, 0, None).sum())

        # Blend: 70% trend-based, 30% rolling average
        average_based = recent_avg * horizon_days
        blended = 0.7 * total_forecast + 0.3 * average_based
        return max(0, blended)

    def _confidence_level(self, n_samples: int) -> str:
        if n_samples >= 200:
            return "high"
        elif n_samples >= 50:
            return "medium"
        else:
            return "low"

    def _empty_forecast(self, horizon_days: int) -> Dict:
        return {
            "period_days": horizon_days,
            "predicted_total_expense": 0,
            "predicted_income": 0,
            "predicted_net_savings": 0,
            "predicted_savings_rate": 0,
            "daily_avg_expense": 0,
            "by_category": {},
            "confidence": "low",
            "forecast_end_date": (datetime.now() + timedelta(days=horizon_days)).strftime("%Y-%m-%d"),
        }

    def spending_trend(self, transactions_df: pd.DataFrame, months: int = 6) -> List[Dict]:
        """
        Return month-by-month spending breakdown for the last `months` months.
        Useful for chart rendering.
        """
        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        cutoff = datetime.now() - timedelta(days=30 * months)
        df = df[df["date"] >= cutoff]

        expenses = df[df["amount"] < 0].copy()
        expenses["month"] = expenses["date"].dt.to_period("M")
        expenses["amount_abs"] = expenses["amount"].abs()

        monthly = expenses.groupby("month")["amount_abs"].sum().reset_index()
        monthly["month_str"] = monthly["month"].astype(str)
        monthly = monthly.sort_values("month")

        return monthly[["month_str", "amount_abs"]].rename(
            columns={"month_str": "month", "amount_abs": "total_expense"}
        ).to_dict("records")

    def savings_rate_history(self, transactions_df: pd.DataFrame, months: int = 6) -> List[Dict]:
        """Return monthly savings rate history."""
        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        cutoff = datetime.now() - timedelta(days=30 * months)
        df = df[df["date"] >= cutoff]
        df["month"] = df["date"].dt.to_period("M")

        result = []
        for month, group in df.groupby("month"):
            income = group[group["amount"] > 0]["amount"].sum()
            expenses = group[group["amount"] < 0]["amount"].abs().sum()
            net = income - expenses
            rate = (net / income * 100) if income > 0 else 0
            result.append({
                "month": str(month),
                "income": round(income, 2),
                "expenses": round(expenses, 2),
                "savings": round(net, 2),
                "savings_rate": round(rate, 1),
            })
        return sorted(result, key=lambda x: x["month"])


# Singleton
_forecaster: Optional[SpendingForecaster] = None


def get_forecaster() -> SpendingForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = SpendingForecaster()
    return _forecaster
