import React from "react";
import { FolderOpen } from "lucide-react";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className = "", title, description, action, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`flex flex-col items-center justify-center text-center py-12 px-6 border border-dashed border-soc-border rounded-lg bg-soc-surface/30 ${className}`.trim()}
        {...props}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded bg-soc-surface border border-soc-border text-soc-text-muted mb-4 shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]">
          <FolderOpen className="h-6 w-6" aria-hidden="true" />
        </div>
        <h3 className="font-display font-medium text-soc-text-primary text-base mb-1">
          {title}
        </h3>
        <p className="text-soc-text-secondary text-sm max-w-md mb-6 leading-relaxed">
          {description}
        </p>
        {action && <div className="flex justify-center">{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = "EmptyState";
