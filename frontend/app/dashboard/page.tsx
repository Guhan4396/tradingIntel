"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import StatsBar from "@/components/dashboard/StatsBar";
import MarketCard from "@/components/dashboard/MarketCard";
import IntelligenceItemCard from "@/components/dashboard/IntelligenceItem";
import { listIntelligence, listAlerts } from "@/lib/api";
import type { IntelligenceItem, Alert } from "@/lib/types";

const TRACKED_MARKETS = ["USA", "UK", "UAE", "EU"];

export default function DashboardPage() {
  const [intelligence, setIntelligence] = useState<IntelligenceItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [intelData, alertData] = await Promise.all([
          listIntelligence({ limit: 5 }),
          listAlerts({ limit: 5 }),
        ]);
        setIntelligence(intelData.items);
        setAlerts(alertData.items);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged).length;
  const urgentItems = intelligence.filter((i) => i.severity === "urgent").length;

  const stats = [
    { label: "Unread Alerts", value: unacknowledgedAlerts, color: unacknowledgedAlerts > 0 ? "text-red-400" : "text-white" },
    { label: "Intelligence Items", value: intelligence.length, color: "text-white" },
    { label: "Urgent Updates", value: urgentItems, color: urgentItems > 0 ? "text-amber-400" : "text-white" },
    { label: "Markets Tracked", value: TRACKED_MARKETS.length, color: "text-green-400" },
  ];

  // Group intelligence by market
  const marketIntelligence: Record<string, IntelligenceItem[]> = {};
  for (const market of TRACKED_MARKETS) {
    marketIntelligence[market] = intelligence.filter(
      (item) => item.countries.includes(market) || item.countries.includes(market.toLowerCase())
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Markets Today</h1>
          <p className="text-slate-400 mt-1">
            {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>
        <Link
          href="/dashboard/shipments"
          className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors"
        >
          Quick Shipment Check →
        </Link>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-5 animate-pulse">
              <div className="h-8 bg-slate-700 rounded w-16 mb-2" />
              <div className="h-4 bg-slate-700 rounded w-24" />
            </div>
          ))}
        </div>
      ) : (
        <StatsBar stats={stats} />
      )}

      {/* Urgent alerts banner */}
      {!loading && unacknowledgedAlerts > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚨</span>
            <div>
              <div className="text-red-400 font-semibold">
                {unacknowledgedAlerts} unacknowledged alert{unacknowledgedAlerts !== 1 ? "s" : ""}
              </div>
              <div className="text-slate-400 text-sm">
                {alerts.filter((a) => !a.acknowledged && a.urgency === "urgent").length} urgent
              </div>
            </div>
          </div>
          <Link
            href="/dashboard/alerts"
            className="text-sm text-red-400 hover:text-red-300 font-medium transition-colors"
          >
            View All →
          </Link>
        </div>
      )}

      {/* Market status cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Market Status</h2>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">🟢 All Clear</span>
            <span className="flex items-center gap-1">🟡 Watch</span>
            <span className="flex items-center gap-1">🔴 Action Required</span>
          </div>
        </div>
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-5 animate-pulse h-32" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {TRACKED_MARKETS.map((market) => (
              <MarketCard
                key={market}
                market={market}
                items={marketIntelligence[market] || []}
              />
            ))}
          </div>
        )}
      </div>

      {/* Recent intelligence */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Recent Intelligence</h2>
          <Link
            href="/dashboard/intelligence"
            className="text-sm text-amber-400 hover:text-amber-300 transition-colors"
          >
            View All →
          </Link>
        </div>
        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-5 animate-pulse h-32" />
            ))}
          </div>
        ) : intelligence.length === 0 ? (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-10 text-center">
            <div className="text-4xl mb-3">📰</div>
            <p className="text-slate-400">No intelligence items yet.</p>
            <p className="text-slate-500 text-sm mt-1">
              Items will appear as sources are ingested.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {intelligence.map((item) => (
              <IntelligenceItemCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
