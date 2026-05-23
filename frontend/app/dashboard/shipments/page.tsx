"use client";

import { useEffect, useState } from "react";
import ShipmentChecker from "@/components/dashboard/ShipmentChecker";
import { getShipmentHistory, formatDate, formatCurrency } from "@/lib/api";
import type { ShipmentCheck } from "@/lib/types";

export default function ShipmentsPage() {
  const [history, setHistory] = useState<ShipmentCheck[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await getShipmentHistory({ limit: 10 });
        setHistory(data.items);
      } catch (err) {
        console.error("Failed to load history:", err);
      } finally {
        setLoadingHistory(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Pre-Shipment Check</h1>
        <p className="text-slate-400 mt-1">
          Get tariff rates, FTA eligibility, duty calculations, and required documents in 15 seconds.
        </p>
      </div>

      <ShipmentChecker />

      {/* History */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Recent Checks</h2>
        {loadingHistory ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-4 animate-pulse h-16" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center">
            <p className="text-slate-400">No shipment checks yet. Run your first check above.</p>
          </div>
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-700 bg-slate-800/80">
                <tr>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">HSN Code</th>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">Destination</th>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">Value</th>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">Rate Applied</th>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">FTA</th>
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {history.map((check) => (
                  <tr key={check.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-amber-400">{check.hsn_code}</td>
                    <td className="px-4 py-3 text-white">{check.dest_country}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {check.value_inr ? formatCurrency(check.value_inr) : "—"}
                    </td>
                    <td className="px-4 py-3 text-white font-semibold">
                      {check.response?.tariff?.applicable_rate || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {check.response?.fta_eligible ? (
                        <span className="text-green-400">✅ Yes</span>
                      ) : (
                        <span className="text-slate-500">❌ No</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{formatDate(check.checked_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
