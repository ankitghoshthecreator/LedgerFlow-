"""
Mock external downstream services for KYC, Credit Bureau, and Disbursal.

Features:
- Credit Bureau with configurable latency, timeout, and failure rate simulation.
- KYC service with optional forced failure setting.
- Disbursal service simulating bank transfer processing.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from typing import Tuple

from app.config import get_settings

settings = get_settings()


class KYCService:
    """Mock KYC Provider (e.g. Identity Verification Service)."""

    async def verify_identity(self, borrower_name: str, borrower_email: str) -> Tuple[bool, str]:
        await asyncio.sleep(0.1)  # Simulate network latency
        if settings.force_kyc_fail or "fail_kyc" in borrower_email.lower():
            return False, "KYC verification failed: Name and SSN/Tax ID mismatch"
        return True, f"Verified Identity for {borrower_name}"


class CreditBureauService:
    """Mock Credit Bureau (e.g. Experian/Equifax API)."""

    async def fetch_credit_profile(self, borrower_email: str) -> Tuple[bool, int, float, str]:
        # Simulate network delay
        latency = random.randint(
            settings.credit_bureau_min_latency_ms,
            settings.credit_bureau_max_latency_ms,
        ) / 1000.0
        await asyncio.sleep(latency)

        # Simulate timeout/failure
        if random.random() < settings.credit_bureau_fail_rate or "fail_credit" in borrower_email.lower():
            return False, 0, 0.0, "Credit Bureau API timeout / service unavailable"

        # Generate realistic score and DTI
        # Seed by email hash for deterministic demo behavior
        seed = sum(ord(c) for c in borrower_email)
        random.seed(seed)
        credit_score = random.randint(580, 820)
        debt_to_income = round(random.uniform(0.15, 0.55), 2)
        random.seed()  # reset seed

        return True, credit_score, debt_to_income, "Equifax"


class DisbursalService:
    """Mock Disbursal Engine (e.g. Stripe / ACH / Bank Wire)."""

    async def initiate_disbursal(self, application_id: str, amount: float) -> Tuple[bool, str]:
        await asyncio.sleep(0.2)
        transaction_id = f"tx_disburse_{uuid.uuid4().hex[:10]}"
        return True, transaction_id
