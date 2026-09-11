"""Pydantic Request and Response Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ApplicationCreateRequest(BaseModel):
    borrower_name: str = Field(..., min_length=2, max_length=200, example="John Doe")
    borrower_email: EmailStr = Field(..., example="john.doe@example.com")
    loan_amount: float = Field(..., gt=0, example=50000.0)
    annual_income: float = Field(..., gt=0, example=120000.0)
    partner_id: str = Field(default="default", example="partner_a")
    idempotency_key: str | None = Field(
        default=None,
        description="Unique client-supplied key for idempotency",
        example="req_987654321",
    )


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    idempotency_key: str
    borrower_name: str
    borrower_email: str
    loan_amount: float
    annual_income: float
    partner_id: str
    status: str
    decision: str | None = None
    rejection_reason: str | None = None
    credit_score: int | None = None
    debt_to_income: float | None = None
    risk_score: float | None = None
    submitted_at: datetime
    updated_at: datetime


class EventLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    application_id: str
    event_type: str
    correlation_id: str
    payload: dict[str, Any]
    occurred_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    timeline: list[EventLogResponse] = []
