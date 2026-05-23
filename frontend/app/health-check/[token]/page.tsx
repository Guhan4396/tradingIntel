import { notFound } from "next/navigation";
import HealthCheckReport from "@/components/health-check/HealthCheckReport";
import type { HealthCheckReport as HealthCheckReportType } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getHealthCheckData(token: string): Promise<HealthCheckReportType | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health-check/${token}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function HealthCheckPage({
  params,
}: {
  params: { token: string };
}) {
  const data = await getHealthCheckData(params.token);

  if (!data) {
    notFound();
  }

  return <HealthCheckReport data={data} />;
}

export async function generateMetadata({ params }: { params: { token: string } }) {
  const data = await getHealthCheckData(params.token);
  const company = data?.customer?.company || "Your Company";
  const minLoss = data?.report?.hero_metric?.potential_loss_min_lakhs;
  const maxLoss = data?.report?.hero_metric?.potential_loss_max_lakhs;

  return {
    title: `Export Health Check — ${company} | TradingIntel`,
    description: minLoss && maxLoss
      ? `${company} may be leaving ₹${minLoss}-${maxLoss} lakh on the table annually. See your personalized export health check.`
      : `Personalized export health check for ${company}`,
  };
}
