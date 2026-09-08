import React from "react";

export type StatusType = "idle" | "running" | "done" | "failed";

export interface StatusDotProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: StatusType;
  showLabel?: boolean;
}

export const StatusDot = React.forwardRef<HTMLSpanElement, StatusDotProps>(
  ({ className = "", status, showLabel = true, ...props }, ref) => {
    // Config mappings matching tokens.ts definitions
    const config = {
      idle: {
        dotClass: "bg-status-idle border-status-idle/30",
        label: "Idle",
        textClass: "text-soc-text-muted",
      },
      running: {
        dotClass: "bg-status-running border-status-running/30 animate-pulse",
        label: "Running",
        textClass: "text-status-running",
      },
      done: {
        dotClass: "bg-status-done border-status-done/30",
        label: "Completed",
        textClass: "text-status-done",
      },
      failed: {
        dotClass: "bg-status-failed border-status-failed/30",
        label: "Failed",
        textClass: "text-status-failed",
      },
    };

    const current = config[status];

    const combinedClasses = `inline-flex items-center gap-2 text-xs font-mono font-medium ${className}`.trim();

    return (
      <span ref={ref} className={combinedClasses} {...props}>
        <span
          className={`h-2.5 w-2.5 rounded-full border shadow-[0_0_8px_rgba(0,0,0,0.15)] ${current.dotClass}`}
          aria-hidden="true"
        />
        {showLabel && <span className={current.textClass}>{current.label}</span>}
      </span>
    );
  }
);

StatusDot.displayName = "StatusDot";
