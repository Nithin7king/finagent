"""
FinAgent — Alerts & Notifications Page
Shows anomaly alerts, bill reminders, and weekly digests.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Alerts — FinAgent", page_icon="🔔", layout="wide")

from frontend.components.api_client import (
    api_get_alerts, api_mark_alert_read, api_mark_all_alerts_read, api_delete_alert
)

if not st.session_state.get("token"):
    st.warning("⚠️ Please log in first.")
    st.stop()

# ─── Header ──────────────────────────────────────────────────────────────────
col_h, col_act = st.columns([3, 1])
with col_h:
    st.markdown("# 🔔 Alerts & Notifications")
    st.caption("Anomaly warnings, bill reminders, and weekly financial digests")

with col_act:
    col_a, col_b = st.columns(2)
    with col_a:
        unread_only = st.toggle("Unread only", value=False)
    with col_b:
        if st.button("✅ Mark All Read", use_container_width=True):
            if api_mark_all_alerts_read():
                st.success("All alerts marked as read!")
                st.rerun()

st.divider()

# ─── Load Alerts ─────────────────────────────────────────────────────────────
with st.spinner("Loading notifications..."):
    data = api_get_alerts(unread_only=unread_only)

if not data:
    st.error("Could not load alerts. Make sure the backend is running.")
    st.stop()

alerts = data.get("alerts", [])
total = data.get("total", 0)
unread_count = data.get("unread_count", 0)

# ─── Summary badges ──────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3)
m1.metric("Total Alerts", str(total))
m2.metric("Unread", str(unread_count), delta_color="inverse" if unread_count > 0 else "off")
m3.metric("Read", str(total - unread_count))

st.divider()

if not alerts:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0; color: #64748B;">
        <div style="font-size: 4rem;">🎉</div>
        <h3>All clear!</h3>
        <p>No alerts to show. Your finances look good.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Alert Type Tabs ─────────────────────────────────────────────────────────
TYPE_ICONS = {
    "anomaly": ("🚨", "Anomaly"),
    "bill": ("📅", "Bill Reminder"),
    "digest": ("📊", "Weekly Digest"),
    "goal": ("🎯", "Goal Update"),
}

SEVERITY_COLORS = {
    "high":   ("alert-high",   "#FF4B4B"),
    "medium": ("alert-medium", "#FFA500"),
    "low":    ("alert-low",    "#43E97B"),
}

# Group alerts by type
type_counts = {}
for a in alerts:
    t = a.get("alert_type", "other")
    type_counts[t] = type_counts.get(t, 0) + 1

# ─── Alert Cards ─────────────────────────────────────────────────────────────
for alert in alerts:
    alert_type = alert.get("alert_type", "other")
    severity = alert.get("severity", "low")
    is_read = alert.get("is_read", False)
    created_at = alert.get("created_at", "")
    alert_id = alert.get("id")

    icon, type_label = TYPE_ICONS.get(alert_type, ("🔔", "Notification"))
    css_class, color = SEVERITY_COLORS.get(severity, ("alert-low", "#43E97B"))

    # Parse timestamp
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        time_str = dt.strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        time_str = created_at[:10] if created_at else "Unknown"

    opacity = "opacity: 1;" if not is_read else "opacity: 0.65;"

    col_card, col_actions = st.columns([8, 1])
    with col_card:
        st.markdown(
            f"""
            <div class="{css_class}" style="{opacity} border-radius: 0 12px 12px 0; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <b>{icon} {alert['title']}</b>
                    {"&nbsp;&nbsp;<span style='background: rgba(108,99,255,0.2); border-radius: 20px; padding: 2px 8px; font-size: 0.7rem; color: #6C63FF;'>UNREAD</span>" if not is_read else ""}
                </div>
                <span style="color: #64748B; font-size: 0.75rem;">{type_label} · {time_str}</span>
            </div>
            <div style="margin-top: 0.5rem; color: #94A3B8; font-size: 0.9rem;">
                {alert['message'][:400]}{"..." if len(alert.get('message','')) > 400 else ""}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_actions:
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if not is_read:
                if st.button("👁️", key=f"read_{alert_id}", help="Mark as read"):
                    api_mark_alert_read(alert_id)
                    st.rerun()
        with act_col2:
            if st.button("🗑️", key=f"del_{alert_id}", help="Delete alert"):
                api_delete_alert(alert_id)
                st.rerun()

# ─── Alert Type Summary ───────────────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Alert Breakdown")
if type_counts:
    cols = st.columns(len(type_counts))
    for i, (atype, cnt) in enumerate(type_counts.items()):
        icon, label = TYPE_ICONS.get(atype, ("🔔", atype.title()))
        cols[i].metric(f"{icon} {label}", str(cnt))
