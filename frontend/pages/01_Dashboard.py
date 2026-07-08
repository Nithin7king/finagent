"""
FinAgent — Dashboard Page
KPI overview, spending charts, forecast widget, and alert banners.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

st.set_page_config(page_title="Dashboard — FinAgent", page_icon="📊", layout="wide")

from frontend.components.api_client import (
    api_get_summary, api_get_forecast, api_get_spending_trend, api_get_anomalies
)
from frontend.components.charts import (
    spending_donut, spending_line, savings_rate_gauge, forecast_waterfall, COLORS
)

# Auth guard
if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

user = st.session_state.get("user", {})

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("# 📊 Financial Dashboard")
st.caption(f"Welcome back, **{user.get('name', 'User')}** · Currency: {user.get('currency', 'INR')}")

# Period selector
period_col, _, refresh_col = st.columns([1, 4, 1])
with period_col:
    period = st.selectbox("Period", [30, 60, 90, 180, 365], format_func=lambda x: f"Last {x} days", label_visibility="collapsed")
with refresh_col:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

# ─── Load Data ────────────────────────────────────────────────────────────────
with st.spinner("Loading financial data..."):
    summary = api_get_summary(days=period)
    forecast = api_get_forecast(horizon=30)
    trend = api_get_spending_trend(months=6)
    anomalies = api_get_anomalies(days=period)

if not summary:
    st.error("Could not load financial data. Make sure the backend is running.")
    st.stop()

# ─── Alert Banners ────────────────────────────────────────────────────────────
anomaly_count = anomalies.get("count", 0) if anomalies else 0
if anomaly_count > 0:
    st.markdown(
        f'<div class="alert-high">⚠️ <b>{anomaly_count} anomalous transaction(s)</b> detected in the last {period} days. '
        f'Visit the <b>Analytics</b> page for details.</div>',
        unsafe_allow_html=True,
    )

# ─── KPI Cards ───────────────────────────────────────────────────────────────
st.markdown("### 💡 Key Metrics")
k1, k2, k3, k4 = st.columns(4)

income = summary.get("total_income", 0)
expenses = summary.get("total_expenses", 0)
savings = summary.get("net_savings", 0)
savings_rate = summary.get("savings_rate", 0)

k1.metric(
    "💰 Total Income",
    f"₹{income:,.0f}",
    delta=f"{period} days",
    delta_color="off",
)
k2.metric(
    "💸 Total Expenses",
    f"₹{expenses:,.0f}",
    delta=f"{summary.get('transaction_count', 0)} transactions",
    delta_color="off",
)
k3.metric(
    "📈 Net Savings",
    f"₹{savings:,.0f}",
    delta=f"{savings_rate:.1f}% rate",
    delta_color="normal" if savings >= 0 else "inverse",
)
k4.metric(
    "🚨 Anomalies",
    str(anomaly_count),
    delta="flagged transactions",
    delta_color="inverse" if anomaly_count > 0 else "off",
)

st.divider()

# ─── Charts Row 1 ─────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns([1, 1])

with chart_col1:
    by_category = summary.get("by_category", {})
    fig_donut = spending_donut(by_category, f"Spending by Category (Last {period} days)")
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

with chart_col2:
    fig_gauge = savings_rate_gauge(savings_rate)
    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    # Forecast quick summary
    if forecast:
        fc_expense = forecast.get("predicted_total_expense", 0)
        fc_income = forecast.get("predicted_income", 0)
        fc_savings = forecast.get("predicted_net_savings", 0)
        fc_confidence = forecast.get("confidence", "N/A")

        st.markdown(
            f"""
            <div class="finagent-card">
            🔮 <b>Next 30 Days Forecast</b> ({fc_confidence} confidence)<br>
            📤 Expenses: ₹{fc_expense:,.0f} &nbsp;|&nbsp;
            📥 Income: ₹{fc_income:,.0f} &nbsp;|&nbsp;
            💾 Net: ₹{fc_savings:,.0f}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ─── Charts Row 2 ─────────────────────────────────────────────────────────────
st.divider()
chart_col3, chart_col4 = st.columns([3, 2])

with chart_col3:
    monthly_trend = trend.get("savings_rate_history", []) if trend else []
    fig_line = spending_line(monthly_trend, "Income vs Expenses vs Savings (6 Months)")
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

with chart_col4:
    fig_forecast = forecast_waterfall(forecast or {}, "30-Day Forecast by Category")
    st.plotly_chart(fig_forecast, use_container_width=True, config={"displayModeBar": False})

# ─── Top Spending Table ───────────────────────────────────────────────────────
st.divider()
st.markdown("### 🏆 Top Spending Categories")
by_cat = summary.get("by_category", {})
if by_cat:
    import pandas as pd
    df_cats = pd.DataFrame([
        {"Category": k, "Amount (₹)": f"₹{v:,.0f}", "% of Expenses": f"{v/expenses*100:.1f}%"}
        for k, v in sorted(by_cat.items(), key=lambda x: -x[1])
    ])
    st.dataframe(df_cats, use_container_width=True, hide_index=True)
else:
    st.info("No spending data for this period.")
