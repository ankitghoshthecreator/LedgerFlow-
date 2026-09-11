"""Test Application Ingestion & Idempotency."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, AsyncSessionLocal, engine
from app.event_bus.in_process import InProcessEventBus
from app.main import app
from app.api.v1.applications import set_global_event_bus


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    bus = InProcessEventBus()
    await bus.start()
    set_global_event_bus(bus)
    yield
    await bus.stop()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_submit_application_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "borrower_name": "Alice Smith",
            "borrower_email": "alice@example.com",
            "loan_amount": 25000.0,
            "annual_income": 85000.0,
            "partner_id": "partner_a",
            "idempotency_key": "test_key_123",
        }
        res = await ac.post("/api/v1/applications", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["borrower_name"] == "Alice Smith"
        assert data["status"] == "submitted"
        assert data["idempotency_key"] == "test_key_123"


@pytest.mark.asyncio
async def test_submit_application_idempotent():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "borrower_name": "Bob Jones",
            "borrower_email": "bob@example.com",
            "loan_amount": 10000.0,
            "annual_income": 50000.0,
            "idempotency_key": "unique_idem_key_999",
        }
        res1 = await ac.post("/api/v1/applications", json=payload)
        assert res1.status_code == 201
        app1_id = res1.json()["application_id"]

        # Duplicate submit
        res2 = await ac.post("/api/v1/applications", json=payload)
        assert res2.status_code == 201
        app2_id = res2.json()["application_id"]

        assert app1_id == app2_id
