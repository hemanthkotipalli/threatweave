/**
 * ThreatWeave Design System Tokens — "Signal Intercept"
 * 
 * This file serves as the single source of truth for the visual token system of the frontend.
 * Every styling attribute (colors, font pairing, spacing, and radii scales) must refer to
 * the tokens exported here to maintain theme consistency and prevent ad-hoc hardcoded values.
 */

export const COLORS = {
  // Theme Background Scales (Warm Signal Intercept near-black theme)
  bg: {
    base: "#0E0C0B",        // Main warm near-black background for the operations console
    surface: "#161311",     // Cards, table frames, panel divisions
    elevated: "#211D1A",    // Modals, popovers, dropdown drawers, active items
    border: "#2E2722",      // Subtle warm amber-gray structural borders and dividers
  },

  // Typography Contrast Scales
  text: {
    primary: "#E2E8F0",     // Default bright UI labels and text (slate-100)
    secondary: "#94A3B8",   // Muted descriptive copy and metadata (slate-400)
    muted: "#64748B",       // Inactive items, detailed labels, or placeholder text
  },

  // Primary Restrained Brand Accents (Signal Orange / Amber)
  accent: {
    primary: "#FF6B35",     // Signal-orange highlights, primary CTA, active navigation
    hover: "#E85520",       // Deep rust-orange hover state
    outline: "rgba(255, 107, 53, 0.4)", // Focusing border outline shadow
  },

  // Strict 5-tier Threat Severity Color Coding (Info/Low desaturated for dominance hierarchy)
  severity: {
    info: "#5B9EB8",        // Informational Alerts (Desaturated steel-cyan)
    low: "#4EAB87",         // Low Risk Alerts (Desaturated sage-green)
    medium: "#FBBF24",      // Moderate Risk Warnings (Amber Yellow)
    high: "#F97316",        // High Risk Threats (Alert Orange)
    critical: "#EF4444",    // Critical Incident (Crimson Red)
  },

  // 4-tier Action Pipeline Status Indicators (Unchanged - functionally load-bearing)
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
    display: "var(--font-display)",       // Barlow Condensed (tactical editorial field-report grotesk)
    body: "var(--font-inter)",            // Inter (high-legibility UI body copy)
    mono: "var(--font-jetbrains-mono)",   // JetBrains Mono (hashes, indicators, telemetry)
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
