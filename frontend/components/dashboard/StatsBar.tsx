interface Stat {
  label: string;
  value: string | number;
  subtext?: string;
  color?: string;
}

interface StatsBarProps {
  stats: Stat[];
}

export default function StatsBar({ stats }: StatsBarProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-slate-800 border border-slate-700 rounded-xl p-5"
        >
          <div className={`text-2xl font-bold ${stat.color || "text-white"}`}>
            {stat.value}
          </div>
          <div className="text-slate-400 text-sm mt-1">{stat.label}</div>
          {stat.subtext && (
            <div className="text-slate-500 text-xs mt-1">{stat.subtext}</div>
          )}
        </div>
      ))}
    </div>
  );
}
