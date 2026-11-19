import { Metadata } from "next";
import { AnalyticsDashboard } from "@/components/analytics/AnalyticsDashboard";

export const metadata: Metadata = {
  title: "Analytics Studio — ThreatWeave SOC Operations",
  description: "Interactive multi-agent threat analytics, severity distribution, modality breakdown, and empirical evaluation benchmarks.",
};

export default function AnalyticsPage() {
  return <AnalyticsDashboard />;
}
