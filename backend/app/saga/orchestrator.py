"""
Saga Orchestrator.

Listens for domain events, determines the next step in the loan underwriting flow,
coordinates signal fetching / risk engine evaluation, and publishes compensating events on failure.

State Flow:
ApplicationSubmitted ──> KYC Check
KYCVerified          ──> Credit Bureau Fetch
CreditScoreFetched   ──> Risk Rules Evaluation
RiskScored           ──> Decision (Approve/Reject)
Approved             ──> Disbursal Initiated ──> Disbursal Completed
"""
from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.domain.enums import DecisionType, RejectionReason
from app.domain.events import (
    ApplicationSubmitted,
    CreditScoreFetched,
    DecisionMade,
    DisbursalInitiated,
    DomainEvent,
    KYCVerified,
    RiskScored,
)
from app.event_bus.base import EventBus
from app.repositories import ApplicationRepository, EventLogRepository
from app.saga.compensations import SagaCompensator
from app.services.mocks import CreditBureauService, DisbursalService, KYCService
from app.services.risk_engine import RiskEngineService

logger = logging.getLogger(__name__)


class SagaOrchestrator:
    """Core Saga Coordinator orchestrating the loan application lifecycle."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.kyc_service = KYCService()
        self.credit_bureau = CreditBureauService()
        self.disbursal_service = DisbursalService()
        self.risk_engine = RiskEngineService()

    def register_listeners() -> None:
        """Helper method — register saga step handlers on event bus."""

    async def handle_application_submitted(self, event: ApplicationSubmitted) -> None:
        """Step 1: ApplicationSubmitted -> Perform KYC."""
        logger.info("Saga [Step 1]: ApplicationSubmitted for %s", event.application_id)
        async with AsyncSessionLocal() as session:
            app_repo = ApplicationRepository(session)
            event_repo = EventLogRepository(session)
            compensator = SagaCompensator(session)

            read_model = await app_repo.get_by_id(event.application_id)
            if not read_model:
                return

            read_model.status = "kyc_in_progress"
            await app_repo.save(read_model)
            await session.commit()

            # Execute KYC
            passed, detail = await self.kyc_service.verify_identity(
                event.borrower_name, event.borrower_email
            )

            if not passed:
                comp_event = await compensator.compensate_kyc_failure(event.application_id, detail)
                await self.event_bus.publish(comp_event)
                return

            # KYC Passed -> emit KYCVerified
            next_event = KYCVerified(
                application_id=event.application_id,
                verified_name=event.borrower_name,
                correlation_id=event.correlation_id,
            )
            await event_repo.append(next_event)

            read_model.status = "credit_fetching"
            await app_repo.save(read_model)
            await session.commit()

            await self.event_bus.publish(next_event)

    async def handle_kyc_verified(self, event: KYCVerified) -> None:
        """Step 2: KYCVerified -> Fetch Credit Score & DTI."""
        logger.info("Saga [Step 2]: KYC Verified for %s. Fetching Credit Score...", event.application_id)
        async with AsyncSessionLocal() as session:
            app_repo = ApplicationRepository(session)
            event_repo = EventLogRepository(session)
            compensator = SagaCompensator(session)

            read_model = await app_repo.get_by_id(event.application_id)
            if not read_model:
                return

            success, credit_score, dti, detail = await self.credit_bureau.fetch_credit_profile(
                read_model.borrower_email
            )

            if not success:
                comp_event = await compensator.compensate_credit_fetch_failure(event.application_id, detail)
                await self.event_bus.publish(comp_event)
                return

            read_model.credit_score = credit_score
            read_model.debt_to_income = dti
            read_model.status = "risk_scoring"
            await app_repo.save(read_model)

            next_event = CreditScoreFetched(
                application_id=event.application_id,
                credit_score=credit_score,
                debt_to_income=dti,
                correlation_id=event.correlation_id,
            )
            await event_repo.append(next_event)
            await session.commit()

            await self.event_bus.publish(next_event)

    async def handle_credit_score_fetched(self, event: CreditScoreFetched) -> None:
        """Step 3: CreditScoreFetched -> Evaluate Risk Rules."""
        logger.info("Saga [Step 3]: Credit Score fetched for %s (%d). Evaluating Risk...", event.application_id, event.credit_score)
        async with AsyncSessionLocal() as session:
            app_repo = ApplicationRepository(session)
            event_repo = EventLogRepository(session)

            read_model = await app_repo.get_by_id(event.application_id)
            if not read_model:
                return

            risk_result = await self.risk_engine.evaluate(
                session=session,
                partner_id=read_model.partner_id,
                credit_score=event.credit_score,
                debt_to_income=event.debt_to_income,
                loan_amount=read_model.loan_amount,
                annual_income=read_model.annual_income,
            )

            read_model.risk_score = risk_result.risk_score
            read_model.status = "decision_pending"
            await app_repo.save(read_model)

            next_event = RiskScored(
                application_id=event.application_id,
                risk_score=risk_result.risk_score,
                rules_passed=risk_result.rules_passed,
                rules_failed=risk_result.rules_failed,
                partner_id=read_model.partner_id,
                correlation_id=event.correlation_id,
            )
            await event_repo.append(next_event)
            await session.commit()

            await self.event_bus.publish(next_event)

    async def handle_risk_scored(self, event: RiskScored) -> None:
        """Step 4: RiskScored -> Decision & Disbursal."""
        logger.info("Saga [Step 4]: Risk Scored for %s (score=%.2f). Making Decision...", event.application_id, event.risk_score)
        async with AsyncSessionLocal() as session:
            app_repo = ApplicationRepository(session)
            event_repo = EventLogRepository(session)

            read_model = await app_repo.get_by_id(event.application_id)
            if not read_model:
                return

            if len(event.rules_failed) == 0:
                # Approve!
                read_model.status = "approved"
                read_model.decision = "approved"
                await app_repo.save(read_model)

                decision_event = DecisionMade(
                    application_id=event.application_id,
                    decision=DecisionType.APPROVED,
                    reason="All partner risk rules passed",
                    risk_score=event.risk_score,
                    correlation_id=event.correlation_id,
                )
                await event_repo.append(decision_event)

                # Initiate Disbursal
                success, tx_id = await self.disbursal_service.initiate_disbursal(
                    event.application_id, read_model.loan_amount
                )
                read_model.status = "disbursal_completed"
                await app_repo.save(read_model)

                disbursal_event = DisbursalInitiated(
                    application_id=event.application_id,
                    amount=read_model.loan_amount,
                    account_ref=tx_id,
                    correlation_id=event.correlation_id,
                )
                await event_repo.append(disbursal_event)
                await session.commit()

                await self.event_bus.publish(decision_event)
                await self.event_bus.publish(disbursal_event)
            else:
                # Reject
                reasons = ", ".join(event.rules_failed)
                read_model.status = "rejected"
                read_model.decision = "rejected"
                read_model.rejection_reason = reasons
                await app_repo.save(read_model)

                decision_event = DecisionMade(
                    application_id=event.application_id,
                    decision=DecisionType.REJECTED,
                    reason=f"Failed risk rules: {reasons}",
                    risk_score=event.risk_score,
                    correlation_id=event.correlation_id,
                )
                await event_repo.append(decision_event)
                await session.commit()

                await self.event_bus.publish(decision_event)
