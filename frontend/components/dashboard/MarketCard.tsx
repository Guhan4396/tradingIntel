import type { IntelligenceItem } from "@/lib/types";

interface MarketCardProps {
  market: string;
  items: IntelligenceItem[];
}

function getMarketStatus(items: IntelligenceItem[]): {
  status: "green" | "amber" | "red";
  label: string;
  emoji: string;
} {
  if (!items.length) return { status: "green", label: "All Clear", emoji: "🟢" };

  const hasUrgent = items.some((i) => i.severity === "urgent");
  const hasWatch = items.some((i) => i.severity === "watch");

  if (hasUrgent) return { status: "red", label: "Action Required", emoji: "🔴" };
  if (hasWatch) return { status: "amber", label: "Monitor Closely", emoji: "🟡" };
  return { status: "green", label: "All Clear", emoji: "🟢" };
}

export default function MarketCard({ market, items }: MarketCardProps) {
  const { status, label, emoji } = getMarketStatus(items);

  const borderColor = {
    green: "border-green-800",
    amber: "border-amber-800",
    red: "border-red-800",
  }[status];

  const bgColor = {
    green: "bg-green-900/10",
    amber: "bg-amber-900/10",
    red: "bg-red-900/10",
  }[status];

  return (
    <div className={`border ${borderColor} ${bgColor} rounded-xl p-5`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white text-lg">{market}</h3>
        <span className="text-2xl">{emoji}</span>
      </div>
      <div className="text-sm text-slate-400 mb-3">{label}</div>
      {items.length > 0 && (
        <div className="space-y-2">
          {items.slice(0, 2).map((item) => (
            <div key={item.id} className="text-xs text-slate-400 truncate">
              •{" "}
              {item.title.length > 60 ? `${item.title.slice(0, 60)}...` : item.title}
            </div>
          ))}
          {items.length > 2 && (
            <div className="text-xs text-slate-500">+{items.length - 2} more updates</div>
          )}
        </div>
      )}
    </div>
  );
}
