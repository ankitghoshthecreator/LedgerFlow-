"""
Domain events — the language of LedgerFlow.

All events are immutable dataclasses. They are the source of truth;
the read model is derived from them.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.enums import DecisionType, EventType, RejectionReason


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ─── Base ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events. Immutable by design."""
    event_id: str = field(default_factory=_new_id)
    occurred_at: datetime = field(default_factory=_now)
    correlation_id: str = field(default_factory=_new_id)  # ties saga steps together

    @property
    def event_type(self) -> EventType:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "occurred_at": self.occurred_at.isoformat(),
            "correlation_id": self.correlation_id,
        }


# ─── Application ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ApplicationSubmitted(DomainEvent):
    application_id: str = ""
    borrower_name: str = ""
    borrower_email: str = ""
    loan_amount: float = 0.0
    annual_income: float = 0.0
    partner_id: str = "default"
    idempotency_key: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.APPLICATION_SUBMITTED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "borrower_name": self.borrower_name,
            "borrower_email": self.borrower_email,
            "loan_amount": self.loan_amount,
            "annual_income": self.annual_income,
            "partner_id": self.partner_id,
            "idempotency_key": self.idempotency_key,
        }


# ─── KYC ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KYCVerified(DomainEvent):
    application_id: str = ""
    kyc_provider: str = "mock"
    verified_name: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.KYC_VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "kyc_provider": self.kyc_provider,
            "verified_name": self.verified_name,
        }


@dataclass(frozen=True)
class KYCFailed(DomainEvent):
    application_id: str = ""
    reason: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.KYC_FAILED

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "application_id": self.application_id, "reason": self.reason}


# ─── Credit Score ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CreditScoreFetched(DomainEvent):
    application_id: str = ""
    credit_score: int = 0
    debt_to_income: float = 0.0
    bureau: str = "mock_bureau"

    @property
    def event_type(self) -> EventType:
        return EventType.CREDIT_SCORE_FETCHED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "credit_score": self.credit_score,
            "debt_to_income": self.debt_to_income,
            "bureau": self.bureau,
        }


@dataclass(frozen=True)
class CreditScoreFetchFailed(DomainEvent):
    application_id: str = ""
    reason: str = ""
    retry_count: int = 0

    @property
    def event_type(self) -> EventType:
        return EventType.CREDIT_SCORE_FETCH_FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "reason": self.reason,
            "retry_count": self.retry_count,
        }


# ─── Risk ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RiskScored(DomainEvent):
    application_id: str = ""
    risk_score: float = 0.0          # 0.0 (safe) → 1.0 (risky)
    rules_passed: list[str] = field(default_factory=list)
    rules_failed: list[str] = field(default_factory=list)
    partner_id: str = "default"

    @property
    def event_type(self) -> EventType:
        return EventType.RISK_SCORED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "risk_score": self.risk_score,
            "rules_passed": self.rules_passed,
            "rules_failed": self.rules_failed,
            "partner_id": self.partner_id,
        }


# ─── Decision ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionMade(DomainEvent):
    application_id: str = ""
    decision: DecisionType = DecisionType.REJECTED
    reason: str = ""
    risk_score: float = 0.0

    @property
    def event_type(self) -> EventType:
        return EventType.DECISION_MADE

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "risk_score": self.risk_score,
        }


# ─── Disbursal ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DisbursalInitiated(DomainEvent):
    application_id: str = ""
    amount: float = 0.0
    account_ref: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.DISBURSAL_INITIATED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "amount": self.amount,
            "account_ref": self.account_ref,
        }


@dataclass(frozen=True)
class DisbursalCompleted(DomainEvent):
    application_id: str = ""
    transaction_id: str = ""
    amount: float = 0.0

    @property
    def event_type(self) -> EventType:
        return EventType.DISBURSAL_COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
        }


# ─── Rejection / Manual Review ────────────────────────────────────────────────

@dataclass(frozen=True)
class ApplicationRejected(DomainEvent):
    application_id: str = ""
    reason: RejectionReason = RejectionReason.KYC_FAILED
    detail: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.APPLICATION_REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "reason": self.reason.value,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ManualReviewQueued(DomainEvent):
    application_id: str = ""
    reason: str = ""

    @property
    def event_type(self) -> EventType:
        return EventType.MANUAL_REVIEW_QUEUED

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "application_id": self.application_id,
            "reason": self.reason,
        }
