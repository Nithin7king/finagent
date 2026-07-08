"""
FinAgent — API Client
Communicates with FastAPI backend from Streamlit frontend.
Handles auth token management and all API calls.
"""
import os
import requests
import streamlit as st
from typing import Optional, Dict, Any

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def _headers() -> Dict[str, str]:
    """Build auth headers from stored token."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _get(path: str, params: Optional[Dict] = None) -> Optional[Dict]:
    try:
        r = requests.get(f"{API_BASE}{path}", headers=_headers(), params=params, timeout=30)
        if r.status_code == 401:
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def _post(path: str, data: Dict) -> Optional[Dict]:
    try:
        r = requests.post(f"{API_BASE}{path}", headers=_headers(), json=data, timeout=30)
        if r.status_code == 401:
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()
        if not r.ok:
            detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
            st.error(f"Error: {detail}")
            return None
        return r.json()
    except requests.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def _put(path: str, data: Dict) -> Optional[Dict]:
    try:
        r = requests.put(f"{API_BASE}{path}", headers=_headers(), json=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def _delete(path: str) -> bool:
    try:
        r = requests.delete(f"{API_BASE}{path}", headers=_headers(), timeout=30)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"API Error: {e}")
        return False


# ─── Auth ─────────────────────────────────────────────────────────────────────

def api_register(name: str, email: str, password: str, income: float) -> Optional[Dict]:
    return _post("/auth/register", {
        "name": name, "email": email, "password": password,
        "monthly_income": income, "currency": "INR",
    })


def api_login(email: str, password: str) -> Optional[Dict]:
    return _post("/auth/login", {"email": email, "password": password})


def api_me() -> Optional[Dict]:
    return _get("/auth/me")


# ─── Transactions ─────────────────────────────────────────────────────────────

def api_get_transactions(days: int = 30, category: str = None, page: int = 1, per_page: int = 50, anomaly_only: bool = False) -> Optional[Dict]:
    params = {"days": days, "page": page, "per_page": per_page}
    if category:
        params["category"] = category
    if anomaly_only:
        params["anomaly_only"] = "true"
    return _get("/transactions", params=params)


def api_upload_csv(file_bytes: bytes, filename: str) -> Optional[Dict]:
    try:
        r = requests.post(
            f"{API_BASE}/transactions/upload-csv",
            headers=_headers(),
            files={"file": (filename, file_bytes, "text/csv")},
            timeout=60,
        )
        if not r.ok:
            st.error(f"Upload failed: {r.json().get('detail', r.text)}")
            return None
        return r.json()
    except requests.RequestException as e:
        st.error(f"Upload error: {e}")
        return None


def api_update_transaction(txn_id: int, data: Dict) -> Optional[Dict]:
    return _put(f"/transactions/{txn_id}", data)


# ─── Analytics ────────────────────────────────────────────────────────────────

def api_get_summary(days: int = 30) -> Optional[Dict]:
    return _get("/analytics/summary", params={"days": days})


def api_get_forecast(horizon: int = 30) -> Optional[Dict]:
    return _get("/analytics/forecast", params={"horizon_days": horizon})


def api_get_spending_trend(months: int = 6) -> Optional[Dict]:
    return _get("/analytics/spending-trend", params={"months": months})


def api_get_anomalies(days: int = 30) -> Optional[Dict]:
    return _get("/analytics/anomalies", params={"days": days})


def api_get_subscriptions() -> Optional[Dict]:
    return _get("/analytics/subscriptions")


def api_train_models() -> Optional[Dict]:
    return _post("/analytics/train-models", {})


def api_what_if(category: str, reduction_pct: float) -> Optional[Dict]:
    return _get("/analytics/what-if", params={"category": category, "reduction_pct": reduction_pct})


# ─── Goals ────────────────────────────────────────────────────────────────────

def api_get_goals() -> Optional[Dict]:
    return _get("/goals")


def api_create_goal(data: Dict) -> Optional[Dict]:
    return _post("/goals", data)


def api_update_goal(goal_id: int, data: Dict) -> Optional[Dict]:
    return _put(f"/goals/{goal_id}", data)


def api_delete_goal(goal_id: int) -> bool:
    return _delete(f"/goals/{goal_id}")


def api_contribute_to_goal(goal_id: int, amount: float) -> Optional[Dict]:
    return _post(f"/goals/{goal_id}/contribute", {"amount": amount})


# ─── Chat ─────────────────────────────────────────────────────────────────────

def api_chat(message: str, session_id: Optional[str] = None) -> Optional[Dict]:
    return _post("/chat", {"message": message, "session_id": session_id})


def api_get_digest() -> Optional[Dict]:
    return _get("/chat/digest")


# ─── Alerts ───────────────────────────────────────────────────────────────────

def api_get_alerts(unread_only: bool = False) -> Optional[Dict]:
    return _get("/alerts", params={"unread_only": str(unread_only).lower()})


def api_mark_alert_read(alert_id: int) -> bool:
    result = _post(f"/alerts/{alert_id}/read", {})
    return result is not None


def api_mark_all_alerts_read() -> bool:
    result = _post("/alerts/read-all", {})
    return result is not None


def api_delete_alert(alert_id: int) -> bool:
    return _delete(f"/alerts/{alert_id}")


def api_get_unread_count() -> int:
    result = _get("/alerts/unread-count")
    return result.get("unread_count", 0) if result else 0


# ─── Profile ──────────────────────────────────────────────────────────────────

def api_update_profile(data: Dict) -> Optional[Dict]:
    return _put("/profile", data)


def api_change_password(current_password: str, new_password: str) -> Optional[Dict]:
    return _post("/profile/change-password", {
        "current_password": current_password,
        "new_password": new_password,
    })


def api_get_profile_stats() -> Optional[Dict]:
    return _get("/profile/stats")


# ─── Export ───────────────────────────────────────────────────────────────────

def api_export_transactions_url(days: int = 90) -> str:
    """Return the direct export URL (for download button)."""
    token = st.session_state.get("token", "")
    return f"{API_BASE}/transactions/export?days={days}&token={token}"
