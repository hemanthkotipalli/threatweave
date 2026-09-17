import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", hoverable = false, style, children, ...props }, ref) => {
    // Base styles with subtle tactical scanline texture
    const baseStyle =
      "bg-soc-surface border border-soc-border rounded-lg p-5 transition-all text-soc-text-primary";
    const hoverStyle = hoverable ? "hover:border-accent-primary/60" : "";
    const combinedClasses = `${baseStyle} ${hoverStyle} ${className}`.trim();

    // Subtle ~2.5% amber scanline motif (pure CSS, no external assets)
    const combinedStyle: React.CSSProperties = {
      backgroundImage:
        "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255, 107, 53, 0.025) 3px, rgba(255, 107, 53, 0.025) 4px)",
      ...style,
    };

    return (
      <div ref={ref} className={combinedClasses} style={combinedStyle} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";
