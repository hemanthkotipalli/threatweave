/**
 * ThreatWeave Design System Tokens
 * 
 * This file serves as the single source of truth for the visual token system of the frontend.
 * Every styling attribute (colors, font pairing, spacing, and radii scales) must refer to
 * the tokens exported here to maintain theme consistency and prevent ad-hoc hardcoded values.
 */

export const COLORS = {
  // Theme Background Scales (Professional dark-first SOC console theme)
  bg: {
    base: "#0B0E14",        // Main background for the dashboard console
    surface: "#111622",     // Cards, table frames, panel divisions
    elevated: "#182030",    // Modals, popovers, dropdown drawers
    border: "#1F293D",      // Subtle borders and grid partitions
  },

  // Typography Contrast Scales
  text: {
    primary: "#E2E8F0",     // Default bright UI labels and text
    secondary: "#94A3B8",   // Muted descriptive descriptions
    muted: "#64748B",       // Inactive items, detailed labels, or placeholder text
  },

  // Primary Restrained Brand Accents
  accent: {
    primary: "#2A66FF",     // Highlights, focus outlines, primary buttons
    hover: "#1D4ED8",       // Hover state transition color
    outline: "rgba(42, 102, 255, 0.4)", // Focusing border outline shadow
  },

  // Strict 5-tier Threat Severity Color Coding
  severity: {
    info: "#38BDF8",        // Informational Alerts (Sky Blue)
    low: "#34D399",         // Low Risk Alerts (Emerald Green)
    medium: "#FBBF24",      // Moderate Risk Warnings (Amber Yellow)
    high: "#F97316",        // High Risk Threats (Orange Warning)
    critical: "#EF4444",    // Critical Incident (Crimson Red)
  },

  // 4-tier Action Pipeline Status Indicators
  status: {
    idle: "#94A3B8",        // Standard waiting state
    running: "#3B82F6",     // Processing active job state
    done: "#10B981",        // Action completed successfully
    failed: "#EF4444",      // Failed task execution
  },
} as const;

// Spacing Scale mapping to REM units (Standard 4px grid system)
export const SPACING = {
  xs: "0.25rem",   // 4px
  sm: "0.5rem",    // 8px
  md: "0.75rem",   // 12px
  lg: "1rem",      // 16px
  xl: "1.5rem",    // 24px
  xxl: "2rem",     // 32px
} as const;

// Typography Scale & Weight bindings
export const TYPE = {
  fontFamily: {
    display: "var(--font-space-grotesk)",
    body: "var(--font-inter)",
    mono: "var(--font-jetbrains-mono)",
  },
  fontSize: {
    xs: "0.75rem",     // 12px - indicator details, table labels
    sm: "0.875rem",    // 14px - standard body copy, labels
    base: "1rem",      // 16px - buttons, inputs
    lg: "1.125rem",    // 18px - secondary panel headings
    xl: "1.25rem",     // 20px - primary card headings
    xxl: "1.5rem",     // 24px - page dashboard headings
    title: "1.875rem", // 30px - large banner display titles
  },
  fontWeight: {
    normal: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  },
} as const;

// Border Radii bindings (Strict sharp borders for professional military-like SOC dashboard)
export const RADII = {
  none: "0px",
  sm: "2px",          // Tags, status badges
  md: "4px",          // Button containers, inputs
  lg: "6px",          // Cards, tables panels
  full: "9999px",     // Status dots
} as const;
