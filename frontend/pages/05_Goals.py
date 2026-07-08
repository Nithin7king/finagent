"""
FinAgent — Goals Page
Savings goals tracker with progress visualization and AI recommendations.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from datetime import datetime, date

st.set_page_config(page_title="Goals — FinAgent", page_icon="🎯", layout="wide")

from frontend.components.api_client import (
    api_get_goals, api_create_goal, api_update_goal,
    api_delete_goal, api_contribute_to_goal
)
from frontend.components.charts import goal_progress_bars

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

st.markdown("# 🎯 Savings Goals")
st.caption("Set financial targets, track progress, and let the AI guide your savings journey")

# ─── Load Goals ───────────────────────────────────────────────────────────────
goals = api_get_goals() or []

# ─── Summary Metrics ──────────────────────────────────────────────────────────
if goals:
    total_target = sum(g.get("target_amount", 0) for g in goals)
    total_saved = sum(g.get("current_amount", 0) for g in goals)
    completed = sum(1 for g in goals if g.get("is_completed"))
    active = len(goals) - completed

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Goals", str(len(goals)))
    m2.metric("Active Goals", str(active))
    m3.metric("Completed 🎉", str(completed))
    m4.metric("Total Saved", f"₹{total_saved:,.0f}", delta=f"of ₹{total_target:,.0f} target")

    # Progress chart
    st.plotly_chart(
        goal_progress_bars(goals),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.divider()

# ─── Goal Cards ───────────────────────────────────────────────────────────────
if goals:
    st.markdown("### 📋 Your Goals")
    for goal in goals:
        progress = goal.get("progress_pct", 0)
        is_completed = goal.get("is_completed", False)
        months_to = goal.get("months_to_goal")

        status_icon = "✅" if is_completed else "🎯"
        border_color = "#43E97B" if is_completed else "#6C63FF"

        with st.container():
            st.markdown(
                f"""
                <div class="finagent-card" style="border-color: {border_color}40;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                <h3 style="margin:0">{status_icon} {goal['name']}</h3>
                <p style="color: #94A3B8; margin: 4px 0;">{goal.get('description') or 'No description'}</p>
                </div>
                <div style="text-align: right;">
                <div class="kpi-big">₹{goal['current_amount']:,.0f}</div>
                <div style="color: #94A3B8;">of ₹{goal['target_amount']:,.0f}</div>
                </div>
                </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Progress bar
            st.progress(min(progress / 100, 1.0))
            prog_col, date_col, contrib_col = st.columns(3)

            with prog_col:
                st.caption(f"**{progress:.1f}%** complete")
                if months_to and not is_completed:
                    st.caption(f"⏱️ ~{months_to:.1f} months at current rate")

            with date_col:
                if goal.get("target_date"):
                    try:
                        td = datetime.fromisoformat(str(goal["target_date"]))
                        st.caption(f"🗓️ Target: {td.strftime('%b %Y')}")
                    except Exception:
                        st.caption(f"🗓️ Target: {goal['target_date']}")
                st.caption(f"💵 Monthly: ₹{goal.get('monthly_contribution', 0):,.0f}")

            with contrib_col:
                if not is_completed:
                    contrib_amount = st.number_input(
                        "Add contribution",
                        min_value=0.0,
                        step=500.0,
                        key=f"contrib_{goal['id']}",
                        label_visibility="collapsed",
                        placeholder="₹ Amount",
                    )
                    if st.button(f"➕ Add ₹{contrib_amount:,.0f}", key=f"add_{goal['id']}"):
                        if contrib_amount > 0:
                            result = api_contribute_to_goal(goal["id"], contrib_amount)
                            if result:
                                st.success(result.get("message", "Contribution added!"))
                                st.rerun()

            # Delete button
            with st.expander("⚙️ Manage", expanded=False):
                del_col, _ = st.columns([1, 3])
                with del_col:
                    if st.button("🗑️ Delete Goal", key=f"del_{goal['id']}", type="secondary"):
                        if api_delete_goal(goal["id"]):
                            st.success("Goal deleted.")
                            st.rerun()

            st.divider()
else:
    st.info("🎯 You don't have any savings goals yet. Create one below!")

# ─── Create New Goal ─────────────────────────────────────────────────────────
with st.expander("➕ Create New Goal", expanded=len(goals) == 0):
    st.markdown("### 🆕 New Savings Goal")

    col1, col2 = st.columns(2)
    with col1:
        g_name = st.text_input("Goal Name", placeholder="Emergency Fund, Europe Trip, MacBook...")
        g_target = st.number_input("Target Amount (₹)", min_value=1000, step=5000, value=100000)
        g_current = st.number_input("Already Saved (₹)", min_value=0, step=1000, value=0)

    with col2:
        g_desc = st.text_area("Description (optional)", placeholder="What is this goal for?", height=100)
        g_monthly = st.number_input("Monthly Contribution (₹)", min_value=0, step=500, value=5000)
        g_date = st.date_input("Target Date (optional)", value=None)

    # Preview calculation
    if g_target > 0 and g_monthly > 0:
        remaining = g_target - g_current
        months_needed = remaining / g_monthly if g_monthly > 0 else 0
        st.info(f"📅 At ₹{g_monthly:,.0f}/month, you'll reach this goal in **{months_needed:.1f} months** "
                f"(₹{remaining:,.0f} remaining)")

    if st.button("🎯 Create Goal", use_container_width=True, type="primary"):
        if not g_name:
            st.error("Please enter a goal name.")
        else:
            goal_data = {
                "name": g_name,
                "description": g_desc or None,
                "target_amount": float(g_target),
                "current_amount": float(g_current),
                "monthly_contribution": float(g_monthly),
                "target_date": datetime.combine(g_date, datetime.min.time()).isoformat() if g_date else None,
            }
            result = api_create_goal(goal_data)
            if result:
                st.success(f"✅ Goal '{g_name}' created!")
                st.rerun()
