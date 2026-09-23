"""
FinAgent — Subscription / Recurring Charge Detector
Detects recurring charges (subscriptions, EMIs, utility bills) in transaction history.
Computes "subscription creep" score.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


AMOUNT_TOLERANCE = 0.10       # 10% tolerance for "same amount" check
MIN_OCCURRENCES = 2           # Must appear at least 2× to be subscription
INTERVAL_CANDIDATES = [7, 14, 28, 30, 31]  # Weekly, biweekly, monthly


def _normalize_merchant(name: str) -> str:
    """Normalize merchant name for grouping."""
    return name.strip().lower()


class SubscriptionDetector:
    """
    Detects recurring subscription charges and EMIs.
    Uses amount-tolerance grouping + interval regularity analysis.
    """

    def detect(self, transactions_df: pd.DataFrame) -> List[Dict]:
        """
        Find all recurring charges in transaction history.

        Args:
            transactions_df: DataFrame with [date, description, amount, category]

        Returns:
            List of detected subscriptions with metadata
        """
        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        expenses = df[df["amount"] < 0].copy()
        expenses["amount_abs"] = expenses["amount"].abs()
        expenses["merchant_key"] = expenses["description"].apply(_normalize_merchant)

        subscriptions = []
        seen_merchants = set()

        # Group by merchant
        for merchant_key, group in expenses.groupby("merchant_key"):
            if merchant_key in seen_merchants:
                continue
            group = group.sort_values("date").reset_index(drop=True)

            if len(group) < MIN_OCCURRENCES:
                continue

            # Check if amounts are similar (within tolerance)
            amounts = group["amount_abs"].values
            mean_amt = np.mean(amounts)
            amount_cv = (np.std(amounts) / mean_amt) if mean_amt > 0 else 0  # Coefficient of variation
            if amount_cv > 0.15:  # > 15% variation → not subscription
                continue

            # Check interval regularity
            dates = group["date"].values
            intervals = [(dates[i+1] - dates[i]) / np.timedelta64(1, "D")
                         for i in range(len(dates) - 1)]
            avg_interval = np.mean(intervals)
            interval_std = np.std(intervals)

            # Must be within ±4 days of a known interval
            is_regular = False
            matched_interval = None
            for candidate in INTERVAL_CANDIDATES:
                if abs(avg_interval - candidate) <= 4:
                    if interval_std <= 5:  # Low variance in interval
                        is_regular = True
                        matched_interval = candidate
                        break

            if not is_regular:
                continue

            # Compute monthly cost
            if matched_interval in (28, 30, 31):
                monthly_cost = np.mean(amounts)
            elif matched_interval == 14:
                monthly_cost = np.mean(amounts) * 2
            elif matched_interval == 7:
                monthly_cost = np.mean(amounts) * 4.33
            else:
                monthly_cost = np.mean(amounts) * (30 / matched_interval)

            # Estimate next charge
            last_date = pd.Timestamp(dates[-1])
            next_expected = last_date + timedelta(days=matched_interval)

            subscriptions.append({
                "merchant": group["description"].iloc[0],
                "category": group["category"].iloc[0],
                "amount": round(float(np.mean(amounts)), 2),
                "interval_days": matched_interval,
                "monthly_cost": round(monthly_cost, 2),
                "occurrences": len(group),
                "last_charge": last_date.to_pydatetime(),
                "next_expected": next_expected.to_pydatetime(),
                "confidence": "high" if interval_std <= 2 else "medium",
            })
            seen_merchants.add(merchant_key)

        # Sort by monthly cost descending
        subscriptions.sort(key=lambda x: x["monthly_cost"], reverse=True)
        return subscriptions

    def subscription_creep_score(
        self,
        subscriptions: List[Dict],
        monthly_income: float,
    ) -> Dict:
        """
        Compute subscription creep score and insights.

        Returns:
            Dict with total_monthly, income_pct, risk_level, insight
        """
        total_monthly = sum(s["monthly_cost"] for s in subscriptions)

        if monthly_income > 0:
            income_pct = (total_monthly / monthly_income) * 100
        else:
            income_pct = 0

        # Risk categorization
        if income_pct <= 5:
            risk_level = "healthy"
            insight = f"Your subscriptions cost ₹{total_monthly:,.0f}/month ({income_pct:.1f}% of income). This is within healthy limits."
        elif income_pct <= 10:
            risk_level = "moderate"
            insight = (
                f"Your subscriptions cost ₹{total_monthly:,.0f}/month ({income_pct:.1f}% of income). "
                f"Consider reviewing infrequently used services."
            )
        else:
            risk_level = "high"
            insight = (
                f"⚠️ Subscription creep detected! ₹{total_monthly:,.0f}/month ({income_pct:.1f}% of income) "
                f"is being spent on recurring charges. Recommend auditing and cancelling unused subscriptions."
            )

        # Identify top 3 most expensive
        top_3 = sorted(subscriptions, key=lambda x: x["monthly_cost"], reverse=True)[:3]
        top_str = ", ".join(f"{s['merchant']} (₹{s['monthly_cost']:.0f})" for s in top_3)

        return {
            "total_monthly_subscriptions": round(total_monthly, 2),
            "income_pct": round(income_pct, 1),
            "risk_level": risk_level,
            "insight": insight,
            "top_3_by_cost": top_str,
            "count": len(subscriptions),
        }

    def upcoming_bills(
        self,
        subscriptions: List[Dict],
        days_ahead: int = 7,
    ) -> List[Dict]:
        """Return subscriptions due within the next `days_ahead` days."""
        now = datetime.now()
        upcoming = []
        for s in subscriptions:
            next_dt = s.get("next_expected")
            if next_dt and now <= next_dt <= now + timedelta(days=days_ahead):
                days_until = (next_dt - now).days
                upcoming.append({
                    "merchant": s["merchant"],
                    "amount": s["amount"],
                    "due_in_days": days_until,
                    "due_date": next_dt.strftime("%Y-%m-%d"),
                })
        return sorted(upcoming, key=lambda x: x["due_in_days"])


# Singleton
_sub_detector: Optional[SubscriptionDetector] = None


def get_subscription_detector() -> SubscriptionDetector:
    global _sub_detector
    if _sub_detector is None:
        _sub_detector = SubscriptionDetector()
    return _sub_detector
