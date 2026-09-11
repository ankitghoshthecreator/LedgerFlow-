"""Domain enums — application lifecycle states and decision types."""
from __future__ import annotations

from enum import StrEnum


class ApplicationStatus(StrEnum):
    """
    Lifecycle states of a loan application.
    The saga drives transitions between these states.
    """
    SUBMITTED = "submitted"
    KYC_IN_PROGRESS = "kyc_in_progress"
    KYC_FAILED = "kyc_failed"
    CREDIT_FETCHING = "credit_fetching"
    CREDIT_FETCH_FAILED = "credit_fetch_failed"
    RISK_SCORING = "risk_scoring"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSAL_INITIATED = "disbursal_initiated"
    DISBURSAL_COMPLETED = "disbursal_completed"
    MANUAL_REVIEW = "manual_review"


class DecisionType(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class RejectionReason(StrEnum):
    KYC_FAILED = "kyc_failed"
    LOW_CREDIT_SCORE = "low_credit_score"
    HIGH_DTI = "high_debt_to_income_ratio"
    LOAN_AMOUNT_TOO_HIGH = "loan_amount_exceeds_income_multiple"
    RULE_EVALUATION_FAILED = "rule_evaluation_failed"
    CREDIT_BUREAU_UNAVAILABLE = "credit_bureau_unavailable"


class EventType(StrEnum):
    APPLICATION_SUBMITTED = "application.submitted"
    KYC_VERIFIED = "kyc.verified"
    KYC_FAILED = "kyc.failed"
    CREDIT_SCORE_FETCHED = "credit_score.fetched"
    CREDIT_SCORE_FETCH_FAILED = "credit_score.fetch_failed"
    RISK_SCORED = "risk.scored"
    DECISION_MADE = "decision.made"
    DISBURSAL_INITIATED = "disbursal.initiated"
    DISBURSAL_COMPLETED = "disbursal.completed"
    APPLICATION_REJECTED = "application.rejected"
    MANUAL_REVIEW_QUEUED = "manual_review.queued"
