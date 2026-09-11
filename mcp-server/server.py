"""
LedgerFlow MCP Server.

Exposes loan underwriting capabilities to AI agents:
1. submit_loan_application
2. get_application_status
3. update_partner_risk_rules
"""
from __future__ import annotations

import os
import httpx
from fastmcp import FastMCP

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

mcp = FastMCP("LedgerFlow Underwriting Engine")


@mcp.tool()
async def submit_loan_application(
    borrower_name: str,
    borrower_email: str,
    loan_amount: float,
    annual_income: float,
    partner_id: str = "default",
) -> str:
    """Submits a borrower loan application into the LedgerFlow Saga Orchestrator."""
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{BACKEND_URL}/api/v1/applications",
            json={
                "borrower_name": borrower_name,
                "borrower_email": borrower_email,
                "loan_amount": loan_amount,
                "annual_income": annual_income,
                "partner_id": partner_id,
            },
        )
        if res.status_code == 201:
            data = res.json()
            return f"Application submitted successfully. ID: {data['application_id']}, Status: {data['status']}"
        return f"Error submitting application: {res.text}"


@mcp.tool()
async def get_application_status(application_id: str) -> str:
    """Queries CQRS read model and event log timeline for a given application ID."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BACKEND_URL}/api/v1/applications/{application_id}")
        if res.status_code == 200:
            data = res.json()
            timeline_summary = ", ".join([e["event_type"] for e in data.get("timeline", [])])
            return (
                f"Borrower: {data['borrower_name']} | Status: {data['status']} | "
                f"Decision: {data.get('decision')} | Score: {data.get('credit_score')} | "
                f"Event Timeline: [{timeline_summary}]"
            )
        return f"Application {application_id} not found."


@mcp.tool()
async def update_partner_risk_rules(
    partner_id: str,
    partner_name: str,
    min_credit_score: float = 650,
    max_dti: float = 0.40,
    max_loan_multiple: float = 5.0,
) -> str:
    """Configures risk evaluation rules for a specific lending partner."""
    async with httpx.AsyncClient() as client:
        payload = {
            "partner_id": partner_id,
            "partner_name": partner_name,
            "rules": [
                {"field": "credit_score", "operator": "min", "value": min_credit_score},
                {"field": "debt_to_income", "operator": "max", "value": max_dti},
                {"field": "loan_amount", "operator": "max_multiple_of_income", "value": max_loan_multiple},
            ],
        }
        res = await client.post(f"{BACKEND_URL}/api/v1/partners/{partner_id}/rules", json=payload)
        if res.status_code == 200:
            return f"Rules updated for partner {partner_id}"
        return f"Error updating rules: {res.text}"


if __name__ == "__main__":
    mcp.run()
