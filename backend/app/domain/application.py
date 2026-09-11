"""
LoanApplication — the core aggregate root.

Encapsulates all state transitions and enforces invariants.
No direct DB writes here — the aggregate raises domain events;
the saga + projector persist them.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.enums import ApplicationStatus, DecisionType, RejectionReason
from app.domain.events import (
    ApplicationRejected,
    ApplicationSubmitted,
    CreditScoreFetched,
    DecisionMade,
    DisbursalCompleted,
    DisbursalInitiated,
    DomainEvent,
    KYCFailed,
    KYCVerified,
    ManualReviewQueued,
    RiskScored,
)


@dataclass
class LoanApplication:
    """
    Aggregate root for a loan application.

    Follows the OOP aggregate pattern: all state mutations go through
    named methods that validate the transition and record an event.
    """

    # Identity
    application_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str = ""

    # Borrower
    borrower_name: str = ""
    borrower_email: str = ""
    loan_amount: float = 0.0
    annual_income: float = 0.0
    partner_id: str = "default"

    # Lifecycle
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    decision: DecisionType | None = None
    rejection_reason: RejectionReason | None = None

    # Signals captured during saga
    credit_score: int | None = None
    debt_to_income: float | None = None
    risk_score: float | None = None

    # Timestamps
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None
    disbursed_at: datetime | None = None

    # Uncommitted events — drained by the orchestrator after each step
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        borrower_name: str,
        borrower_email: str,
        loan_amount: float,
        annual_income: float,
        partner_id: str = "default",
        idempotency_key: str = "",
    ) -> "LoanApplication":
        app = cls(
            borrower_name=borrower_name,
            borrower_email=borrower_email,
            loan_amount=loan_amount,
            annual_income=annual_income,
            partner_id=partner_id,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )
        event = ApplicationSubmitted(
            application_id=app.application_id,
            borrower_name=borrower_name,
            borrower_email=borrower_email,
            loan_amount=loan_amount,
            annual_income=annual_income,
            partner_id=partner_id,
            idempotency_key=app.idempotency_key,
        )
        app._events.append(event)
        return app

    # ── Saga transition methods ───────────────────────────────────────────────

    def mark_kyc_in_progress(self) -> None:
        self._assert_status(ApplicationStatus.SUBMITTED)
        self.status = ApplicationStatus.KYC_IN_PROGRESS

    def mark_kyc_verified(self, verified_name: str) -> KYCVerified:
        self._assert_status(ApplicationStatus.KYC_IN_PROGRESS)
        self.status = ApplicationStatus.CREDIT_FETCHING
        event = KYCVerified(
            application_id=self.application_id,
            verified_name=verified_name,
        )
        self._events.append(event)
        return event

    def mark_kyc_failed(self, reason: str) -> KYCFailed:
        self._assert_status(ApplicationStatus.KYC_IN_PROGRESS)
        self.status = ApplicationStatus.KYC_FAILED
        event = KYCFailed(application_id=self.application_id, reason=reason)
        self._events.append(event)
        return event

    def mark_credit_score_fetched(
        self, credit_score: int, debt_to_income: float
    ) -> CreditScoreFetched:
        self.status = ApplicationStatus.RISK_SCORING
        self.credit_score = credit_score
        self.debt_to_income = debt_to_income
        event = CreditScoreFetched(
            application_id=self.application_id,
            credit_score=credit_score,
            debt_to_income=debt_to_income,
        )
        self._events.append(event)
        return event

    def mark_risk_scored(
        self,
        risk_score: float,
        rules_passed: list[str],
        rules_failed: list[str],
    ) -> RiskScored:
        self.status = ApplicationStatus.DECISION_PENDING
        self.risk_score = risk_score
        event = RiskScored(
            application_id=self.application_id,
            risk_score=risk_score,
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            partner_id=self.partner_id,
        )
        self._events.append(event)
        return event

    def approve(self) -> DecisionMade:
        self.status = ApplicationStatus.APPROVED
        self.decision = DecisionType.APPROVED
        self.decided_at = datetime.now(timezone.utc)
        event = DecisionMade(
            application_id=self.application_id,
            decision=DecisionType.APPROVED,
            reason="All risk rules passed",
            risk_score=self.risk_score or 0.0,
        )
        self._events.append(event)
        return event

    def reject(self, reason: RejectionReason, detail: str = "") -> ApplicationRejected:
        self.status = ApplicationStatus.REJECTED
        self.decision = DecisionType.REJECTED
        self.rejection_reason = reason
        self.decided_at = datetime.now(timezone.utc)
        event = ApplicationRejected(
            application_id=self.application_id,
            reason=reason,
            detail=detail,
        )
        self._events.append(event)
        return event

    def queue_for_manual_review(self, reason: str) -> ManualReviewQueued:
        self.status = ApplicationStatus.MANUAL_REVIEW
        self.decision = DecisionType.MANUAL_REVIEW
        event = ManualReviewQueued(application_id=self.application_id, reason=reason)
        self._events.append(event)
        return event

    def initiate_disbursal(self, account_ref: str) -> DisbursalInitiated:
        self._assert_status(ApplicationStatus.APPROVED)
        self.status = ApplicationStatus.DISBURSAL_INITIATED
        event = DisbursalInitiated(
            application_id=self.application_id,
            amount=self.loan_amount,
            account_ref=account_ref,
        )
        self._events.append(event)
        return event

    def complete_disbursal(self, transaction_id: str) -> DisbursalCompleted:
        self._assert_status(ApplicationStatus.DISBURSAL_INITIATED)
        self.status = ApplicationStatus.DISBURSAL_COMPLETED
        self.disbursed_at = datetime.now(timezone.utc)
        event = DisbursalCompleted(
            application_id=self.application_id,
            transaction_id=transaction_id,
            amount=self.loan_amount,
        )
        self._events.append(event)
        return event

    # ── Event management ─────────────────────────────────────────────────────

    def collect_events(self) -> list[DomainEvent]:
        """Drain and return uncommitted events."""
        events, self._events = self._events, []
        return events

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _assert_status(self, expected: ApplicationStatus) -> None:
        if self.status != expected:
            raise ValueError(
                f"Expected status {expected!r}, got {self.status!r} "
                f"for application {self.application_id}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "borrower_name": self.borrower_name,
            "borrower_email": self.borrower_email,
            "loan_amount": self.loan_amount,
            "annual_income": self.annual_income,
            "partner_id": self.partner_id,
            "status": self.status.value,
            "decision": self.decision.value if self.decision else None,
            "credit_score": self.credit_score,
            "debt_to_income": self.debt_to_income,
            "risk_score": self.risk_score,
            "submitted_at": self.submitted_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }
