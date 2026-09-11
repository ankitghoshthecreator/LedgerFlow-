"""
Application Ingestion Service.

Handles idempotency checks, creates the aggregate root, appends the initial event to
the event log, creates the initial read model projection, and publishes the domain event.
"""
from __future__ import annotations

import logging
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.application import LoanApplication
from app.event_bus.base import EventBus
from app.models import ApplicationReadModel
from app.repositories import ApplicationRepository, EventLogRepository
from app.schemas.application import ApplicationCreateRequest

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus,
    ) -> None:
        self.session = session
        self.event_bus = event_bus
        self.app_repo = ApplicationRepository(session)
        self.event_repo = EventLogRepository(session)

    async def ingest_application(
        self, request: ApplicationCreateRequest
    ) -> Tuple[ApplicationReadModel, bool]:
        """
        Ingests a new borrower loan application.

        Returns (read_model, is_new).
        If idempotency_key was seen previously, returns the existing record (is_new=False).
        """
        idempotency_key = request.idempotency_key or f"auto_{request.borrower_email}_{request.loan_amount}"

        # 1. Check idempotency
        existing = await self.app_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            logger.info("Idempotent submission detected for key %s", idempotency_key)
            return existing, False

        # 2. Create Aggregate Root
        app_aggregate = LoanApplication.create(
            borrower_name=request.borrower_name,
            borrower_email=request.borrower_email,
            loan_amount=request.loan_amount,
            annual_income=request.annual_income,
            partner_id=request.partner_id,
            idempotency_key=idempotency_key,
        )

        # 3. Create initial read model
        read_model = ApplicationReadModel(
            application_id=app_aggregate.application_id,
            idempotency_key=app_aggregate.idempotency_key,
            borrower_name=app_aggregate.borrower_name,
            borrower_email=app_aggregate.borrower_email,
            loan_amount=app_aggregate.loan_amount,
            annual_income=app_aggregate.annual_income,
            partner_id=app_aggregate.partner_id,
            status=app_aggregate.status.value,
        )
        await self.app_repo.save(read_model)

        # 4. Collect domain events & save to Event Log
        events = app_aggregate.collect_events()
        for event in events:
            await self.event_repo.append(event)

        await self.session.commit()

        # 5. Publish event to Event Bus (triggers Saga Orchestrator)
        for event in events:
            await self.event_bus.publish(event)

        logger.info(
            "Successfully ingested application %s (key=%s)",
            app_aggregate.application_id,
            idempotency_key,
        )
        return read_model, True
