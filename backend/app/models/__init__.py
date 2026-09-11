"""
ORM Models for LedgerFlow.

1. EventLog: Append-only source-of-truth event store.
2. ApplicationReadModel: Denormalized CQRS read view for fast queries.
3. PartnerRulesModel: Multi-tenant risk evaluation rule sets.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventLogModel(Base):
    """Append-only store for domain events."""
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    application_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, default=_utc_now)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utc_now)


class ApplicationReadModel(Base):
    """Denormalized read-optimized view for queries & dashboard."""
    __tablename__ = "application_read_model"

    application_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    borrower_name: Mapped[str] = mapped_column(String(200), nullable=False)
    borrower_email: Mapped[str] = mapped_column(String(200), nullable=False)
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    partner_id: Mapped[str] = mapped_column(String(50), nullable=False, default="default", index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="submitted", index=True)
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    debt_to_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=_utc_now, onupdate=_utc_now)


class PartnerRulesModel(Base):
    """Partner-specific JSON risk evaluation rules."""
    __tablename__ = "partner_rules"

    partner_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    partner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=_utc_now, onupdate=_utc_now)
