"""
Configurable Risk Rules Engine (Multi-Tenant).

Evaluates applicant signals against JSON-configured rule thresholds for each lending partner.

Example Partner Rules JSON:
{
  "partner_id": "partner_a",
  "rules": [
    { "field": "credit_score", "operator": "min", "value": 650 },
    { "field": "debt_to_income", "operator": "max", "value": 0.45 },
    { "field": "loan_amount", "operator": "max_multiple_of_income", "value": 5.0 }
  ]
}
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import PartnerRulesRepository

logger = logging.getLogger(__name__)

DEFAULT_RULES = [
    {"field": "credit_score", "operator": "min", "value": 620},
    {"field": "debt_to_income", "operator": "max", "value": 0.50},
    {"field": "loan_amount", "operator": "max_multiple_of_income", "value": 6.0},
]


@dataclass
class RiskEvaluationResult:
    risk_score: float
    rules_passed: list[str] = field(default_factory=list)
    rules_failed: list[str] = field(default_factory=list)


class RiskEngineService:
    """Multi-tenant risk evaluation engine."""

    async def evaluate(
        self,
        session: AsyncSession,
        partner_id: str,
        credit_score: int,
        debt_to_income: float,
        loan_amount: float,
        annual_income: float,
    ) -> RiskEvaluationResult:
        repo = PartnerRulesRepository(session)
        partner_model = await repo.get_by_partner_id(partner_id)

        rules = partner_model.rules if partner_model and "rules" in partner_model.rules else DEFAULT_RULES

        passed: list[str] = []
        failed: list[str] = []

        signals = {
            "credit_score": credit_score,
            "debt_to_income": debt_to_income,
            "loan_amount": loan_amount,
            "annual_income": annual_income,
        }

        for rule in rules:
            rule_name = f"{rule['field']} {rule['operator']} {rule['value']}"
            try:
                is_valid = self._eval_rule(rule, signals)
                if is_valid:
                    passed.append(rule_name)
                else:
                    failed.append(rule_name)
            except Exception as exc:
                logger.error("Failed to evaluate rule %s: %s", rule_name, exc)
                failed.append(f"{rule_name} (evaluation_error)")

        # Calculate risk score (0.0 = lowest risk, 1.0 = highest risk)
        total = len(passed) + len(failed)
        fail_ratio = len(failed) / total if total > 0 else 1.0

        # Adjust risk score based on credit score weighting
        score_penalty = max(0.0, (750 - credit_score) / 300.0)
        risk_score = round(min(1.0, max(0.0, (fail_ratio * 0.6) + (score_penalty * 0.4))), 2)

        return RiskEvaluationResult(
            risk_score=risk_score,
            rules_passed=passed,
            rules_failed=failed,
        )

    def _eval_rule(self, rule: dict[str, Any], signals: dict[str, Any]) -> bool:
        field_name = rule["field"]
        operator = rule["operator"]
        threshold = rule["value"]

        val = signals.get(field_name)

        if operator == "min":
            return float(val) >= float(threshold)
        elif operator == "max":
            return float(val) <= float(threshold)
        elif operator == "max_multiple_of_income":
            income = signals.get("annual_income", 1.0)
            if income <= 0:
                return False
            multiple = val / income
            return multiple <= float(threshold)
        else:
            raise ValueError(f"Unknown operator {operator}")
