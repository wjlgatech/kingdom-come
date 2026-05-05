# Design System — Kingdom Come

*Created: 2026-05-04 via `/design-consultation`. Anchored to `COMPETITIVE-UX.md` and the 5 user stories.*

---

## Product Context

- **What this is:** Predictive formation intelligence for seminaries — a workbench that helps seminarians reflect with an AI mentor and helps formation directors triage cohort risk, plan groups, and log outcomes.
- **Who it's for:** Two primary personas — Marcus (24, second-year seminarian discerning evangelism) and Sister Theresa (50s, formation director with a 24-student cohort).
- **Space/industry:** Adjacent to formation/spiritual apps (Hallow, Pray.com), cohort-based learning (Maven, Reforge), AI mentors (Pi.ai, Khanmigo), and instructor risk dashboards (Canvas/IntelliBoard).
- **Project type:** Web application with editorial-feeling marketing surfaces. Vanilla HTML/CSS/JS served by FastAPI from `/static`.

---

## Aesthetic Direction

- **Direction:** **Editorial Pastoral** — the product reads like a thoughtful religious print publication that happens to have an interactive workbench.
- **Decoration level:** Intentional. Subtle warm-paper background, hairline rules between sections, avatar disks with initials. No illustration, no decorative blobs, no stock-photo heroes.
- **Mood:** Pastoral but precise. Warm but not sentimental. Slow enough to invite reflection, sharp enough that Theresa can triage 24 students in five minutes.
- **Reference register:** *Plough Quarterly*, *Comment Magazine*, *Image Journal* for the typographic and color register. Maven and Reforge for the cohort-learning IA. Hallow for the calm contemplative surfaces.

---

## Typography

Self-host or load from Google Fonts. Avoid Inter / Roboto / Poppins as primary (overused). All three families chosen are open source.

| Role | Font | Why |
|------|------|-----|
| Display (hero, page titles) | **Fraunces** (variable, opsz + wght) | Soft slope, optical sizing, editorial warmth at large sizes. |
| Body (paragraphs, chat bubbles, reading surfaces) | **Source Serif 4** | Quiet companion to Fraunces; excellent at 16px; supports sustained reading. |
| UI / Labels / Chrome (buttons, nav, form labels) | **Geist** | Modern sans, restrained, doesn't compete with the serif. |
| Data / Tables (cohort triage, metrics) | **Geist** with `font-feature-settings: "tnum"` | Same family for consistency; tabular figures keep numbers aligned. |
| Code (rare; admin only) | **JetBrains Mono** | Fallback. Not used in primary surfaces. |

**Loading:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Geist:wght@400;500;600&display=swap" rel="stylesheet">
```

**Modular scale** (1.250 / major third):

| Token | Size | Line height | Usage |
|-------|------|-------------|-------|
| `--text-xs` | 12px / 0.75rem | 1.4 | Status pills, captions, labels |
| `--text-sm` | 14px / 0.875rem | 1.5 | UI buttons, table cells |
| `--text-base` | 16px / 1rem | 1.6 | Body text (Source Serif 4) |
| `--text-lg` | 18px / 1.125rem | 1.55 | Lead paragraph, chat bubbles |
| `--text-xl` | 22px / 1.375rem | 1.4 | Section headings (h3) |
| `--text-2xl` | 28px / 1.75rem | 1.3 | Page subheadings (h2) — Fraunces |
| `--text-3xl` | 38px / 2.375rem | 1.2 | Page titles (h1) — Fraunces |
| `--text-4xl` | 52px / 3.25rem | 1.1 | Marketing hero — Fraunces, opsz 96 |

---

## Color

- **Approach:** Restrained. Cream + warm ink + a single liturgical rose accent. Status colors only render when a status is being expressed.
- **Dark mode:** Surfaces redesigned (not just inverted). Saturation reduced ~15%. Accent lifted toward dusty rose.

### Light mode (default)

| Token | Hex | Role |
|-------|-----|------|
| `--bg` | `#FAF7F2` | App background — warm parchment |
| `--surface` | `#FFFFFF` | Cards, panels, modals |
| `--surface-2` | `#F4EFE6` | Secondary surface (e.g., active nav, hover bg) |
| `--ink` | `#1B1A18` | Primary text — warm near-black, never `#000` |
| `--ink-muted` | `#5C564E` | Secondary text, metadata |
| `--ink-faint` | `#8A8378` | Tertiary text, placeholders |
| `--hairline` | `#E8E1D6` | Dividers, borders |
| `--accent` | `#7C2D3A` | Primary action, at-risk flag — liturgical rose |
| `--accent-soft` | `#F2DDDF` | Accent background tint (soft hover, alert background) |
| `--accent-ink` | `#FAF7F2` | Text on accent (use parchment, not pure white) |

### Dark mode

| Token | Hex | Role |
|-------|-----|------|
| `--bg` | `#181614` | App background |
| `--surface` | `#221F1B` | Cards, panels |
| `--surface-2` | `#2C2823` | Secondary surface |
| `--ink` | `#F0EAE0` | Primary text |
| `--ink-muted` | `#A09686` | Secondary text |
| `--ink-faint` | `#7A7166` | Tertiary text |
| `--hairline` | `#3A3530` | Dividers |
| `--accent` | `#D08FA0` | Lifted dusty rose |
| `--accent-soft` | `#3A2329` | Accent background tint in dark |
| `--accent-ink` | `#181614` | Text on accent |

### Status colors (REC-2 named statuses)

Always render with a text label — never color-only. Background uses the soft tint, foreground uses the strong color.

| Status | Strong | Soft | Meaning |
|--------|--------|------|---------|
| Thriving | `#2F6B43` | `#E1EEE6` | High engagement, active reflection. |
| Steady | `#5C564E` (= `--ink-muted`) | `#F4EFE6` | Holding pattern, no action needed. |
| Needs check-in | `#B88A1F` | `#F6ECD2` | Soft alert — engagement softening. |
| At risk | `#7C2D3A` (= `--accent`) | `#F2DDDF` | Hard alert — intervene this week. |

Dark mode: strong colors lift ~15% (e.g., Verdant → `#5FA378`), softs become surface-2 tints.

### Contrast budget

All text/background combinations pass WCAG AA. The accent on parchment passes AAA for normal text (`#7C2D3A` on `#FAF7F2` ≈ 9.2:1). Never use the muted ink on `--surface-2` for body text — only metadata.

---

## Spacing

- **Base unit:** 4px.
- **Density:** Comfortable. Not a compact gradebook, not a luxury gallery.
- **Scale:** `2(2px) 4(4px) 8(8px) 12(12px) 16(16px) 24(24px) 32(32px) 48(48px) 64(64px) 96(96px)`

```css
:root {
  --space-2: 0.125rem;   /* 2px */
  --space-4: 0.25rem;    /* 4px */
  --space-8: 0.5rem;     /* 8px */
  --space-12: 0.75rem;   /* 12px */
  --space-16: 1rem;      /* 16px */
  --space-24: 1.5rem;    /* 24px */
  --space-32: 2rem;      /* 32px */
  --space-48: 3rem;      /* 48px */
  --space-64: 4rem;      /* 64px */
  --space-96: 6rem;      /* 96px */
}
```

---

## Layout

- **Approach:** Hybrid. Editorial asymmetry on home/landing surfaces; grid-disciplined on workbench, chat, and roster surfaces.
- **Grid:** 12 columns at `≥960px`, 8 at `≥640px`, 4 below. 24px gutter at desktop, 16px at tablet, 12px at mobile.
- **Reading width:** 720px max for editorial/long-form (formation arc, mentor reflections).
- **Dashboard width:** 1280px max for triage and roster.
- **Border radius:**

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Buttons, inputs |
| `--radius-md` | 8px | Cards, panels |
| `--radius-lg` | 12px | Large modal surfaces |
| `--radius-pill` | 9999px | Status pills, avatars |

No uniform bubbly radius across all elements. The hierarchy is intentional.

### Composition principles

- One typographic anchor per screen (the page title, set in Fraunces). Everything else defers.
- Hairline rules between sections, never heavy borders.
- Avatars: 32px or 40px circle, initial in Geist 500 over a tinted disk derived from the student's name (deterministic, soft palette).
- Empty states use a single italic line in `--ink-muted`. No illustrations.

---

## Motion

- **Approach:** Minimal-functional. Motion only when it aids comprehension (state change, focus, streamed-text reveal).
- **No** scroll-driven animation, no page transitions, no parallax, no decorative hover choreography.
- **Easing:** `enter` `ease-out`, `exit` `ease-in`, `move` `ease-in-out`.
- **Duration:**

| Token | Duration | Usage |
|-------|----------|-------|
| `--motion-micro` | 100ms | Button press, focus ring, hover tint |
| `--motion-short` | 150ms | Chat chunk reveal, status pill change |
| `--motion-medium` | 250ms | Card expand, panel slide |
| `--motion-long` | 400ms | Modal open (used sparingly) |

Honor `prefers-reduced-motion: reduce` — collapse all motion to instant.

---

## Component Primitives

Built as plain HTML + CSS — no framework. CSS variables drive theming.

### Button

Three weights: `primary` (accent fill), `secondary` (surface with hairline border), `ghost` (text only). All 40px tall, 12/16/20px horizontal padding by size. `--radius-sm`.

### Status pill

Inline element, `--radius-pill`, 12px text in Geist 500, soft background + strong foreground from the status color pair. Always label + (optional) dot.

### Chat bubble (mentor + student)

Body in Source Serif 4 at `--text-lg`, line-height 1.55. Student bubbles align right with `--accent-soft` background; mentor bubbles align left with `--surface` background and `--hairline` border. Streamed chunks reveal with `opacity 0→1` over `--motion-short`. "Mentor remembers:" pill list above the input shows the 3 recalled memory snippets.

### Profile card

Avatar (40px) + name (Fraunces `--text-xl`) + role/cohort (Geist `--text-sm` muted) + status pill on the right. Hairline divider below. Click → student profile (REC-5: outcomes log here).

### Triage row (REC-2 + REC-7)

| Avatar | Name + cohort | Status pill | Reason (one sentence) | Action button (ghost) |

The reason is the load-bearing element. "Marcus hasn't reflected in 9 days — a check-in this week would help." Never just a number.

### Reading card

For long-form surfaces (formation arc, weekly reflection). 720px max-width, Source Serif 4 body, Fraunces lead paragraph. Drop-cap optional on the first letter of the first paragraph for editorial moments.

---

## Accessibility Floor

- WCAG AA on all text/background combinations. Most pass AAA in light mode.
- Focus ring: 2px solid `--accent` with 2px offset. Visible on every interactive element.
- Touch targets ≥ 44px square.
- Status is never communicated by color alone — always paired with a text label.
- Honor `prefers-reduced-motion` and `prefers-color-scheme`.
- Form fields: visible labels (no placeholder-as-label), error messages programmatically associated, required marked in text not just color.
- Keyboard navigation: tab order matches visual order, all actions reachable without a mouse.
- Live regions: chat stream uses `aria-live="polite"`; triage status changes use `aria-live="polite"` with the status name spoken (not the color).

---

## Safe vs. Risk

### Safe choices (category baseline — readers expect these)

- Warm-paper background for thoughtful religious editorial. Every reference (Plough, Comment, Image) does this.
- Status pills with text + color for triage. Universal LMS pattern (Canvas, Maven, IntelliBoard).
- Variable serif for display. Established prestige choice in the editorial register.

### Risks (where the product gets its own face)

1. **Serif body in a web app.** Most SaaS defaults to sans. Cost: dense data is harder to scan, so tabular surfaces switch to Geist. Win: every reading surface signals "slow down, this matters" — the entire mood depends on this.
2. **Liturgical rose `#7C2D3A` as the only accent.** Recognizable to anyone formed in liturgical traditions; pairs naturally with cream. Cost: reads "too Catholic" if expanded to non-liturgical contexts — easy to retheme by swapping `--accent` per institution.
3. **Asymmetric editorial home.** Cohort dashboards default to symmetric 3-column heroes. Cost: less "balanced" looking. Win: the home is a cover, not a control panel.

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-04 | Initial design system created | Anchored to user stories #1-#5 and the 8 prioritized recommendations in COMPETITIVE-UX.md. |
| 2026-05-04 | Fraunces + Source Serif 4 + Geist | Editorial register; avoid Inter/Roboto overuse; serif body is the deliberate risk. |
| 2026-05-04 | Liturgical rose `#7C2D3A` as accent | Recognizable to formation context; pairs with cream; can be retheme'd per institution. |
| 2026-05-04 | Status labels (Thriving / Steady / Needs check-in / At risk) replace numeric scores | Direct port of REC-2; the reasons array gets rendered in plain English alongside. |

---

## Implementation notes (for the redesign work that follows)

- Existing `frontend/styles.css` will be replaced section-by-section, not all at once. The chat panel (REC-3) and triage view (REC-2 + REC-7) are P1 and should land first, since they're the surfaces with the highest user-impact delta.
- The proof-grid stat block in the current `index.html` ("10 tests / 4 formation engines / 100% open source") doesn't survive the role-shaped landing pivot (REC-1) and will be removed.
- Avatar generation is deterministic from the student name — `hsl(deg, 35%, 88%)` background where `deg = hash(name) % 360`, initial centered in `--ink`.
- All status logic lives in a single helper `statusFromRisk(risk)` that maps the existing `dropout_risk` API output to the four named statuses. Reasons array passes through unchanged, rendered as a single-sentence translation per code (`low_engagement` → "Engagement has dropped this week.").
