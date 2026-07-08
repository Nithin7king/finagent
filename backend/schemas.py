"""
FinAgent — Pydantic Schemas
Request/response models for FastAPI endpoints
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    monthly_income: Optional[float] = 0.0
    currency: Optional[str] = "INR"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    monthly_income: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Transactions ─────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: float
    category: Optional[str] = None
    notes: Optional[str] = None

class TransactionUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    date: datetime
    description: str
    amount: float
    category: str
    ml_category: Optional[str]
    ml_confidence: Optional[float]
    anomaly_score: Optional[float]
    anomaly_label: bool
    anomaly_explanation: Optional[str]
    is_subscription: bool
    subscription_interval_days: Optional[int]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    total: int
    transactions: List[TransactionOut]


# ─── Goals ───────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_amount: float
    current_amount: Optional[float] = 0.0
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = 0.0

class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = None
    is_completed: Optional[bool] = None

class GoalOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_amount: float
    current_amount: float
    target_date: Optional[datetime]
    monthly_contribution: float
    is_completed: bool
    progress_pct: Optional[float] = None
    months_to_goal: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Alerts ──────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics ───────────────────────────────────────────────────────────────

class SpendingSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    by_category: dict

class ForecastResponse(BaseModel):
    period_days: int
    predicted_total: float
    by_category: dict
    confidence: str

class AnomalyResponse(BaseModel):
    transaction_id: int
    description: str
    amount: float
    date: datetime
    anomaly_score: float
    severity: str
    explanation: str

class SubscriptionResponse(BaseModel):
    merchant: str
    amount: float
    interval_days: int
    monthly_cost: float
    last_charge: datetime
    next_expected: Optional[datetime]


# ─── Chat / Agent ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []
    tool_calls_made: Optional[List[str]] = []
    session_id: str
