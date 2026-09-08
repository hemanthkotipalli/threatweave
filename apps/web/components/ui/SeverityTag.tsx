import React from "react";
import { Info, CheckCircle, AlertTriangle, AlertCircle, AlertOctagon } from "lucide-react";

export type SeverityType = "info" | "low" | "medium" | "high" | "critical";

export interface SeverityTagProps extends React.HTMLAttributes<HTMLSpanElement> {
  severity: SeverityType;
}

export const SeverityTag = React.forwardRef<HTMLSpanElement, SeverityTagProps>(
  ({ className = "", severity, ...props }, ref) => {
    // Style and icon configurations for the strict 5-tier severity system
    const config = {
      info: {
        bg: "bg-severity-info/5 border-severity-info/20 text-severity-info",
        icon: Info,
        label: "INFO",
      },
      low: {
        bg: "bg-severity-low/5 border-severity-low/20 text-severity-low",
        icon: CheckCircle,
        label: "LOW",
      },
      medium: {
        bg: "bg-severity-medium/5 border-severity-medium/20 text-severity-medium",
        icon: AlertTriangle,
        label: "MEDIUM",
      },
      high: {
        bg: "bg-severity-high/5 border-severity-high/20 text-severity-high",
        icon: AlertCircle,
        label: "HIGH",
      },
      critical: {
        bg: "bg-severity-critical/5 border-severity-critical/20 text-severity-critical font-bold",
        icon: AlertOctagon,
        label: "CRITICAL",
      },
    };

    const current = config[severity];
    const Icon = current.icon;

    const baseStyle =
      "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-mono font-medium tracking-wider";
    const combinedClasses = `${baseStyle} ${current.bg} ${className}`.trim();

    return (
      <span ref={ref} className={combinedClasses} {...props}>
        <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        {current.label}
      </span>
    );
  }
);

SeverityTag.displayName = "SeverityTag";
