import type { Metadata } from "next";
import Sidebar from "@/components/dashboard/Sidebar";

export const metadata: Metadata = {
  title: "Dashboard | TradingIntel",
  description: "Your AI-powered trade intelligence dashboard",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-[#0F172A]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
