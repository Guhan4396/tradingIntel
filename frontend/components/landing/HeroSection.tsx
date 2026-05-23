"use client";

import { useState } from "react";
import SignupForm from "./SignupForm";

export default function HeroSection() {
  const [showForm, setShowForm] = useState(false);

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center bg-[#0F172A] overflow-hidden px-4">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-[#0F172A] to-slate-900" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-amber-500/5 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-5xl mx-auto text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm px-4 py-2 rounded-full mb-8">
          <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
          AI-Powered Trade Intelligence — Live Monitoring 24/7
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight mb-6">
          Stop Losing{" "}
          <span className="text-amber-400">₹30-80 Lakh</span>
          <br />
          to Regulatory Chaos
        </h1>

        <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-8 leading-relaxed">
          Indian textile exporters lose crores annually to missed FTA benefits, surprise tariff
          changes, and delayed regulatory updates. TradingIntel fixes this with AI-powered
          intelligence delivered in{" "}
          <span className="text-white font-semibold">4 hours, not 4 weeks</span>.
        </p>

        {/* Stats bar */}
        <div className="flex flex-wrap justify-center gap-8 mb-12">
          {[
            { label: "Lost annually to missed FTAs", value: "₹30-80 Lakh" },
            { label: "Alert delivery time", value: "4 Hours" },
            { label: "Pre-shipment check", value: "15 Seconds" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold text-amber-400">{stat.value}</div>
              <div className="text-sm text-slate-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => setShowForm(true)}
            className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-8 py-4 rounded-xl text-lg transition-all duration-200 hover:shadow-lg hover:shadow-amber-500/25"
          >
            Get Free Export Health Check
          </button>
          <a
            href="/dashboard"
            className="border border-slate-600 hover:border-amber-500 text-slate-300 hover:text-white px-8 py-4 rounded-xl text-lg transition-all duration-200"
          >
            View Live Dashboard
          </a>
        </div>

        <p className="text-slate-500 text-sm mt-4">
          No credit card required • Free 30-day trial • Setup in 2 minutes
        </p>
      </div>

      {/* Signup modal */}
      {showForm && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={(e) => e.target === e.currentTarget && setShowForm(false)}
        >
          <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Get Your Free Export Health Check</h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-slate-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <SignupForm onSuccess={() => setShowForm(false)} />
          </div>
        </div>
      )}
    </section>
  );
}
