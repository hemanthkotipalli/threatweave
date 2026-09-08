import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", size = "md", children, ...props }, ref) => {
    // Base styles including layout, typography, transitions, focus rings, and cursor states
    const baseStyle =
      "inline-flex items-center justify-center font-display font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 focus-visible:ring-offset-soc-base disabled:opacity-50 disabled:pointer-events-none rounded-md cursor-pointer";

    // Variant mapping using variables pointing to tokens.ts
    const variantStyles = {
      primary: "bg-accent-primary hover:bg-accent-hover text-soc-text-primary border border-transparent shadow-sm",
      secondary: "bg-soc-surface hover:bg-soc-elevated text-soc-text-primary border border-soc-border",
      ghost: "hover:bg-soc-surface text-soc-text-secondary hover:text-soc-text-primary border border-transparent",
    };

    // Sizing standards
    const sizeStyles = {
      sm: "h-8 px-3 text-xs",
      md: "h-10 px-4 text-sm",
      lg: "h-12 px-6 text-base",
    };

    const combinedClasses = `${baseStyle} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`.trim();

    return (
      <button ref={ref} className={combinedClasses} {...props}>
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
