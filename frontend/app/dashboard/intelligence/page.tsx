"use client";

import { useEffect, useState, useCallback } from "react";
import IntelligenceItemCard from "@/components/dashboard/IntelligenceItem";
import { listIntelligence, reviewIntelligenceItem, triggerIngestion } from "@/lib/api";
import type { IntelligenceItem } from "@/lib/types";

const SEVERITY_OPTIONS = [
  { value: "", label: "All Severity" },
  { value: "urgent", label: "🚨 Urgent" },
  { value: "watch", label: "👀 Watch" },
  { value: "opportunity", label: "✅ Opportunity" },
];

const MARKET_OPTIONS = ["", "USA", "UK", "UAE", "EU", "Australia", "Japan", "Canada", "India"];
const PAGE_SIZE = 10;

export default function IntelligencePage() {
  const [items, setItems] = useState<IntelligenceItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [page, setPage] = useState(0);

  const [filters, setFilters] = useState({
    severity: "",
    country: "",
    hsn_code: "",
    from_date: "",
    to_date: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (filters.severity) params.severity = filters.severity;
      if (filters.country) params.country = filters.country;
      if (filters.hsn_code) params.hsn_code = filters.hsn_code;
      if (filters.from_date) params.from_date = filters.from_date;
      if (filters.to_date) params.to_date = filters.to_date;

      const data = await listIntelligence(params as Parameters<typeof listIntelligence>[0]);
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load intelligence:", err);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const handleReview = async (id: string) => {
    try {
      await reviewIntelligenceItem(id, { is_reviewed: true });
      setItems((prev) =>
        prev.map((item) => (item.id === id ? { ...item, is_reviewed: true } : item))
      );
    } catch (err) {
      console.error("Failed to mark as reviewed:", err);
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    try {
      await triggerIngestion();
      setTimeout(() => load(), 2000);
    } catch (err) {
      console.error("Ingestion failed:", err);
    } finally {
      setTimeout(() => setIngesting(false), 3000);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Intelligence Feed</h1>
          <p className="text-slate-400 mt-1">{total} total items</p>
        </div>
        <button
          onClick={handleIngest}
          disabled={ingesting}
          className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
        >
          {ingesting ? "Ingesting..." : "Trigger Ingestion"}
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
        <div className="flex flex-wrap gap-4">
          <select
            value={filters.severity}
            onChange={(e) => handleFilterChange("severity", e.target.value)}
            className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={filters.country}
            onChange={(e) => handleFilterChange("country", e.target.value)}
            className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          >
            {MARKET_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt || "All Markets"}</option>
            ))}
          </select>

          <input
            type="text"
            value={filters.hsn_code}
            onChange={(e) => handleFilterChange("hsn_code", e.target.value)}
            placeholder="Filter by HSN code"
            className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 placeholder-slate-400 focus:outline-none focus:border-amber-500"
          />

          <input
            type="date"
            value={filters.from_date}
            onChange={(e) => handleFilterChange("from_date", e.target.value)}
            className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          />

          <input
            type="date"
            value={filters.to_date}
            onChange={(e) => handleFilterChange("to_date", e.target.value)}
            className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          />

          {Object.values(filters).some(Boolean) && (
            <button
              onClick={() => {
                setFilters({ severity: "", country: "", hsn_code: "", from_date: "", to_date: "" });
                setPage(0);
              }}
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Items */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-5 animate-pulse h-40" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-16 text-center">
          <div className="text-5xl mb-4">🧠</div>
          <h3 className="text-xl font-semibold text-white mb-2">No Intelligence Items</h3>
          <p className="text-slate-400 mb-4">
            {Object.values(filters).some(Boolean)
              ? "No items match your current filters."
              : "Intelligence items will appear as sources are ingested and processed."}
          </p>
          <button
            onClick={handleIngest}
            className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-6 py-2.5 rounded-xl text-sm transition-colors"
          >
            Trigger First Ingestion
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {items.map((item) => (
              <IntelligenceItemCard key={item.id} item={item} onReview={handleReview} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-slate-400 text-sm">
                Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
