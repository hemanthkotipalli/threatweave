import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline" | "accent";
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className = "", variant = "default", children, ...props }, ref) => {
    const baseStyle =
      "inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-mono font-medium border";

    const variantStyles = {
      default: "bg-soc-elevated border-soc-border text-soc-text-secondary",
      outline: "bg-transparent border-soc-border text-soc-text-secondary",
      accent: "bg-accent-primary/10 border-accent-primary/30 text-accent-primary",
    };

    const combinedClasses = `${baseStyle} ${variantStyles[variant]} ${className}`.trim();

    return (
      <span ref={ref} className={combinedClasses} {...props}>
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
