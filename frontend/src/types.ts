export interface Application {
  application_id: str;
  idempotency_key: str;
  borrower_name: str;
  borrower_email: str;
  loan_amount: number;
  annual_income: number;
  partner_id: str;
  status: str;
  decision?: str;
  rejection_reason?: str;
  credit_score?: number;
  debt_to_income?: number;
  risk_score?: number;
  submitted_at: str;
  updated_at: str;
}

export interface DomainEventItem {
  event_id: str;
  application_id: str;
  event_type: str;
  correlation_id: str;
  payload: Record<string, any>;
  occurred_at: str;
}

export interface ApplicationDetail extends Application {
  timeline: DomainEventItem[];
}
type str = string;
