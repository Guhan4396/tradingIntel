"use client";

import type { Alert } from "@/lib/types";
import { getSeverityColor, getSeverityEmoji, formatDate } from "@/lib/api";

interface AlertItemProps {
  alert: Alert;
  onAcknowledge: (id: string) => Promise<void>;
}

export default function AlertItem({ alert, onAcknowledge }: AlertItemProps) {
  const item = alert.item;
  const severity = alert.urgency;
  const severityStyles = getSeverityColor(severity);
  const emoji = getSeverityEmoji(severity);

  return (
    <div className={`border rounded-xl p-5 ${severityStyles} ${alert.acknowledged ? "opacity-60" : ""}`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${severityStyles}`}>
            {emoji} {severity.toUpperCase()}
          </span>
          {alert.acknowledged && (
            <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full">
              ✓ Acknowledged
            </span>
          )}
        </div>
        <span className="text-xs text-slate-500 flex-shrink-0">{formatDate(alert.sent_at)}</span>
      </div>

      {item && (
        <>
          <h3 className="text-white font-semibold text-base mb-2">{item.title}</h3>
          <p className="text-slate-400 text-sm leading-relaxed mb-3">{item.summary}</p>

          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mb-3">
            {item.countries && item.countries.length > 0 && (
              <span>📍 {item.countries.slice(0, 3).join(", ")}</span>
            )}
            {item.hsn_codes && item.hsn_codes.length > 0 && (
              <span>🏷️ HSN: {item.hsn_codes.slice(0, 3).join(", ")}</span>
            )}
          </div>

          {item.action_text && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                Required Action
              </span>
              <p className="text-slate-300 text-sm mt-1">{item.action_text}</p>
            </div>
          )}

          <div className="flex items-center gap-4">
            {item.source_url && (
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                View Source →
              </a>
            )}
            {!alert.acknowledged && (
              <button
                onClick={() => onAcknowledge(alert.id)}
                className="ml-auto text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-4 py-2 rounded-lg transition-colors"
              >
                Acknowledge Alert
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
