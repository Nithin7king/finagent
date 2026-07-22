"""
FinAgent — SQLAlchemy ORM Models
Tables: users, transactions, goals, alerts, agent_memory
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
import enum

from backend.database import Base


class TransactionCategory(str, enum.Enum):
    FOOD = "Food & Dining"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    UTILITIES = "Utilities & Bills"
    HEALTHCARE = "Healthcare"
    ENTERTAINMENT = "Entertainment"
    INCOME = "Income"
    INVESTMENTS = "Investments"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    OTHER = "Other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    monthly_income = Column(Float, default=0.0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("AgentMemory", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Core fields
    date = Column(DateTime, nullable=False, index=True)
    description = Column(String, nullable=False)          # merchant name / note
    amount = Column(Float, nullable=False)                 # negative = expense, positive = income
    category = Column(String, default="Other")
    subcategory = Column(String, nullable=True)

    # ML-derived fields
    ml_category = Column(String, nullable=True)           # ML-predicted category
    ml_confidence = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)          # 0–1, higher = more anomalous
    anomaly_label = Column(Boolean, default=False)
    anomaly_explanation = Column(Text, nullable=True)
    is_subscription = Column(Boolean, default=False)
    subscription_interval_days = Column(Integer, nullable=True)

    # Encrypted sensitive fields (stored as hex string)
    encrypted_notes = Column(Text, nullable=True)         # AES-256 encrypted

    # Metadata
    source = Column(String, default="manual")             # manual | csv | synthetic
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True)
    monthly_contribution = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    alert_type = Column(String, nullable=False)           # anomaly | bill | goal | digest
    severity = Column(String, default="medium")           # low | medium | high
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String, nullable=True)            # NULL = persistent memory

    role = Column(String, nullable=False)                 # user | assistant | system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")           # low | medium | high
    is_actioned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
