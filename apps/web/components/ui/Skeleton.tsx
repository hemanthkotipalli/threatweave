import React from "react";

export type SkeletonProps = React.HTMLAttributes<HTMLDivElement>;

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className = "", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`animate-pulse rounded bg-soc-elevated/70 border border-soc-border/10 ${className}`.trim()}
        {...props}
      />
    );
  }
);

Skeleton.displayName = "Skeleton";
