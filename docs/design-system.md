# ThreatWeave Design System

This document outlines the visual tokens, font choices, scales, and component guidelines for the ThreatWeave SOC Operations Console frontend.

---

## 1. Color System Tokens

Every color utilized across components, panels, or typography must tie back to these tokens (defined in [`lib/tokens.ts`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/lib/tokens.ts) and configured within [`app/globals.css`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/app/globals.css)).

### Background & Surface Scales
- **SOC Base Background** (`#0B0E14`): Main dark backdrop for the operations dashboard.
- **SOC Surface** (`#111622`): Secondary containers, table backgrounds, and card bodies.
- **SOC Elevated** (`#182030`): Popups, dropdown drawers, and dialog surfaces.
- **SOC Border** (`#1F293D`): Separation grids, lines, and borders.

### Typography Contrast Scales
- **Primary Text** (`#E2E8F0`): Highest contrast, used for headers and primary controls.
- **Secondary Text** (`#94A3B8`): Muted copy, descriptions, and labels.
- **Muted Text** (`#64748B`): Timestamps, detailed items, and disabled states.

### Primary Accents (Restrained Usage Only)
- **Accent Primary** (`#2A66FF`): Primary interactive button colors, focus states, and selection markers.
- **Accent Hover** (`#1D4ED8`): Hover state for accent actions.
- **Accent Outline** (`rgba(42, 102, 255, 0.4)`): Shadow glows for keyboard navigation outlines.

### Threat Severity Levels
- **Info** (`#38BDF8`): Sky Blue (Informational logs/events).
- **Low** (`#34D399`): Emerald Green (Normal operation / low risk alerts).
- **Medium** (`#FBBF24`): Amber Yellow (Minor anomalies / moderate warnings).
- **High** (`#F97316`): Orange (Active threats / high warning status).
- **Critical** (`#EF4444`): Crimson Red (Urgent security breach / critical action needed).

### Swarm Pipeline Status Dots
- **Idle** (`#94A3B8`): Slate Gray (Awaiting job inputs).
- **Running** (`#3B82F6`): Blue (Active processing execution).
- **Completed** (`#10B981`): Green (Success / agent consensus complete).
- **Failed** (`#EF4444`): Red (Execution crash / network error).

---

## 2. Typography & Spacing Scale

### Typography Pairing
- **Display Font**: `Space Grotesk` (Geometric sans-serif for screen titles, headings, and counts).
- **Body Font**: `Inter` (Clear, high legibility sans-serif for UI forms, listings, and text).
- **Monospace Font**: `JetBrains Mono` (Coding logs, indicator badges, IDs, and severity codes).

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
- **lg** (`6px`): Cards, table panels.

---

## 3. Component Usage Guidance

All components are fully typed and placed under [`components/ui/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/components/ui/):

1. **`Button`**: Provides primary, secondary, and ghost variant states for action execution.
2. **`Card`**: Visual boundary card container with border framing.
3. **`Badge`**: Basic badge label highlighting small metadata segments.
4. **`SeverityTag`**: Custom tag resolving a fixed color and fixed Lucide icon based on the 5 threat severity levels.
5. **`StatusDot`**: Renders dynamic status indicators mapping background glows (with pulses for running states).
6. **`Skeleton`**: Pulsing shape container representing load placeholders (motion-paused on prefers-reduced-motion).
7. **`EmptyState`**: Layout structure displaying empty lists/screens with contextual explanations and button triggers.
