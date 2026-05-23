import axios from "axios";
import type {
  Customer,
  Subscription,
  IntelligenceItem,
  Alert,
  ShipmentCheck,
  ShipmentCheckResponse,
  HealthCheckReport,
  PaginatedResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Customers ───────────────────────────────────────────────────────────────

export async function listCustomers(params?: {
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<Customer>> {
  const res = await api.get("/customers", { params });
  return res.data;
}

export async function createCustomer(data: {
  name: string;
  company: string;
  whatsapp?: string;
  email?: string;
  vertical_tag?: string;
  turnover_range?: string;
  plan?: string;
}): Promise<Customer> {
  const res = await api.post("/customers", data);
  return res.data;
}

export async function getCustomer(id: string): Promise<Customer> {
  const res = await api.get(`/customers/${id}`);
  return res.data;
}

export async function updateCustomer(
  id: string,
  data: Partial<Customer>
): Promise<Customer> {
  const res = await api.patch(`/customers/${id}`, data);
  return res.data;
}

export async function getSubscription(customerId: string): Promise<Subscription> {
  const res = await api.get(`/customers/${customerId}/subscription`);
  return res.data;
}

export async function updateSubscription(
  customerId: string,
  data: Partial<Subscription>
): Promise<Subscription> {
  const res = await api.put(`/customers/${customerId}/subscription`, data);
  return res.data;
}

// ─── Intelligence ─────────────────────────────────────────────────────────────

export async function listIntelligence(params?: {
  severity?: string;
  hsn_code?: string;
  country?: string;
  from_date?: string;
  to_date?: string;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<IntelligenceItem>> {
  const res = await api.get("/intelligence", { params });
  return res.data;
}

export async function getIntelligenceItem(id: string): Promise<IntelligenceItem> {
  const res = await api.get(`/intelligence/${id}`);
  return res.data;
}

export async function reviewIntelligenceItem(
  id: string,
  data: { is_reviewed: boolean; reviewer_notes?: string }
): Promise<IntelligenceItem> {
  const res = await api.post(`/intelligence/${id}/review`, data);
  return res.data;
}

export async function triggerIngestion(): Promise<{ status: string; message: string }> {
  const res = await api.post("/intelligence/ingest");
  return res.data;
}

// ─── Alerts ──────────────────────────────────────────────────────────────────

export async function listAlerts(params?: {
  customer_id?: string;
  acknowledged?: boolean;
  skip?: number;
  limit?: number;
}): Promise<PaginatedResponse<Alert>> {
  const res = await api.get("/alerts", { params });
  return res.data;
}

export async function acknowledgeAlert(id: string): Promise<Alert> {
  const res = await api.patch(`/alerts/${id}/acknowledge`);
  return res.data;
}

// ─── Shipments ───────────────────────────────────────────────────────────────

export async function checkShipment(data: {
  customer_id?: string;
  hsn_code: string;
  dest_country: string;
  quantity?: number;
  value_inr?: number;
}): Promise<ShipmentCheckResponse & { check_id?: string }> {
  const res = await api.post("/shipments/check", data);
  return res.data;
}

export async function getShipmentHistory(params?: {
  customer_id?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: ShipmentCheck[] }> {
  const res = await api.get("/shipments/history", { params });
  return res.data;
}

// ─── Health Check ─────────────────────────────────────────────────────────────

export async function requestHealthCheck(data: {
  name: string;
  company: string;
  whatsapp?: string;
  email?: string;
  products_exported: string;
  top_markets: string;
  turnover_range: string;
}): Promise<{ token: string; message: string; report_url: string }> {
  const res = await api.post("/health-check/request", data);
  return res.data;
}

export async function getHealthCheck(token: string): Promise<HealthCheckReport> {
  const res = await api.get(`/health-check/${token}`);
  return res.data;
}

// ─── Utilities ────────────────────────────────────────────────────────────────

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "urgent":
      return "text-red-400 bg-red-900/20 border-red-800";
    case "watch":
      return "text-amber-400 bg-amber-900/20 border-amber-800";
    case "opportunity":
      return "text-green-400 bg-green-900/20 border-green-800";
    default:
      return "text-slate-400 bg-slate-800 border-slate-700";
  }
}

export function getSeverityEmoji(severity: string): string {
  switch (severity) {
    case "urgent":
      return "🚨";
    case "watch":
      return "👀";
    case "opportunity":
      return "✅";
    default:
      return "📢";
  }
}

export function formatDate(dateString: string): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatCurrency(amount: number): string {
  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)} lakh`;
  }
  return `₹${amount.toLocaleString("en-IN")}`;
}
