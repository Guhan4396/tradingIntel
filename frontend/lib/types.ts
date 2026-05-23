// TradingIntel shared TypeScript types

export type Severity = "urgent" | "watch" | "opportunity";
export type CustomerStatus = "trial" | "active" | "paused" | "churned";
export type Plan = "monthly" | "annual" | "pilot";
export type Channel = "whatsapp" | "email" | "dashboard";

export interface Customer {
  id: string;
  name: string;
  company: string;
  whatsapp?: string;
  email?: string;
  vertical_tag: string;
  turnover_range?: string;
  status: CustomerStatus;
  trial_started_at?: string;
  subscription_started_at?: string;
  plan: Plan;
  created_at: string;
}

export interface Subscription {
  id: string;
  customer_id: string;
  hsn_codes: string[];
  dest_markets: string[];
  source_markets: string[];
  notification_prefs: {
    digest_frequency?: string;
    alert_sensitivity?: string;
    channels?: string[];
  };
}

export interface IntelligenceItem {
  id: string;
  ingested_item_id?: string;
  title: string;
  summary: string;
  severity: Severity;
  hsn_codes: string[];
  countries: string[];
  action_text?: string;
  source_url?: string;
  processed_at: string;
  is_reviewed: boolean;
  reviewer_notes?: string;
}

export interface Alert {
  id: string;
  customer_id: string;
  item_id: string;
  urgency: string;
  sent_at: string;
  acknowledged_at?: string;
  acknowledged: boolean;
  item?: {
    title: string;
    summary: string;
    severity: Severity;
    hsn_codes: string[];
    countries: string[];
    action_text?: string;
    source_url?: string;
  };
}

export interface ShipmentCheck {
  id?: string;
  customer_id?: string;
  hsn_code: string;
  dest_country: string;
  quantity?: number;
  value_inr?: number;
  response: ShipmentCheckResponse;
  checked_at: string;
}

export interface ShipmentCheckResponse {
  tariff: {
    mfn_rate: string;
    preferential_rate?: string;
    applicable_rate: string;
    tariff_chapter?: string;
  };
  duty_estimate_inr?: number;
  documents_required: string[];
  fta_eligible: boolean;
  fta_details: string;
  recent_port_issues: string[];
  optimization_tip: string;
  compliance_notes?: string[];
  hs_code_chapter?: string;
  note?: string;
  check_id?: string;
}

export interface HealthCheckReport {
  token: string;
  customer?: {
    name: string;
    company: string;
    status: string;
  };
  products_exported: string;
  top_markets: string;
  turnover_range: string;
  report: {
    hero_metric: {
      potential_loss_min_lakhs: number;
      potential_loss_max_lakhs: number;
      primary_risk_description: string;
    };
    tariff_exposure: {
      title: string;
      severity: Severity;
      items: Array<{
        risk: string;
        impact: string;
        markets_affected: string[];
        hsn_codes: string[];
        urgency: string;
      }>;
    };
    fta_benefits_missed: {
      title: string;
      annual_savings_min_lakhs: number;
      annual_savings_max_lakhs: number;
      items: Array<{
        fta_name: string;
        benefit: string;
        eligibility: string;
        markets: string[];
        savings_estimate: string;
      }>;
    };
    upcoming_risks: {
      title: string;
      items: Array<{
        risk: string;
        timeline: string;
        impact_level: string;
        affected_products: string;
      }>;
    };
    market_opportunities: {
      title: string;
      items: Array<{
        market: string;
        opportunity: string;
        potential_revenue_lakhs: number;
        timeframe: string;
        action_required: string;
      }>;
    };
    summary_metrics: {
      tariff_risks_count: number;
      fta_opportunities_count: number;
      upcoming_risks_count: number;
      market_opportunities_count: number;
    };
    generated_at: string;
    company: string;
    name: string;
  };
  created_at: string;
  trial_signup_url: string;
}

export interface PaginatedResponse<T> {
  total: number;
  skip: number;
  limit: number;
  items: T[];
}
