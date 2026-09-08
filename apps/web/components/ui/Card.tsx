import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", hoverable = false, children, ...props }, ref) => {
    const baseStyle =
      "bg-soc-surface border border-soc-border rounded-lg p-5 transition-all text-soc-text-primary";
    const hoverStyle = hoverable ? "hover:border-accent-primary/60" : "";
    const combinedClasses = `${baseStyle} ${hoverStyle} ${className}`.trim();

    return (
      <div ref={ref} className={combinedClasses} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";
