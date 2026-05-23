"use client";

import { useEffect, useState } from "react";
import { getSubscription, updateSubscription } from "@/lib/api";
import type { Subscription } from "@/lib/types";

const MARKET_OPTIONS = ["USA", "UK", "UAE", "EU", "Australia", "Japan", "Canada", "Germany", "France", "Italy", "Bangladesh", "Vietnam", "China"];
const DIGEST_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly (Recommended)" },
  { value: "immediate", label: "Immediate (Urgent Only)" },
];
const SENSITIVITY_OPTIONS = [
  { value: "high", label: "High — All updates" },
  { value: "medium", label: "Medium — Watch & Urgent only" },
  { value: "low", label: "Low — Urgent only" },
];

// Demo customer ID — in production this comes from auth context
const DEMO_CUSTOMER_ID = "demo";

export default function SettingsPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [newHsn, setNewHsn] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getSubscription(DEMO_CUSTOMER_ID);
        setSubscription(data);
      } catch {
        // Set defaults if no subscription found
        setSubscription({
          id: "",
          customer_id: DEMO_CUSTOMER_ID,
          hsn_codes: ["6101", "6201", "5208"],
          dest_markets: ["USA", "UK", "UAE"],
          source_markets: ["India"],
          notification_prefs: {
            digest_frequency: "weekly",
            alert_sensitivity: "high",
            channels: ["whatsapp", "email"],
          },
        });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async () => {
    if (!subscription) return;
    setSaving(true);
    setError("");
    try {
      const updated = await updateSubscription(DEMO_CUSTOMER_ID, {
        hsn_codes: subscription.hsn_codes,
        dest_markets: subscription.dest_markets,
        source_markets: subscription.source_markets,
        notification_prefs: subscription.notification_prefs,
      });
      setSubscription(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save settings";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const addHsn = () => {
    if (!newHsn.trim() || !/^\d{4,8}$/.test(newHsn.trim())) {
      setError("Enter a valid HSN code (4-8 digits)");
      return;
    }
    if (subscription?.hsn_codes.includes(newHsn.trim())) {
      setError("HSN code already added");
      return;
    }
    setSubscription((prev) =>
      prev ? { ...prev, hsn_codes: [...prev.hsn_codes, newHsn.trim()] } : prev
    );
    setNewHsn("");
    setError("");
  };

  const removeHsn = (code: string) => {
    setSubscription((prev) =>
      prev ? { ...prev, hsn_codes: prev.hsn_codes.filter((c) => c !== code) } : prev
    );
  };

  const toggleMarket = (market: string) => {
    setSubscription((prev) => {
      if (!prev) return prev;
      const exists = prev.dest_markets.includes(market);
      return {
        ...prev,
        dest_markets: exists
          ? prev.dest_markets.filter((m) => m !== market)
          : [...prev.dest_markets, market],
      };
    });
  };

  const toggleChannel = (channel: string) => {
    setSubscription((prev) => {
      if (!prev) return prev;
      const channels = prev.notification_prefs.channels || [];
      const exists = channels.includes(channel);
      return {
        ...prev,
        notification_prefs: {
          ...prev.notification_prefs,
          channels: exists ? channels.filter((c) => c !== channel) : [...channels, channel],
        },
      };
    });
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-slate-700 rounded w-48" />
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-40 bg-slate-800 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-slate-400 mt-1">Manage your HSN codes, markets, and notification preferences</p>
        </div>
        <div className="flex items-center gap-4">
          {saved && (
            <span className="text-green-400 text-sm">✓ Settings saved!</span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-amber-500 hover:bg-amber-400 disabled:bg-amber-500/50 text-slate-900 font-semibold px-6 py-2.5 rounded-xl transition-colors"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* HSN Codes */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-2">HSN Codes</h2>
        <p className="text-slate-400 text-sm mb-4">
          We'll monitor trade intelligence for these specific HSN codes.
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {subscription?.hsn_codes.map((code) => (
            <span
              key={code}
              className="inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-sm px-3 py-1.5 rounded-lg"
            >
              {code}
              <button
                onClick={() => removeHsn(code)}
                className="text-amber-600 hover:text-amber-400 transition-colors text-xs"
              >
                ×
              </button>
            </span>
          ))}
          {subscription?.hsn_codes.length === 0 && (
            <p className="text-slate-500 text-sm">No HSN codes added yet.</p>
          )}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newHsn}
            onChange={(e) => { setNewHsn(e.target.value); setError(""); }}
            onKeyDown={(e) => e.key === "Enter" && addHsn()}
            placeholder="Add HSN code (e.g., 6101)"
            className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 text-sm"
          />
          <button
            onClick={addHsn}
            className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Add
          </button>
        </div>
      </div>

      {/* Destination Markets */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-2">Destination Markets</h2>
        <p className="text-slate-400 text-sm mb-4">
          Select the markets you export to. We'll prioritize intelligence for these regions.
        </p>
        <div className="flex flex-wrap gap-2">
          {MARKET_OPTIONS.map((market) => {
            const selected = subscription?.dest_markets.includes(market);
            return (
              <button
                key={market}
                onClick={() => toggleMarket(market)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selected
                    ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                    : "bg-slate-700 border border-slate-600 text-slate-400 hover:text-white hover:border-slate-500"
                }`}
              >
                {market}
                {selected && " ✓"}
              </button>
            );
          })}
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Notification Preferences</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Digest Frequency</label>
            <select
              value={subscription?.notification_prefs.digest_frequency || "weekly"}
              onChange={(e) =>
                setSubscription((prev) =>
                  prev ? { ...prev, notification_prefs: { ...prev.notification_prefs, digest_frequency: e.target.value } } : prev
                )
              }
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-amber-500"
            >
              {DIGEST_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Alert Sensitivity</label>
            <select
              value={subscription?.notification_prefs.alert_sensitivity || "high"}
              onChange={(e) =>
                setSubscription((prev) =>
                  prev ? { ...prev, notification_prefs: { ...prev.notification_prefs, alert_sensitivity: e.target.value } } : prev
                )
              }
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:border-amber-500"
            >
              {SENSITIVITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6">
          <label className="block text-sm font-medium text-slate-300 mb-3">Notification Channels</label>
          <div className="flex gap-4">
            {["whatsapp", "email", "dashboard"].map((channel) => {
              const enabled = subscription?.notification_prefs.channels?.includes(channel);
              return (
                <button
                  key={channel}
                  onClick={() => toggleChannel(channel)}
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium capitalize transition-all ${
                    enabled
                      ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                      : "bg-slate-700 border border-slate-600 text-slate-400 hover:text-white"
                  }`}
                >
                  {channel === "whatsapp" ? "📱 WhatsApp" : channel === "email" ? "📧 Email" : "💻 Dashboard"}
                  {enabled && " ✓"}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Subscription status */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Subscription</h2>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-white font-medium">Current Plan:</span>
              <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-full text-sm font-semibold">
                30-Day Free Trial
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-2">
              Upgrade to continue access after your trial ends.
            </p>
          </div>
          <button className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold px-6 py-2.5 rounded-xl transition-colors">
            Upgrade Plan
          </button>
        </div>
      </div>
    </div>
  );
}
