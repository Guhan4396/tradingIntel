import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradingIntel — AI-Powered Trade Intelligence for Indian Exporters",
  description:
    "Stop losing ₹30-80 lakh annually to missed FTA benefits and tariff surprises. TradingIntel monitors 10+ global regulatory sources 24/7 and alerts you in 4 hours — not 4 weeks.",
  keywords: "trade intelligence, Indian exporters, textile exporters, FTA benefits, tariff alerts, DGFT, CBIC",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-900 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
