"""
Saga Compensating Actions.

Invoked when a downstream step in the underwriting workflow fails.
Ensures application state is never left stuck in an inconsistent or floating state.
"""
from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.application import LoanApplication
from app.domain.enums import RejectionReason
from app.domain.events import ApplicationRejected, ManualReviewQueued
from app.repositories import ApplicationRepository, EventLogRepository

logger = logging.getLogger(__name__)


class SagaCompensator:
    """Executes compensating actions upon workflow failure."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.app_repo = ApplicationRepository(session)
        self.event_repo = EventLogRepository(session)

    async def compensate_kyc_failure(
        self, application_id: str, reason: str
    ) -> ApplicationRejected:
        logger.warning("Compensating KYC failure for app %s: %s", application_id, reason)
        read_model = await self.app_repo.get_by_id(application_id)
        if read_model:
            read_model.status = "rejected"
            read_model.decision = "rejected"
            read_model.rejection_reason = RejectionReason.KYC_FAILED.value
            await self.app_repo.save(read_model)

        event = ApplicationRejected(
            application_id=application_id,
            reason=RejectionReason.KYC_FAILED,
            detail=reason,
        )
        await self.event_repo.append(event)
        await self.session.commit()
        return event

    async def compensate_credit_fetch_failure(
        self, application_id: str, reason: str
    ) -> ManualReviewQueued:
        logger.warning(
            "Credit bureau timed out/failed for app %s. Routing to manual review.", application_id
        )
        read_model = await self.app_repo.get_by_id(application_id)
        if read_model:
            read_model.status = "manual_review"
            read_model.decision = "manual_review"
            read_model.rejection_reason = RejectionReason.CREDIT_BUREAU_UNAVAILABLE.value
            await self.app_repo.save(read_model)

        event = ManualReviewQueued(
            application_id=application_id,
            reason=f"Credit bureau unavailable: {reason}",
        )
        await self.event_repo.append(event)
        await self.session.commit()
        return event
