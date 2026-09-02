# LedgerFlow
### An Event-Driven Loan Underwriting & Risk Engine

## 🧠 Overview

LedgerFlow simulates the backend of a lending platform: a borrower applies, the system pulls signals, scores risk, and reaches a decision — all as a chain of events rather than one big synchronous function, so partial failure never leaves the system in an inconsistent state.

This is the project that speaks fluent NBFC/fintech, straight out of the box.

## 🗺️ Project Roadmap (6 Parts)

To ensure manageable and structured development, the LedgerFlow project is divided into the following six phases:

1. **Part 1: Event Bus & Infrastructure Setup** - Setting up Kafka for domain events, PostgreSQL for the read model/event log, and Redis for caching and rate limiting.
2. **Part 2: Application Ingestion API (FastAPI)** - Building the entry point for borrower applications, handling basic validation, implementing idempotency, and publishing the `application.submitted` event.
3. **Part 3: Saga Orchestrator & State Management** - Creating the core orchestrator that listens for domain events, determines the next steps in the underwriting workflow, and publishes compensating events upon failures.
4. **Part 4: Configurable Risk Rules Engine** - Developing the multi-tenant risk evaluation service that assesses fetched signals against partner-specific JSON thresholds.
5. **Part 5: CQRS Read Model & Projections** - Implementing the logic to rebuild application states from the event stream into a read-optimized PostgreSQL view for fast querying.
6. **Part 6: Real-time Operations Dashboard (React)** - Building the frontend interface that subscribes to application status updates via WebSockets and visualizes the system's state.

## Problem Statement

Lending backends have a hard constraint: a loan decision touches multiple services (KYC, credit bureau, risk scoring, disbursal) that can each fail independently, and the system must never end up in a state where money moved but the underlying decision wasn't properly recorded, or vice versa.

A single synchronous request/response chain can't survive a mid-flow failure cleanly. LedgerFlow uses an event-driven **saga pattern**: each step publishes an event, the next step reacts to it, and every step has a defined compensating action if something downstream fails.

## ⚙️ System Design

### Application Saga
```
APPLICATION_SUBMITTED
        ↓
   KYC_VERIFIED  ──fail──→ APPLICATION_REJECTED (compensate: notify user)
        ↓
CREDIT_SCORE_FETCHED ──fail──→ APPLICATION_REJECTED (compensate: log + notify)
        ↓
  RISK_SCORED
        ↓
 DECISION_MADE (approved/rejected)
        ↓
  [if approved] DISBURSAL_INITIATED → DISBURSAL_COMPLETED
```

### Core Components
- **Event Bus** — Kafka topics per domain event (`application.submitted`, `kyc.verified`, …)
- **Saga Orchestrator** — listens for events, decides next step, publishes next event or a compensating event on failure
- **Rules Engine** — configurable risk-scoring rules per tenant/partner (JSON-defined thresholds, not hardcoded `if` chains) — this is the "configurable, multi-tenant" piece
- **Read Model (CQRS)** — a denormalized PostgreSQL view optimized for the ops dashboard, rebuilt from the event stream (not the source of truth — the events are)
- **Dashboard** — React + TypeScript, WebSocket-subscribed to application status updates in real time

### Configurable Risk Rules (multi-tenant)
```json
{
  "partner": "partner_a",
  "rules": [
    { "field": "credit_score", "min": 650 },
    { "field": "debt_to_income", "max": 0.4 },
    { "field": "loan_amount", "max_multiple_of_income": 5 }
  ]
}
```
Different lending partners, different risk appetite, zero code changes.

## 🧪 Failure Handling
- **Credit bureau API times out** — saga retries with backoff, then routes to manual review queue rather than silently rejecting
- **Disbursal succeeds but confirmation event is lost** — reconciliation job periodically diffs the read model against the event log and re-emits missing events
- **Duplicate application submission** — idempotency key on `application.submitted`, deduplicated at ingestion
- **Partial rule evaluation failure** — a single failing rule doesn't crash the whole risk scoring step; failures are collected and surfaced to underwriting

## Tech Stack
- **Backend:** Python, FastAPI
- **Event bus:** Kafka
- **Database:** PostgreSQL (read model), event log append-only store
- **Cache:** Redis (session state, rate limiting on application submission)
- **Frontend:** React, TypeScript, WebSockets for live status
- **Deployment:** Docker, AWS (ECS/Fargate, RDS Postgres, MSK or self-hosted Kafka)

## 🔑 Key Features
- Full saga-based orchestration with compensating actions — no stuck "half-approved" applications
- Config-driven, per-tenant risk rules (add a lending partner without a deploy)
- CQRS read model for a fast ops dashboard without touching the source-of-truth event log
- Real-time status updates to the frontend via WebSockets
- Reconciliation job proving eventual consistency between event log and read model

## 🚀 Future Improvements
- Real credit-bureau sandbox integration (or a mocked one with realistic latency/failure injection)
- ML-based risk scoring model behind the rules engine (rules as guardrails, model as the score)
- Multi-region event replication for disaster recovery

## 📚 Why This Project Matters for SDE Roles (especially at Edgro)
This one is close to a 1:1 match with Edgro's own language: "configurable, multi-tenant systems that flex as the business and partners' needs change," a "risk engine," and databases doing real modeling work. It also directly extends your existing Nexus Transaction Engine — same financial-correctness instincts, one layer up the stack.

---
*This is a design spec / project blueprint — an implementation plan, not a claim of a built system, until executed.*
