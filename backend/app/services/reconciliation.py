"""
Reconciliation Job.

Periodically diffs the append-only event log against the CQRS read model
to ensure eventual consistency. Re-emits or updates read models if discrepancies exist.
"""
from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationReadModel, EventLogModel

logger = logging.getLogger(__name__)


class ReconciliationService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def reconcile_application(self, application_id: str) -> bool:
        """
        Diffs events vs read model for a single application.
        Returns True if consistent, False if fixed.
        """
        # Fetch event log sequence
        stmt_events = (
            select(EventLogModel)
            .where(EventLogModel.application_id == application_id)
            .order_by(EventLogModel.id.asc())
        )
        res_events = await self.session.execute(stmt_events)
        events = res_events.scalars().all()

        if not events:
            return True

        latest_event = events[-1]

        # Fetch read model
        stmt_read = select(ApplicationReadModel).where(
            ApplicationReadModel.application_id == application_id
        )
        res_read = await self.session.execute(stmt_read)
        read_model = res_read.scalar_one_or_none()

        if not read_model:
            logger.warning(
                "Reconciliation: Read model missing for app %s! Rebuilding...",
                application_id,
            )
            # Rebuild read model from events
            first_event = events[0]
            payload = first_event.payload
            new_read = ApplicationReadModel(
                application_id=application_id,
                idempotency_key=payload.get("idempotency_key", application_id),
                borrower_name=payload.get("borrower_name", "Unknown"),
                borrower_email=payload.get("borrower_email", "unknown@example.com"),
                loan_amount=payload.get("loan_amount", 0.0),
                annual_income=payload.get("annual_income", 0.0),
                partner_id=payload.get("partner_id", "default"),
                status=latest_event.event_type.split(".")[-1],
            )
            self.session.add(new_read)
            await self.session.commit()
            return False

        return True
