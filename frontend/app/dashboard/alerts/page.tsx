"use client";

import { useEffect, useState, useCallback } from "react";
import AlertItem from "@/components/dashboard/AlertItem";
import { listAlerts, acknowledgeAlert } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unacknowledged" | "acknowledged">("all");
  const [page, setPage] = useState(0);

  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: { acknowledged?: boolean; skip: number; limit: number } = {
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (filter === "unacknowledged") params.acknowledged = false;
      if (filter === "acknowledged") params.acknowledged = true;

      const data = await listAlerts(params);
      setAlerts(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  }, [filter, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeAlert(id);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, acknowledged: true, acknowledged_at: new Date().toISOString() } : a
        )
      );
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    }
  };

  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Alerts</h1>
          <p className="text-slate-400 mt-1">
            {total} total alerts
            {unacknowledgedCount > 0 && (
              <span className="ml-2 bg-red-900/50 text-red-400 border border-red-700 text-xs px-2 py-0.5 rounded-full">
                {unacknowledgedCount} unread
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {(["all", "unacknowledged", "acknowledged"] as const).map((f) => (
          <button
            key={f}
            onClick={() => { setFilter(f); setPage(0); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              filter === f
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
          >
            {f === "unacknowledged" ? "Unread" : f === "acknowledged" ? "Read" : "All"}
          </button>
        ))}
      </div>

      {/* Alert items */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-5 animate-pulse h-40" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-16 text-center">
          <div className="text-5xl mb-4">🔔</div>
          <h3 className="text-xl font-semibold text-white mb-2">No Alerts</h3>
          <p className="text-slate-400">
            {filter === "unacknowledged"
              ? "All caught up! No unread alerts."
              : "Alerts will appear here when urgent trade intelligence is detected."}
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {alerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onAcknowledge={handleAcknowledge}
              />
            ))}
          </div>

          {/* Pagination */}
          {Math.ceil(total / PAGE_SIZE) > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-slate-400 text-sm">
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
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
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(total / PAGE_SIZE) - 1}
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
