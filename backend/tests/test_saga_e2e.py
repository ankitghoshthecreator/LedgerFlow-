"""End-to-End Saga Integration Test."""
import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, engine
from app.event_bus.in_process import InProcessEventBus
from app.main import app, global_bus
from app.api.v1.applications import set_global_event_bus


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await global_bus.start()
    set_global_event_bus(global_bus)
    yield
    await global_bus.stop()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_full_saga_approval_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "borrower_name": "Charlie Brown",
            "borrower_email": "charlie@example.com",
            "loan_amount": 15000.0,
            "annual_income": 90000.0,
            "partner_id": "default",
            "idempotency_key": "charlie_e2e_1",
        }
        # 1. Ingest application
        res = await ac.post("/api/v1/applications", json=payload)
        assert res.status_code == 201
        app_id = res.json()["application_id"]

        # 2. Wait for async saga execution to process events
        await asyncio.sleep(1.5)

        # 3. Check read model status
        detail_res = await ac.get(f"/api/v1/applications/{app_id}")
        assert detail_res.status_code == 200
        data = detail_res.json()

        # Should reach disbursal_completed or decision_made
        assert data["status"] in ["disbursal_completed", "approved", "rejected", "manual_review"]
        assert len(data["timeline"]) >= 3
