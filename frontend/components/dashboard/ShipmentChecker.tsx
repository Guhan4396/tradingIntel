"use client";

import { useState } from "react";
import { checkShipment, formatCurrency } from "@/lib/api";
import type { ShipmentCheckResponse } from "@/lib/types";

const POPULAR_DESTINATIONS = ["USA", "UK", "UAE", "EU", "Australia", "Japan", "Canada"];

export default function ShipmentChecker() {
  const [form, setForm] = useState({
    hsn_code: "",
    dest_country: "",
    quantity: "",
    value_inr: "",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ShipmentCheckResponse | null>(null);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.hsn_code || !form.dest_country) {
      setError("HSN code and destination country are required.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await checkShipment({
        hsn_code: form.hsn_code,
        dest_country: form.dest_country,
        quantity: form.quantity ? parseFloat(form.quantity) : undefined,
        value_inr: form.value_inr ? parseFloat(form.value_inr) : undefined,
      });
      setResult(data);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to check shipment. Please try again.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Pre-Shipment Intelligence Check</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              HSN Code <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="hsn_code"
              value={form.hsn_code}
              onChange={handleChange}
              placeholder="e.g., 6101, 5208, 620342"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Destination Country <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="dest_country"
              value={form.dest_country}
              onChange={handleChange}
              placeholder="e.g., UK, USA, UAE"
              list="country-suggestions"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
            />
            <datalist id="country-suggestions">
              {POPULAR_DESTINATIONS.map((c) => <option key={c} value={c} />)}
            </datalist>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Quantity (units)
            </label>
            <input
              type="number"
              name="quantity"
              value={form.quantity}
              onChange={handleChange}
              placeholder="e.g., 5000"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Shipment Value (₹)
            </label>
            <input
              type="number"
              name="value_inr"
              value={form.value_inr}
              onChange={handleChange}
              placeholder="e.g., 500000"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {/* Quick select for popular destinations */}
        <div className="flex flex-wrap gap-2 mb-4">
          {POPULAR_DESTINATIONS.map((country) => (
            <button
              key={country}
              type="button"
              onClick={() => setForm((prev) => ({ ...prev, dest_country: country }))}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                form.dest_country === country
                  ? "bg-amber-500/20 border-amber-500 text-amber-400"
                  : "border-slate-600 text-slate-400 hover:border-slate-500 hover:text-white"
              }`}
            >
              {country}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg px-4 py-3 text-red-400 text-sm mb-4">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-amber-500 hover:bg-amber-400 disabled:bg-amber-500/50 text-slate-900 font-bold py-3 rounded-xl transition-colors disabled:cursor-not-allowed"
        >
          {loading ? "Checking..." : "Run Pre-Shipment Check →"}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-6">
          <h3 className="text-lg font-semibold text-white">
            Results: HSN {form.hsn_code} → {form.dest_country}
          </h3>

          {/* Tariff section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">MFN Rate</div>
              <div className="text-2xl font-bold text-white">{result.tariff.mfn_rate}</div>
            </div>
            {result.tariff.preferential_rate && (
              <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-4">
                <div className="text-xs text-green-400 uppercase tracking-wide mb-1">FTA Rate</div>
                <div className="text-2xl font-bold text-green-400">{result.tariff.preferential_rate.split("(")[0]}</div>
                <div className="text-xs text-green-500 mt-1">
                  {result.tariff.preferential_rate.includes("(") ? result.tariff.preferential_rate.split("(")[1]?.replace(")", "") : ""}
                </div>
              </div>
            )}
            <div className={`rounded-lg p-4 ${result.fta_eligible ? "bg-green-900/20 border border-green-800/30" : "bg-slate-700/50"}`}>
              <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Your Rate</div>
              <div className={`text-2xl font-bold ${result.fta_eligible ? "text-green-400" : "text-white"}`}>
                {result.tariff.applicable_rate}
              </div>
              {result.duty_estimate_inr !== undefined && result.duty_estimate_inr !== null && (
                <div className="text-xs text-slate-400 mt-1">
                  Est. Duty: {formatCurrency(result.duty_estimate_inr)}
                </div>
              )}
            </div>
          </div>

          {/* FTA eligibility */}
          <div className={`flex items-start gap-3 p-4 rounded-lg border ${
            result.fta_eligible
              ? "bg-green-900/20 border-green-800/40"
              : "bg-slate-700/30 border-slate-700"
          }`}>
            <span className="text-2xl flex-shrink-0">{result.fta_eligible ? "✅" : "❌"}</span>
            <div>
              <div className={`font-semibold ${result.fta_eligible ? "text-green-400" : "text-slate-400"}`}>
                {result.fta_eligible ? "FTA Eligible" : "FTA Not Applicable"}
              </div>
              <p className="text-slate-300 text-sm mt-1">{result.fta_details}</p>
            </div>
          </div>

          {/* Documents required */}
          <div>
            <h4 className="text-white font-medium mb-3">
              Required Documents ({result.documents_required.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {result.documents_required.map((doc, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-slate-300">
                  <span className="text-amber-400 flex-shrink-0">•</span>
                  {doc}
                </div>
              ))}
            </div>
          </div>

          {/* Port issues */}
          {result.recent_port_issues && result.recent_port_issues.length > 0 && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg p-4">
              <h4 className="text-red-400 font-medium mb-2">⚠️ Port Issues</h4>
              {result.recent_port_issues.map((issue, i) => (
                <p key={i} className="text-slate-300 text-sm">{issue}</p>
              ))}
            </div>
          )}

          {/* Optimization tip */}
          {result.optimization_tip && (
            <div className="bg-amber-900/20 border border-amber-800/40 rounded-lg p-4">
              <h4 className="text-amber-400 font-medium mb-2">💡 Optimization Tip</h4>
              <p className="text-slate-300 text-sm">{result.optimization_tip}</p>
            </div>
          )}

          {result.note && (
            <p className="text-slate-500 text-xs italic">{result.note}</p>
          )}
        </div>
      )}
    </div>
  );
}
