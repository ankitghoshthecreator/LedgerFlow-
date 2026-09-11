"""
Data access layer (Repositories) following OOP principles.
"""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import DomainEvent
from app.models import ApplicationReadModel, EventLogModel, PartnerRulesModel


class EventLogRepository:
    """Repository for managing immutable domain event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, event: DomainEvent) -> EventLogModel:
        event_dict = event.to_dict()
        record = EventLogModel(
            event_id=event.event_id,
            application_id=getattr(event, "application_id", ""),
            event_type=event.event_type.value,
            correlation_id=event.correlation_id,
            payload=event_dict,
            occurred_at=event.occurred_at,
        )
        self.session.add(record)
        return record

    async def get_by_application_id(self, application_id: str) -> Sequence[EventLogModel]:
        stmt = (
            select(EventLogModel)
            .where(EventLogModel.application_id == application_id)
            .order_by(EventLogModel.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ApplicationRepository:
    """Repository for querying and persisting CQRS read models."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, application_id: str) -> ApplicationReadModel | None:
        stmt = select(ApplicationReadModel).where(ApplicationReadModel.application_id == application_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> ApplicationReadModel | None:
        stmt = select(ApplicationReadModel).where(ApplicationReadModel.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, read_model: ApplicationReadModel) -> ApplicationReadModel:
        self.session.add(read_model)
        return read_model

    async def list_all(self, limit: int = 50, offset: int = 0) -> Sequence[ApplicationReadModel]:
        stmt = (
            select(ApplicationReadModel)
            .order_by(ApplicationReadModel.submitted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PartnerRulesRepository:
    """Repository for managing partner risk rules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_partner_id(self, partner_id: str) -> PartnerRulesModel | None:
        stmt = select(PartnerRulesModel).where(PartnerRulesModel.partner_id == partner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, partner_id: str, partner_name: str, rules: dict) -> PartnerRulesModel:
        existing = await self.get_by_partner_id(partner_id)
        if existing:
            existing.partner_name = partner_name
            existing.rules = rules
            return existing

        new_rules = PartnerRulesModel(
            partner_id=partner_id,
            partner_name=partner_name,
            rules=rules,
        )
        self.session.add(new_rules)
        return new_rules
