"use client";

import type { HealthCheckReport as HealthCheckReportType } from "@/lib/types";

const SEVERITY_COLORS = {
  urgent: "border-red-800 bg-red-900/20",
  watch: "border-amber-800 bg-amber-900/20",
  opportunity: "border-green-800 bg-green-900/20",
  high: "border-red-800 bg-red-900/20",
  medium: "border-amber-800 bg-amber-900/20",
  low: "border-blue-800 bg-blue-900/20",
};

const SEVERITY_BADGE = {
  urgent: "bg-red-900/50 text-red-400 border border-red-700",
  watch: "bg-amber-900/50 text-amber-400 border border-amber-700",
  opportunity: "bg-green-900/50 text-green-400 border border-green-700",
  high: "bg-red-900/50 text-red-400 border border-red-700",
  medium: "bg-amber-900/50 text-amber-400 border border-amber-700",
  low: "bg-blue-900/50 text-blue-400 border border-blue-700",
};

interface Props {
  data: HealthCheckReportType;
}

export default function HealthCheckReport({ data }: Props) {
  const { report } = data;
  const hero = report.hero_metric;
  const metrics = report.summary_metrics;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      {/* Hero banner */}
      <div className="bg-gradient-to-r from-red-900/40 to-amber-900/40 border-b border-red-800/30 py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-2 rounded-full mb-6">
            🚨 Personalized Export Risk Analysis for {report.company}
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
            You Potentially Left
            <br />
            <span className="text-red-400">
              ₹{hero.potential_loss_min_lakhs}-{hero.potential_loss_max_lakhs} Lakh
            </span>
            <br />
            on the Table
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
            {hero.primary_risk_description}
          </p>

          {/* Summary metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            {[
              { label: "Tariff Risks", value: metrics.tariff_risks_count, color: "text-red-400" },
              { label: "FTA Opportunities", value: metrics.fta_opportunities_count, color: "text-amber-400" },
              { label: "Upcoming Risks", value: metrics.upcoming_risks_count, color: "text-orange-400" },
              { label: "Market Opportunities", value: metrics.market_opportunities_count, color: "text-green-400" },
            ].map((m) => (
              <div key={m.label} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <div className={`text-3xl font-bold ${m.color}`}>{m.value}</div>
                <div className="text-slate-400 text-sm mt-1">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-12 space-y-12">
        {/* Section 1: Tariff Exposure */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="w-8 h-8 bg-red-900/50 border border-red-700 rounded-lg flex items-center justify-center text-sm">🚨</span>
            {report.tariff_exposure.title}
          </h2>
          <div className="space-y-4">
            {report.tariff_exposure.items.map((item, i) => (
              <div
                key={i}
                className={`border rounded-xl p-6 ${SEVERITY_COLORS[item.urgency as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.watch}`}
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <h3 className="font-semibold text-white text-lg">{item.risk}</h3>
                  <span className={`text-xs px-3 py-1 rounded-full flex-shrink-0 ${SEVERITY_BADGE[item.urgency as keyof typeof SEVERITY_BADGE] || SEVERITY_BADGE.watch}`}>
                    {item.urgency.toUpperCase()}
                  </span>
                </div>
                <p className="text-slate-300 mb-3">{item.impact}</p>
                <div className="flex flex-wrap gap-4 text-sm text-slate-400">
                  <span>📍 {item.markets_affected.join(", ")}</span>
                  {item.hsn_codes.length > 0 && (
                    <span>🏷️ HSN: {item.hsn_codes.slice(0, 3).join(", ")}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 2: FTA Benefits Missed */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="w-8 h-8 bg-amber-900/50 border border-amber-700 rounded-lg flex items-center justify-center text-sm">💰</span>
              {report.fta_benefits_missed.title}
            </h2>
            <div className="text-right">
              <div className="text-amber-400 font-bold text-xl">
                ₹{report.fta_benefits_missed.annual_savings_min_lakhs}–{report.fta_benefits_missed.annual_savings_max_lakhs}L/yr
              </div>
              <div className="text-slate-400 text-sm">potential savings</div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.fta_benefits_missed.items.map((item, i) => (
              <div
                key={i}
                className="bg-amber-900/10 border border-amber-800/40 rounded-xl p-6"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded font-medium">
                    {item.fta_name}
                  </span>
                </div>
                <p className="text-white font-medium mb-2">{item.benefit}</p>
                <p className="text-slate-400 text-sm mb-3">{item.eligibility}</p>
                <div className="flex items-center justify-between">
                  <span className="text-green-400 font-semibold text-sm">{item.savings_estimate}</span>
                  <span className="text-slate-500 text-xs">{item.markets.join(", ")}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 3: Upcoming Risks */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="w-8 h-8 bg-orange-900/50 border border-orange-700 rounded-lg flex items-center justify-center text-sm">⏰</span>
            {report.upcoming_risks.title}
          </h2>
          <div className="space-y-4">
            {report.upcoming_risks.items.map((item, i) => (
              <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 flex gap-4">
                <div className={`flex-shrink-0 w-2 rounded-full ${
                  item.impact_level === "high" ? "bg-red-500" :
                  item.impact_level === "medium" ? "bg-amber-500" : "bg-blue-500"
                }`} />
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <h3 className="text-white font-medium">{item.risk}</h3>
                    <span className="text-slate-400 text-sm flex-shrink-0">📅 {item.timeline}</span>
                  </div>
                  <p className="text-slate-400 text-sm">{item.affected_products}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 4: Market Opportunities */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="w-8 h-8 bg-green-900/50 border border-green-700 rounded-lg flex items-center justify-center text-sm">🌍</span>
            {report.market_opportunities.title}
          </h2>
          <div className="space-y-4">
            {report.market_opportunities.items.map((item, i) => (
              <div key={i} className="bg-green-900/10 border border-green-800/40 rounded-xl p-6">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <span className="text-green-400 font-bold text-lg">📍 {item.market}</span>
                    <p className="text-white mt-1">{item.opportunity}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-green-400 font-bold">₹{item.potential_revenue_lakhs}L+</div>
                    <div className="text-slate-400 text-xs">potential</div>
                  </div>
                </div>
                <p className="text-slate-400 text-sm mb-3">{item.timeframe}</p>
                <div className="bg-green-900/20 rounded-lg px-4 py-3">
                  <strong className="text-green-300 text-sm">Action Required:</strong>
                  <p className="text-slate-300 text-sm mt-1">{item.action_required}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-r from-amber-500/10 to-amber-600/10 border border-amber-500/20 rounded-2xl p-10 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Stop Leaving Money Behind?
          </h2>
          <p className="text-slate-400 text-lg mb-8">
            Join TradingIntel and get real-time intelligence on all these risks and opportunities.
            Start your 30-day free trial today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/dashboard"
              className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-10 py-4 rounded-xl text-lg transition-all duration-200"
            >
              Start 30-Day Free Trial →
            </a>
            <a
              href="/"
              className="border border-slate-600 hover:border-slate-500 text-slate-300 hover:text-white px-10 py-4 rounded-xl text-lg transition-all duration-200"
            >
              Learn More
            </a>
          </div>
          <p className="text-slate-500 text-sm mt-4">
            No credit card • Cancel anytime • Setup in 2 minutes
          </p>
        </section>
      </div>
    </div>
  );
}
