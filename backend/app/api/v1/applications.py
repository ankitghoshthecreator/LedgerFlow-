"""API Router for Loan Applications."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.event_bus.base import EventBus
from app.schemas.application import ApplicationCreateRequest, ApplicationResponse
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/applications", tags=["Applications"])

# Global event bus reference set on app startup
_global_event_bus: EventBus | None = None


def set_global_event_bus(bus: EventBus) -> None:
    global _global_event_bus
    _global_event_bus = bus


def get_event_bus() -> EventBus:
    if _global_event_bus is None:
        raise RuntimeError("Event bus is not initialized")
    return _global_event_bus


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new loan application",
    description="Builds entry point for borrower applications with basic validation, idempotency, and publishes application.submitted event.",
)
async def submit_application(
    request: ApplicationCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> ApplicationResponse:
    ingestion_service = IngestionService(db, event_bus)
    read_model, is_new = await ingestion_service.ingest_application(request)
    return ApplicationResponse.model_validate(read_model)
