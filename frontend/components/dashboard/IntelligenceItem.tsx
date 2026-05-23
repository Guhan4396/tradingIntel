import type { IntelligenceItem as IntelligenceItemType } from "@/lib/types";
import { getSeverityColor, getSeverityEmoji, formatDate } from "@/lib/api";

interface IntelligenceItemProps {
  item: IntelligenceItemType;
  onReview?: (id: string) => void;
}

export default function IntelligenceItemCard({ item, onReview }: IntelligenceItemProps) {
  const severityStyles = getSeverityColor(item.severity);
  const emoji = getSeverityEmoji(item.severity);

  return (
    <div className={`border rounded-xl p-5 ${severityStyles}`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${severityStyles}`}>
            {emoji} {item.severity.toUpperCase()}
          </span>
          {item.hsn_codes.slice(0, 3).map((code) => (
            <span key={code} className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
              HSN {code}
            </span>
          ))}
        </div>
        <span className="text-xs text-slate-500 flex-shrink-0">{formatDate(item.processed_at)}</span>
      </div>

      <h3 className="text-white font-semibold text-base mb-2">{item.title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed mb-3">{item.summary}</p>

      <div className="flex items-center gap-4 text-xs text-slate-500 mb-3">
        {item.countries.length > 0 && (
          <span>📍 {item.countries.slice(0, 3).join(", ")}</span>
        )}
      </div>

      {item.action_text && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Recommended Action
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
        {onReview && !item.is_reviewed && (
          <button
            onClick={() => onReview(item.id)}
            className="text-xs text-slate-500 hover:text-white transition-colors ml-auto"
          >
            Mark Reviewed
          </button>
        )}
        {item.is_reviewed && (
          <span className="text-xs text-slate-600 ml-auto">✓ Reviewed</span>
        )}
      </div>
    </div>
  );
}
