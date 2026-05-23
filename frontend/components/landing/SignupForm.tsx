"use client";

import { useState } from "react";
import { requestHealthCheck } from "@/lib/api";

interface SignupFormProps {
  onSuccess?: (token: string) => void;
}

const TURNOVER_OPTIONS = [
  { value: "<5 Cr", label: "Less than ₹5 Crore" },
  { value: "5-50 Cr", label: "₹5 – 50 Crore" },
  { value: "50-500 Cr", label: "₹50 – 500 Crore" },
  { value: "500 Cr+", label: "More than ₹500 Crore" },
];

export default function SignupForm({ onSuccess }: SignupFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    company: "",
    whatsapp: "",
    email: "",
    products_exported: "",
    top_markets: "",
    turnover_range: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [reportUrl, setReportUrl] = useState("");

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Validation
    if (!formData.name || !formData.company || !formData.products_exported ||
        !formData.top_markets || !formData.turnover_range) {
      setError("Please fill in all required fields.");
      setLoading(false);
      return;
    }

    try {
      const result = await requestHealthCheck(formData);
      setSuccess(true);
      setReportUrl(result.report_url);
      if (onSuccess) onSuccess(result.token);

      // Redirect to report
      setTimeout(() => {
        window.location.href = result.report_url;
      }, 1500);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center py-8">
        <div className="text-5xl mb-4">✅</div>
        <h3 className="text-2xl font-bold text-white mb-2">Your Report is Ready!</h3>
        <p className="text-slate-400 mb-4">Redirecting you to your personalized Export Health Check...</p>
        {reportUrl && (
          <a href={reportUrl} className="text-amber-400 hover:text-amber-300 underline">
            Click here if you're not redirected
          </a>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Your Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Rajesh Kumar"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Company Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            name="company"
            value={formData.company}
            onChange={handleChange}
            placeholder="Surat Fabrics Pvt Ltd"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            WhatsApp Number
          </label>
          <input
            type="tel"
            name="whatsapp"
            value={formData.whatsapp}
            onChange={handleChange}
            placeholder="+91 98765 43210"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Work Email
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="rajesh@surat-fabrics.com"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          What do you export? <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          name="products_exported"
          value={formData.products_exported}
          onChange={handleChange}
          placeholder="e.g., Cotton shirts, denim fabric, polyester yarn (HSN 6101-6212)"
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          Top 3 Export Markets <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          name="top_markets"
          value={formData.top_markets}
          onChange={handleChange}
          placeholder="e.g., USA, UK, UAE"
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-colors"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          Annual Export Turnover <span className="text-red-400">*</span>
        </label>
        <select
          name="turnover_range"
          value={formData.turnover_range}
          onChange={handleChange}
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-amber-500 transition-colors"
          required
        >
          <option value="">Select turnover range</option>
          {TURNOVER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-amber-500 hover:bg-amber-400 disabled:bg-amber-500/50 text-slate-900 font-bold py-3.5 rounded-xl text-lg transition-all duration-200 disabled:cursor-not-allowed"
      >
        {loading ? "Generating Your Report..." : "Get My Free Export Health Check →"}
      </button>

      <p className="text-center text-xs text-slate-500">
        Takes 30 seconds • No credit card • Personalized AI report
      </p>
    </form>
  );
}
