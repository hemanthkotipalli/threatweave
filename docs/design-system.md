# ThreatWeave Design System — "Signal Intercept"

This document outlines the visual tokens, font choices, scales, and component guidelines for the ThreatWeave SOC Operations Console frontend following the **"Signal Intercept"** visual restyle.

---

## 1. Color System Tokens

Every color utilized across components, panels, or typography ties directly back to tokens defined in [`lib/tokens.ts`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/lib/tokens.ts) and configured within [`app/globals.css`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/app/globals.css).

### Background & Surface Scales (Warm Signal Intercept Palette)
- **SOC Base Background** (`#0E0C0B`): Warm, near-black command console backdrop replacing generic cool navy-black.
- **SOC Surface** (`#161311`): Secondary containers, table backgrounds, and card bodies with subtle warmth.
- **SOC Elevated** (`#211D1A`): Popups, dropdown drawers, dialog surfaces, and active items.
- **SOC Border** (`#2E2722`): Subtle warm amber-gray separation grids and partition lines.

### Typography Contrast Scales
- **Primary Text** (`#E2E8F0`): Highest contrast, used for headers, active text, and high-priority labels.
- **Secondary Text** (`#94A3B8`): Muted copy, descriptions, and tabular metadata.
- **Muted Text** (`#64748B`): Timestamps, IDs, disabled items, and empty-state placeholders.

### Primary Accents (Signal Orange / Amber)
- **Accent Primary** (`#FF6B35`): High-visibility signal-orange for primary buttons, focus states, and key threat highlights.
- **Accent Hover** (`#E85520`): Deep rust-orange hover transition state.
- **Accent Outline** (`rgba(255, 107, 53, 0.4)`): High-visibility focus ring glow ensuring keyboard accessibility.

### Threat Severity Levels
- **Info** (`#5B9EB8`): Desaturated steel-cyan (low dominance).
- **Low** (`#4EAB87`): Desaturated sage-green (low dominance).
- **Medium** (`#FBBF24`): Amber Yellow (minor anomalies / warnings).
- **High** (`#F97316`): Orange Alert (active threats / high severity).
- **Critical** (`#EF4444`): Crimson Red (urgent security incident).

*Design Rationale:* Desaturating `info` and `low` allows `critical` and `high` threats to immediately dominate visual perception in dense SOC dashboards.

### Swarm Pipeline Status Dots
- **Idle** (`#94A3B8`): Slate Gray (awaiting job inputs).
- **Running** (`#3B82F6`): Blue (active processing execution with pulse).
- **Completed** (`#10B981`): Green (action completed successfully).
- **Failed** (`#EF4444`): Red (execution error / crash).

---

## 2. WCAG Contrast Compliance

| Token / Usage Context | Foreground Hex | Background Hex | Contrast Ratio | WCAG 2.1 AA Compliance |
| :--- | :--- | :--- | :---: | :---: |
| **Accent against Base Background** | `#FF6B35` | `#0E0C0B` | **6.88 : 1** | **PASS** (Normal text >= 4.5:1) |
| **Accent against Surface Cards** | `#FF6B35` | `#161311` | **6.52 : 1** | **PASS** (Normal text >= 4.5:1) |
| **Primary Button Text on Accent** | `#0E0C0B` (Dark) | `#FF6B35` | **6.88 : 1** | **PASS** (Normal text >= 4.5:1) |
| **Primary Text on Base** | `#E2E8F0` | `#0E0C0B` | **15.42 : 1** | **PASS** (Exceeds AAA >= 7.0:1) |
| **Secondary Text on Surface** | `#94A3B8` | `#161311` | **7.41 : 1** | **PASS** (Exceeds AAA >= 7.0:1) |

---

## 3. Typography & Spacing Scale

### Typography Pairing
- **Display Font**: `Barlow Condensed` (`var(--font-display)` via `next/font/google`). Narrow, high-density tactical field-report grotesk optimized for headers, statistics, and command-center interfaces.
- **Body Font**: `Inter` (`var(--font-inter)`). Clear, high-legibility sans-serif for UI forms, listings, and text.
- **Monospace Font**: `JetBrains Mono` (`var(--font-jetbrains-mono)`). Technical telemetry, IDs, hashes, and indicators.

### Spacing Scale (4px Base Grid)
- **xs** (4px / `0.25rem`): Inner element spacing (badges, dots).
- **sm** (8px / `0.5rem`): Inline margins, labels layout.
- **md** (12px / `0.75rem`): Component items gap.
- **lg** (16px / `1rem`): Standard padding, grid gaps.
- **xl** (24px / `1.5rem`): Card layouts, segment paddings.
- **xxl** (32px / `2rem`): Major header partitions.

### Radii Scale
- **none** (`0px`): Default sharp corners.
- **sm** (`2px`): Sub-labels, tags, status dots.
- **md** (`4px`): Interactive elements, buttons, inputs.
- **lg** (`6px`): Primary cards, popups, and dropdown menus.

---

## 4. Visual Motifs & Distinctive Elements

1. **Card Phosphor Scanline Texture:**
   - Every `Card` component features a pure CSS linear gradient overlay (`repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255, 107, 53, 0.025) 3px, rgba(255, 107, 53, 0.025) 4px)`).
   - Generates an ultra-subtle (~2.5% opacity) CRT/phosphor scanline texture without external image assets or network overhead.
2. **Cross-Modal Corroboration Connector:**
   - In the Investigation Workspace (`/investigations/[id]`), when multiple specialist agents detect the same technical indicator, a shared accent badge (`Corroborated Signal: [tag]`) and an accent left-border connector (`border-l-2 border-accent-primary`) are rendered above the corroborating findings.
