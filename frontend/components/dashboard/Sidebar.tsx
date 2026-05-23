"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const navItems = [
  { href: "/dashboard", label: "Markets Today", icon: "📊", exact: true },
  { href: "/dashboard/shipments", label: "Pre-Shipment Check", icon: "🔍" },
  { href: "/dashboard/intelligence", label: "Intelligence Feed", icon: "🧠" },
  { href: "/dashboard/alerts", label: "Alerts", icon: "🔔" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-amber-400 font-bold text-xl">TradingIntel</span>
        </Link>
        <p className="text-slate-500 text-xs mt-1">Trade Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = item.exact
            ? pathname === item.href
            : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Customer info at bottom */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-xl">
          <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center text-slate-900 font-bold text-sm">
            E
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-white text-sm font-medium truncate">Exporter</div>
            <div className="text-xs">
              <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-xs">
                Trial
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
