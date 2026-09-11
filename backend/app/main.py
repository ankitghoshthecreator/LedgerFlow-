"""
LedgerFlow FastAPI Application Factory.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.api.v1.applications import set_global_event_bus
from app.config import get_settings
from app.database import create_all_tables
from app.domain.events import (
    ApplicationSubmitted,
    CreditScoreFetched,
    KYCVerified,
    RiskScored,
)
from app.event_bus.in_process import InProcessEventBus
from app.saga.orchestrator import SagaOrchestrator

settings = get_settings()
global_bus = InProcessEventBus()
orchestrator = SagaOrchestrator(global_bus)

# Wire Saga Handlers to Event Bus
global_bus.subscribe(ApplicationSubmitted, orchestrator.handle_application_submitted)
global_bus.subscribe(KYCVerified, orchestrator.handle_kyc_verified)
global_bus.subscribe(CreditScoreFetched, orchestrator.handle_credit_score_fetched)
global_bus.subscribe(RiskScored, orchestrator.handle_risk_scored)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_all_tables()
    await global_bus.start()
    set_global_event_bus(global_bus)
    yield
    # Shutdown
    await global_bus.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Event-Driven Loan Underwriting & Risk Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api")


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }
