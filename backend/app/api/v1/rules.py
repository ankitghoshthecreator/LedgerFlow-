"""API Router for Partner Risk Rules Management."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import PartnerRulesRepository

router = APIRouter(prefix="/partners", tags=["Partner Risk Rules"])


class RuleDefinition(BaseModel):
    field: str
    operator: str
    value: float


class PartnerRulesSchema(BaseModel):
    partner_id: str
    partner_name: str
    rules: list[RuleDefinition]


@router.get("/{partner_id}/rules", response_model=PartnerRulesSchema)
async def get_partner_rules(
    partner_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    repo = PartnerRulesRepository(db)
    model = await repo.get_by_partner_id(partner_id)
    if not model:
        # Default fallback rules
        return {
            "partner_id": partner_id,
            "partner_name": f"Partner {partner_id.title()}",
            "rules": [
                {"field": "credit_score", "operator": "min", "value": 650},
                {"field": "debt_to_income", "operator": "max", "value": 0.40},
                {"field": "loan_amount", "operator": "max_multiple_of_income", "value": 5.0},
            ],
        }
    return {
        "partner_id": model.partner_id,
        "partner_name": model.partner_name,
        "rules": model.rules.get("rules", []),
    }


@router.post("/{partner_id}/rules", status_code=status.HTTP_200_OK)
async def update_partner_rules(
    partner_id: str,
    payload: PartnerRulesSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    repo = PartnerRulesRepository(db)
    rules_dict = {"rules": [r.model_dump() for r in payload.rules]}
    updated = await repo.save(partner_id, payload.partner_name, rules_dict)
    return {
        "status": "updated",
        "partner_id": updated.partner_id,
        "rules": updated.rules["rules"],
    }
