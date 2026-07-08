"""
FinAgent — Analytics Page
Anomaly explorer, subscription detector, forecast, and what-if simulator.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analytics — FinAgent", page_icon="🔍", layout="wide")

from frontend.components.api_client import (
    api_get_anomalies, api_get_subscriptions, api_get_forecast,
    api_get_summary, api_what_if
)
from frontend.components.charts import spending_bar, forecast_waterfall, COLORS

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

st.markdown("# 🔍 Analytics & Insights")

tab1, tab2, tab3, tab4 = st.tabs(["🚨 Anomalies", "🔄 Subscriptions", "🔮 Forecast", "🎮 What-If"])

# ─── Tab 1: Anomalies ─────────────────────────────────────────────────────────
with tab1:
    st.markdown("### 🚨 Anomalous Transactions")
    st.caption("Flagged by Isolation Forest model with SHAP-style explanations")

    days_col, _ = st.columns([1, 3])
    with days_col:
        anomaly_days = st.selectbox("Period", [30, 60, 90, 180], key="anomaly_days",
                                     format_func=lambda x: f"Last {x} days")

    with st.spinner("Running anomaly detection..."):
        anomaly_data = api_get_anomalies(days=anomaly_days)

    if anomaly_data:
        count = anomaly_data.get("count", 0)
        if count == 0:
            st.success("✅ No anomalies detected in this period. Your spending looks normal!")
        else:
            st.markdown(f"**{count} anomaly/anomalies found** in the last {anomaly_days} days")
            anomalies = anomaly_data.get("anomalies", [])

            for a in anomalies:
                severity = a.get("severity", "low")
                severity_class = f"alert-{severity}"
                score = a.get("anomaly_score", 0)
                score_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))

                st.markdown(
                    f"""
                    <div class="{severity_class}">
                    <b>{a.get('date', 'N/A')}</b> &nbsp;·&nbsp; 
                    <b>{a.get('description', 'Unknown')}</b> &nbsp;·&nbsp;
                    <span style="color: {'#FF4B4B' if severity == 'high' else '#FFA500'}">
                    ₹{abs(float(a.get('amount', 0))):,.0f}
                    </span>
                    &nbsp;·&nbsp; Category: {a.get('category', 'Other')}<br>
                    <small>Score: {score_bar} {score:.2f} ({severity.upper()})</small><br>
                    <small>🔍 {a.get('explanation', 'Unusual pattern detected.')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Summary chart
            if anomalies:
                df_a = pd.DataFrame(anomalies)
                by_cat = df_a.groupby("category").size().to_dict()
                fig = spending_bar(by_cat, "Anomalies by Category")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.error("Could not load anomaly data.")


# ─── Tab 2: Subscriptions ─────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔄 Subscription & Recurring Charge Detector")
    st.caption("Auto-detects recurring charges based on amount regularity and payment intervals")

    with st.spinner("Analyzing recurring charges..."):
        sub_data = api_get_subscriptions()

    if sub_data:
        creep = sub_data.get("creep_analysis", {})
        subs = sub_data.get("subscriptions", [])
        upcoming = sub_data.get("upcoming_bills", [])

        # Creep score
        risk = creep.get("risk_level", "healthy")
        risk_color = {"healthy": "#43E97B", "moderate": "#FFA500", "high": "#FF4B4B"}.get(risk, "#43E97B")

        cols = st.columns(4)
        cols[0].metric("Monthly Cost", f"₹{creep.get('total_monthly_subscriptions', 0):,.0f}")
        cols[1].metric("% of Income", f"{creep.get('income_pct', 0):.1f}%")
        cols[2].metric("Subscriptions Found", str(creep.get("count", 0)))
        cols[3].metric("Risk Level", risk.upper())

        st.markdown(
            f'<div class="alert-{"high" if risk == "high" else "low"}">{creep.get("insight", "")}</div>',
            unsafe_allow_html=True,
        )

        # Upcoming bills
        if upcoming:
            st.markdown("#### ⏰ Upcoming Bills (Next 7 Days)")
            for bill in upcoming:
                st.info(
                    f"📅 **{bill['merchant']}** — ₹{bill['amount']:,.0f} due in {bill['due_in_days']} day(s) ({bill['due_date']})"
                )

        # Subscription table
        if subs:
            st.markdown("#### 📋 All Detected Subscriptions")
            df_s = pd.DataFrame(subs)
            display = df_s[["merchant", "category", "amount", "monthly_cost", "interval_days", "confidence", "last_charge", "next_expected"]].copy()
            display.columns = ["Merchant", "Category", "Charge (₹)", "Monthly Cost (₹)", "Interval (days)", "Confidence", "Last Charge", "Next Expected"]
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("No recurring subscriptions detected. Upload more transaction history for better detection.")
    else:
        st.error("Could not load subscription data.")


# ─── Tab 3: Forecast ─────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🔮 Spending Forecast")
    st.caption("Rolling mean + linear trend extrapolation based on your last 90 days")

    horizon = st.select_slider(
        "Forecast horizon",
        options=[7, 14, 30, 60, 90],
        value=30,
        format_func=lambda x: f"{x} days",
    )

    with st.spinner("Computing forecast..."):
        fc = api_get_forecast(horizon=horizon)

    if fc:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Projected Expenses", f"₹{fc.get('predicted_total_expense', 0):,.0f}")
        col2.metric("Projected Income", f"₹{fc.get('predicted_income', 0):,.0f}")
        col3.metric("Projected Savings", f"₹{fc.get('predicted_net_savings', 0):,.0f}")
        col4.metric(
            "Confidence",
            fc.get("confidence", "N/A").upper(),
            delta=f"Until {fc.get('forecast_end_date', 'N/A')}",
            delta_color="off",
        )

        fig = forecast_waterfall(fc, f"{horizon}-Day Forecast by Category")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.error("Forecast unavailable. Add more transaction data.")


# ─── Tab 4: What-If Simulator ─────────────────────────────────────────────────
with tab4:
    st.markdown("### 🎮 What-If Simulator")
    st.caption("Simulate the impact of reducing spending in any category")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        categories = [
            "Food & Dining", "Transport", "Shopping", "Utilities & Bills",
            "Healthcare", "Entertainment", "Education", "Travel",
        ]
        sim_cat = st.selectbox("Category to reduce", categories)
    with col2:
        reduction = st.slider("Reduction percentage", 5, 80, 20, step=5, format="%d%%")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_sim = st.button("▶️ Simulate", use_container_width=True)

    if run_sim:
        with st.spinner("Running simulation..."):
            result = api_what_if(sim_cat, float(reduction))

        if result and "error" not in result:
            st.markdown(f"""
            <div class="finagent-card">
            <h3>📊 Simulation Results</h3>
            <p>Category: <b>{result['category']}</b> · Reduction: <b>{reduction}%</b></p>
            <hr style="border-color: rgba(108,99,255,0.2)">
            <p>Current monthly spend: <b>₹{result['current_monthly_spend']:,.0f}</b></p>
            <p>Monthly savings: <span style="color: #43E97B; font-size: 1.5rem; font-weight: 700;">₹{result['monthly_savings']:,.0f}</span></p>
            <p>Annual savings: <span style="color: #6C63FF; font-size: 1.2rem; font-weight: 600;">₹{result['annual_savings']:,.0f}</span></p>
            <hr style="border-color: rgba(108,99,255,0.2)">
            <p>💡 {result['insight']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif result:
            st.warning(result.get("error", "No data available for this category."))
