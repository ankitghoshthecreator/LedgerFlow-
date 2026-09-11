"""
CQRS Query Router & Application Details API.

Fast denormalized queries backed by ApplicationReadModel, plus event timeline log.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import ApplicationRepository, EventLogRepository
from app.schemas.application import ApplicationDetailResponse, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["CQRS Read Model"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Any:
    repo = ApplicationRepository(db)
    models = await repo.list_all(limit=limit, offset=offset)
    return [ApplicationResponse.model_validate(m) for m in models]


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application_detail(
    application_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    app_repo = ApplicationRepository(db)
    event_repo = EventLogRepository(db)

    read_model = await app_repo.get_by_id(application_id)
    if not read_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    events = await event_repo.get_by_application_id(application_id)

    response_dict = ApplicationResponse.model_validate(read_model).model_dump()
    response_dict["timeline"] = [
        {
            "event_id": e.event_id,
            "application_id": e.application_id,
            "event_type": e.event_type,
            "correlation_id": e.correlation_id,
            "payload": e.payload,
            "occurred_at": e.occurred_at,
        }
        for e in events
    ]

    return response_dict
