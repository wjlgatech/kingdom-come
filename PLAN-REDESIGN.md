# PLAN-REDESIGN.md — Kingdom Come UI Redesign

*Synthesized from `COMPETITIVE-UX.md` (8 RECs), `DESIGN.md` (Editorial Pastoral system), and `design-preview.html` (visual reference for /me and /cohort/triage).*

## Scope

Replace the engineer dashboard at `/` with two role-shaped homes (Seminarian / Director) and seven role-specific surfaces. Preserve the existing 4-form workbench at `/admin/workbench` for engineers and API consumers. All UI rebuilt in vanilla HTML/CSS/JS using the tokens from `DESIGN.md`. Backend unchanged.

## Information Architecture (proposed)

| Route | Persona | Story / REC | Phase |
|-------|---------|-------------|-------|
| `/` | Both | Role-shaped landing — two doors with previews (REC-1) | P1 |
| `/me` | Marcus | Morning home: today's prompt + status + next path (Story #1, REC-1, REC-2) | P1 |
| `/me/chat` | Marcus | Continuing mentor thread with "Mentor remembers:" surface (Story #2, REC-3) | P1 |
| `/me/timeline` | Marcus | Formation arc — weekly cards (REC-6) | P2 |
| `/cohort` | Theresa | Altitude 1: cohort overview (one number + one sentence) (REC-7) | P2 |
| `/cohort/triage` | Theresa | Altitude 2: triage list with named statuses + plain-English reasons (Story #3, REC-2, REC-7) | P1 |
| `/cohort/groups` | Theresa | Drag-drop roster grouping with auto-suggest (Story #4, REC-4) | P2 |
| `/students/:id` | Theresa | Altitude 3: student profile + 2-click outcome logging (Story #5, REC-5, REC-7) | P1 |
| `/admin/workbench` | Engineer | Existing 4-form dashboard, untouched | P0 (already exists) |

P1 = first ship (covers all 5 stories at MVP). P2 = follow-up. Existing chat panel inside the workbench is removed; `/me/chat` replaces it.

## Navigation system

- **Global header (every page except `/`):** brand mark "KC" wordmark on the left → `/`. On the right: identity chip (`Marcus Reilly · Seminarian` or `Sister Theresa · Director`) with a discreet "Switch role" link. No top-nav menu — the role determines the surface set.
- **Per-role subnav** (small Geist `--text-sm` tabs under the header on every role-page):
  - **Seminarian:** `Today` (`/me`) · `Mentor` (`/me/chat`) · `Arc` (`/me/timeline`)
  - **Director:** `Cohort` (`/cohort`) · `Triage` (`/cohort/triage`) · `Groups` (`/cohort/groups`)
  - Active tab: `--accent` underline 2px, otherwise `--ink-muted`.
- **Breadcrumbs (director, /students/:id only):** `Cohort › Triage › Marcus Reilly`. Geist `--text-xs`, `--ink-faint`, ` › ` separator. Click any segment to navigate up.
- **Back affordance for the modal (outcome logging):** ESC closes; backdrop click closes; explicit close button top-right. Focus returns to the `+ Log outcome` button.
- **Engineer access to `/admin/workbench`:** small Geist `--text-xs` `--ink-faint` link bottom-right of `/`, label "Engineer workbench". No menu, no header link — engineers know where it is.

## Per-screen specifications

### `/` — Role-shaped landing

- **Layout:** Editorial asymmetric hero. Single Fraunces headline, two large door-cards stacked below with previews of what's behind each.
- **Door cards:** `Seminarian` (preview: "Today's reflection prompt + your status pill"), `Formation director` (preview: "3 students need a check-in this week"). Each card is one click → /me or /cohort.
- **Footer-class link:** small `/admin/workbench` link bottom-right for engineers.

### `/me` — Marcus's morning

Uses the design preview as the visual reference. Three stacked cards:
1. Today's reflection prompt (Source Serif 4 lead, primary action "Begin reflection").
2. Your formation status (status pill + one-sentence reason, ghost link "View full arc →").
3. Next in your path (curriculum step, two ghost actions).

Plus a persistent "Talk to mentor →" link to `/me/chat`.

### `/me/chat` — Continuing mentor thread

- Persistent thread, scroll-back visible.
- Above the input: "Mentor remembers:" pill list with the top-3 recalled memory snippets returned by `get_memory()`.
- "Manage memory" link at top-right → list of stored memories with delete buttons.
- Streamed bubbles render inline (already wired via WS chunks). No JSON `<output>`.

### `/cohort/triage` — Director's primary working surface

Uses the design preview as the visual reference. Per row: avatar · name + cohort · status pill · one-sentence reason · ghost action ("Schedule →" or "Profile →"). Sort: at-risk → needs check-in → steady → thriving.

### `/students/:id` — Student profile

- Header: avatar (40px) · Fraunces name · cohort + role · current status pill.
- Tabs: `Reflections` (chronological mentor convos), `Outcomes` (logged events), `Risk history` (weekly status transitions).
- Floating action: `+ Log outcome` button. Opens a modal that prefills `student_id`. Director enters only `impact_score` (slider) + `description` (textarea). Submit → outcome appears in the profile feed instantly.

### `/cohort/groups` — Roster grouping (P2)

- Left pane: roster, draggable.
- Right pane: named group columns accepting drops.
- "Suggest groups" button calls `/orchestration/actions` and pre-fills.
- "Confirm plan" submits the structured payload.

### `/me/timeline` — Formation arc (P2)

Vertical scroll of weekly cards: this week's reflections · mentor highlights · ministry outcome (if any) · next curriculum step. 720px reading width, Fraunces drop-cap on the first paragraph of the most recent week.

### `/cohort` — Cohort overview (P2)

Altitude-1 surface: one paragraph + one chart (median engagement trend over 8 weeks). Below: triage card snippet (top 3) with link to `/cohort/triage`.

## Hero copy & status threshold mapping

**Landing `/` headline:** *"Predictive intelligence for formation, not for performance."* Sub: *"Two doors. One for the seminarian discerning a calling. One for the director shaping a cohort."* No "Welcome to," no "Unlock the power of," no "Your all-in-one."

**Status thresholds** (from `dropout_risk.score` returned by the existing endpoint):

| Score | Status | Reason rendering |
|-------|--------|------------------|
| 0 | `Thriving` | Render the strongest positive signal (`high_engagement`, `frequent_reflections`) as one sentence. |
| 1 | `Steady` | Single sentence: "Holding pattern this week." |
| 2 | `Needs check-in` | Render the leading reason in plain English. |
| 3+ | `At risk` | Render all reasons concatenated as 1-2 sentences, with the strongest first. |

**Reason translations** (lookup table — single source of truth, lives in `frontend/status.js`):

| Reason code | Plain-English translation |
|-------------|---------------------------|
| `low_engagement` | "Engagement has dropped this week." |
| `few_reflections` | "Hasn't reflected in {N} days." |
| `calling_drift` | "Recent reflections lean away from earlier discernment." |
| `missed_outcomes` | "Hasn't logged a ministry outcome since {date}." |
| `high_engagement` | "Reflecting consistently and engaged in cohort discussions." |
| `frequent_reflections` | "Reflecting most days this week." |

## Interaction state matrix

Per-surface states. Every state is a feature, not a fallback.

| Surface | Loading | Empty | Error | Success | Partial / first-run |
|---------|---------|-------|-------|---------|---------------------|
| `/` | n/a (static) | n/a | n/a | n/a | First-run: same as default — no greeting personalization on `/`. |
| `/me` | Skeleton: 3 card outlines with shimmering hairlines (`--motion-medium` pulse). | Marcus has no curriculum yet → "Your formation path is still being shaped. Check back after your first 1:1." in italic `--ink-muted`. | Endpoint failure → card body becomes "Couldn't load your status. Try again in a minute." with retry ghost button. Single-card scope, never blocks the whole page. | n/a (no submit on this surface). | First-run: hero greeting "Welcome, Marcus. Let's start with one reflection." with primary action "Begin first reflection" pointing at `/me/chat`. |
| `/me/chat` | Mentor bubble shows "•••" cursor while LLM is streaming. Memory pills show skeleton. | Empty thread (first-time): mentor bubble "Hello, Marcus. What's on your heart today?" with no memory pills. | LLM 429/500 → mentor bubble becomes `--accent` outlined: "I'm not able to think clearly just now. Try again in a moment." Send button stays enabled. WS disconnect: status pill in header changes to "Reconnecting…" amber. | Send: streamed content reveals chunk-by-chunk over `--motion-short`. | If `get_memory()` returns 0 results: pills row collapses entirely (no "Mentor remembers:" label). |
| `/cohort/triage` | Skeleton: 5 row outlines. | All thriving (no triage needed): single editorial line in `--ink-muted` italic — *"No one needs a check-in this week. The cohort is steady."* with a small `Thriving` pill icon. | Endpoint failure → "Couldn't load the triage list." with retry. | n/a (no submit). | First-run (cohort just enrolled, insufficient data): "We're still learning your cohort's rhythm. Triage signals appear after week 2." |
| `/students/:id` | Skeleton: header outline + 3 tab outlines. | New student, no reflections/outcomes: `Reflections` tab shows italic "{Name} hasn't logged a reflection yet." `Outcomes` tab shows the `+ Log outcome` button enlarged with copy "Log {Name}'s first ministry outcome." | Outcome save fails → modal stays open, error toast at top of modal in `--accent`: "Save failed. Try again." Form values preserved. | Outcome save success → modal closes, new outcome appears at top of `Outcomes` tab with `--motion-medium` fade-in. | Risk history with <3 weeks: chart placeholder with "Building your risk picture — 3 weeks of data needed." |
| `/cohort/groups` (P2) | Skeleton: roster column + 2 empty group columns. | No suggested groups returned: empty group columns labeled "Drag students here to start." | `/orchestration/actions` failure → toast at bottom: "Couldn't suggest groups. You can still build them manually." | "Confirm plan" success → toast "Groups confirmed for {date}." Page resets to current state. | First-run: groups column shows seed columns "alpha, beta, gamma" pre-populated. |
| `/me/timeline` (P2) | Skeleton: 3 week-card outlines. | Marcus is new (<1 week): "Your arc starts after your first week. Come back Sunday." | Endpoint failure → page-level retry. | n/a (read-only). | n/a. |
| `/cohort` (P2) | Skeleton: paragraph + chart outline. | Cohort empty: "Add students to begin." | Endpoint failure → retry. | n/a. | First-week cohort: chart shows the single point + caption "Trend appears after 3 weeks." |

## Session arcs

Three storyboards. These exist so the implementer can feel the emotional shape, not just satisfy the spec.

### Marcus, first run (Tuesday morning, just enrolled)

1. He opens `/`. The hero says *"Predictive intelligence for formation, not for performance."* He picks `Seminarian` because his formation director told him to.
2. `/me` greets him: *"Welcome, Marcus. Let's start with one reflection."* The status pill is intentionally absent — no judgment until there's data.
3. He clicks `Begin first reflection`. He lands in `/me/chat`. The mentor opens with *"Hello, Marcus. What's on your heart today?"* No memory pills, because there's nothing to remember yet.
4. He types two paragraphs about feeling overwhelmed by Mission Theology readings. The mentor responds in three streamed sentences, ends with a single specific question.
5. He closes the tab. Total time: 4 minutes. He felt seen, not surveilled.

### Marcus, day 14 (Tuesday morning, in rhythm)

1. `/me`: *"Good morning, Marcus."* italic name in liturgical rose. Status pill: `Steady`. Reason: *"Holding pattern this week."* Today's prompt is contextual (the prompt service should rotate; if it doesn't yet, that's a P2 backend gap to flag).
2. He clicks "Talk to mentor about it" on the curriculum card. Lands in `/me/chat` with the curriculum step in scope. Memory pills show three of his prior conversations.
3. Mentor remembers a prior reflection ("you said the small group felt heavy"). He writes one paragraph. Mentor reflects back. He goes to morning prayer.

### Theresa, Friday afternoon (week 7, 24 students)

1. `/cohort/triage`. The page loads with three rows: Marcus (`Needs check-in`), Sarah (`At risk`), David (`Needs check-in`). The reasons are in plain English. She doesn't have to think — she scans and decides.
2. She clicks `Schedule →` on Sarah. (P2: opens calendar integration; P1: links to mailto with prefilled subject.)
3. She clicks `Profile →` on Marcus. Lands in `/students/:id`. Sees his last three reflections in the `Reflections` tab. Sees no outcomes logged in three weeks.
4. She clicks `+ Log outcome` because Marcus led a Sunday children's gathering. Modal opens with `student_id=marcus-r` prefilled. She drags the impact slider to 0.65, types one sentence, hits Save. Modal closes; the outcome appears at the top of his Outcomes tab. Total time: 11 seconds from `+` click to save.
5. She closes the tab. Total session: 4 minutes for the whole cohort.

## New components (to be added to DESIGN.md after implementation)

These don't exist in DESIGN.md's current component primitives section. Specced here, will be promoted to DESIGN.md when implemented:

- **Door card** (`/` only): 480px wide, 280px tall, `--surface` background, 1px `--hairline` border, `--radius-md`. Hover lifts hairline to `--accent` over `--motion-micro`. Inside: section label (Geist xs), title (Fraunces text-2xl), single-line preview of behind-the-door content, ghost arrow `→` bottom-right.
- **Outcome modal** (`/students/:id` only): centered, 480px wide, max-height 80vh, `--surface` with `--radius-lg`. Backdrop is `rgba(27, 26, 24, 0.6)`. Inside: header with student name in Fraunces, impact slider (0-1, snaps to 0.05), description textarea (Source Serif 4, 4 rows), Save (primary) + Cancel (ghost) row. Focus traps inside modal.
- **Memory pill** (`/me/chat` only): inline element, `--surface-2` background, 1px `--hairline` border, `--radius-pill`, Geist text-xs `--ink-muted`. Max-width 280px with text-overflow ellipsis. Hover reveals a small × that calls `delete_memory`.
- **Profile tab bar** (`/students/:id` only): horizontal, Geist text-sm, `--ink-muted` default, `--ink` + 2px `--accent` underline when active. Tabs: `Reflections`, `Outcomes`, `Risk history`. ARIA: `role="tablist"` with proper `aria-selected` / `aria-controls`.
- **Skeleton row/card**: `--surface-2` background with a subtle horizontal shimmer (1.5s `--motion-medium` linear infinite), no text. Used for all loading states.

## Per-surface motion

| Surface | Motion |
|---------|--------|
| `/` | Door card hover: hairline → `--accent` over `--motion-micro`. No entrance animation (page is static). |
| `/me` | Cards fade-in stagger over `--motion-medium` (50ms delay per card). Status pill change uses `--motion-short` color tween. |
| `/me/chat` | Streamed bubble chunks reveal `opacity 0→1` over `--motion-short`. New bubbles slide in from below 8px over `--motion-short`. Send button "press" `transform: scale(0.97)` over `--motion-micro`. |
| `/cohort/triage` | Row hover: background tint to `--surface-2` over `--motion-micro`. Status pill change: `--motion-short` color tween. |
| `/students/:id` | Tab switch: panel cross-fade over `--motion-short`. Modal: backdrop fade + dialog scale `0.96 → 1` over `--motion-medium`. |

All motion honors `prefers-reduced-motion: reduce` (instant transitions).

## Responsive & accessibility

### Breakpoints

| Range | Layout |
|-------|--------|
| `≥ 960px` | Full design. `/` doors side-by-side. `/me` cards single-column max 720px centered. `/cohort/triage` full-width rows. `/students/:id` two-pane (header + tabbed content). |
| `640-959px` | `/` doors stack vertically. `/me` unchanged (already centered). `/cohort/triage` rows wrap reason below name; status pill + action stay right. `/students/:id` collapses to one column. |
| `< 640px` (phone) | All grids collapse to single column. Subnav becomes a sticky horizontal scroll strip (no hamburger). Triage rows: avatar + name + status pill on top row; reason below; action button full-width below that. Modal becomes full-screen sheet. Memory pills wrap or scroll horizontally. Touch targets ≥ 44px. |

### Accessibility floor (specific to each surface)

- **Landmarks:** `<header>` with brand + identity chip · `<nav aria-label="Persona navigation">` for subnav · `<main>` for surface body · `<footer>` only on `/`. No `<aside>` unless a real complementary content area exists.
- **Headings:** Each surface starts with one `<h1>` (the surface title). Subsections use `<h2>`/`<h3>` in document order. No skipped levels.
- **Keyboard:**
  - `/` doors are `<a>` elements — Enter activates. Tab order: brand → door 1 → door 2 → engineer link.
  - `/me/chat` input is the default focus on page load. `Cmd/Ctrl + Enter` sends; `Enter` for newline.
  - `/cohort/triage` rows use `<a>` for the action — focusable in source order. Status pills are not focusable (informational).
  - `/students/:id` tabs follow ARIA tab pattern (Left/Right arrows move between tabs, Home/End jump to first/last).
  - Outcome modal: focus traps on open (first focusable element gets focus); ESC closes; focus returns to triggering button.
- **Screen reader:**
  - Chat thread: `aria-live="polite"` on the bubble container; new mentor messages announce when streaming completes (not chunk-by-chunk).
  - Triage status changes: `aria-live="polite"` with the status name read aloud (not the color).
  - Loading skeletons: `aria-busy="true"` on the container, with `aria-label="Loading {surface}"` until data arrives.
  - Memory pills: `<ul>` with `<li>` items; pills include `aria-label="Mentor remembers: {snippet}"` since the visible text is truncated.
- **Color contrast:** all text combinations pass WCAG AA. Status pills tested: each strong-on-soft pair ≥ 4.5:1. The accent rose on parchment passes AAA (9.2:1).
- **Touch targets:** minimum 44×44px for all interactive elements on phone. Status pills are not interactive — no minimum applies.
- **Forms (outcome modal):** label-for-input pairing (no placeholder-as-label). Required marked with `*` in text and `aria-required="true"`. Errors associated via `aria-describedby`.
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` collapses all motion to instant. Skeleton shimmer becomes static.

## Implementation phases

- **P1 (SHIPPED 2026-05-05):** `/`, `/me`, `/me/chat`, `/cohort/triage`, `/students/:id`, plus `/admin/workbench` preserved. Status helper, Jinja2 templates, all P1 components, 16 new tests, full E2E coverage. 55/55 tests passing across 3 consecutive runs.
- **P2 (SHIPPED 2026-05-05):** `/me/timeline` (REC-6 longitudinal arc), `/cohort` (REC-7 altitude-1 overview with median engagement chart), `/cohort/groups` (REC-4 drag-drop planner with orchestration suggestions). Subnav extended for both roles. 8 new tests (3 routes + 3 E2E + 2 subnav). 63/63 tests passing across 2 consecutive runs.
- **P3:** time-bounded shared challenges (REC-8).

## Backend changes required

**No new business-logic endpoints for P1.** All existing routes (`/predictive/dropout-risk`, `/curriculum/recommendations`, `/orchestration/actions`, `/outcomes`, `/ws/chat`, `/health`) stay unchanged.

Required additions in `backend/app.py`:

1. **5 thin HTML route handlers** (one per surface), each ~3 lines:

   ```python
   @app.get("/me", include_in_schema=False)
   def me_page(): return FileResponse(FRONTEND_DIR / "me.html")

   @app.get("/me/chat", include_in_schema=False)
   def chat_page(): return FileResponse(FRONTEND_DIR / "chat.html")

   @app.get("/cohort/triage", include_in_schema=False)
   def triage_page(): return FileResponse(FRONTEND_DIR / "cohort_triage.html")

   @app.get("/students/{student_id}", include_in_schema=False)
   def profile_page(student_id: str): return FileResponse(FRONTEND_DIR / "student_profile.html")

   @app.get("/admin/workbench", include_in_schema=False)
   def workbench_page(): return FileResponse(FRONTEND_DIR / "index.html")
   ```

2. **Modify the existing `/` route** to return `door.html` instead of `index.html`. The old `index.html` is reachable at `/admin/workbench`.

3. **WS protocol addition (`backend/api/ws_chat.py`):** before streaming chunks, emit a single `{"memory": [...]}` envelope so `/me/chat` can render memory pills. Implementation: in `handle_chat_ws`, capture the `memory` list returned by `get_memory()` and yield it as the first chunk; the WS handler wraps non-string yields as JSON envelopes. Total change: ~5 lines in `ai_pipeline.py` + ~3 lines in `ws_chat.py`. Existing `{chunk}/{done}/{error}` envelopes unchanged. (Backwards-compat verified by existing `tests/test_ws_chat.py`.)

P2 timeline view needs a new `/students/{id}/timeline` aggregation endpoint.

## Cohort & profile data source for P1

`/cohort/triage` and `/students/:id` need a list of students and per-student profile data, but no such endpoint exists today. P1 ships demo data in a frontend constants file:

```js
// frontend/cohort_data.js
export const COHORT = [
  { id: 'stu-marcus-r',  name: 'Marcus Reilly',  cohort: 'St. Aloysius S26', engagement: 0.42, reflection_count: 2, calling: ['evangelism'] },
  { id: 'stu-sarah-k',   name: 'Sarah Kim',      cohort: 'St. Aloysius S26', engagement: 0.18, reflection_count: 0, calling: ['liturgy'], drift: true },
  { id: 'stu-david-o',   name: 'David Okafor',   cohort: 'St. Aloysius S26', engagement: 0.40, reflection_count: 1, calling: ['pastoral_care'] },
  { id: 'stu-anna-t',    name: 'Anna Theroux',   cohort: 'St. Aloysius S26', engagement: 0.85, reflection_count: 4, calling: ['mission'] },
  // ... ~20 more for a realistic 24-student cohort
];

export const PROFILE_FIXTURES = {
  'stu-marcus-r': {
    reflections: [/* 3 most recent chat snippets */],
    outcomes:    [/* logged ministry events */],
    risk_history:[/* 8-week status transitions */],
  },
  // ... per student
};
```

Each surface calls the existing `/predictive/dropout-risk` endpoint per student to get the `score + reasons` (cheap; sync map over the 24-element array). Status mapping happens in `frontend/status.js`. When real data lands, replace `cohort_data.js` with fetch calls to a new `/cohort/students` endpoint — frontend interface stays identical.

## Frontend module API

`frontend/status.js` is the single source of truth. ES module, loaded via `<script type="module">` — no build step.

```js
// frontend/status.js
export const STATUS = Object.freeze({
  THRIVING: 'thriving',
  STEADY:   'steady',
  CHECK_IN: 'checkin',
  AT_RISK:  'risk',
});

export function statusFromRisk({ score }) {
  if (score >= 3) return STATUS.AT_RISK;
  if (score === 2) return STATUS.CHECK_IN;
  if (score === 1) return STATUS.STEADY;
  return STATUS.THRIVING;
}

export function statusLabel(status) {
  return { thriving: 'Thriving', steady: 'Steady', checkin: 'Needs check-in', risk: 'At risk' }[status];
}

const REASON_TRANSLATIONS = {
  low_engagement:       () => 'Engagement has dropped this week.',
  few_reflections:      ({ days = 9 }) => `Hasn't reflected in ${days} days.`,
  calling_drift:        () => 'Recent reflections lean away from earlier discernment.',
  missed_outcomes:      ({ since = 'three weeks' }) => `Hasn't logged a ministry outcome in ${since}.`,
  high_engagement:      () => 'Reflecting consistently and engaged in cohort discussions.',
  frequent_reflections: () => 'Reflecting most days this week.',
};

export function reasonsToSentence(reasons, ctx = {}) {
  if (!reasons || reasons.length === 0) return 'Holding pattern this week.';
  return reasons.map(r => REASON_TRANSLATIONS[r]?.(ctx) ?? r).join(' ');
}

// Avatar helpers (small enough to share this module)
export function avatarHue(name) {
  return [...name].reduce((h, c) => h + c.charCodeAt(0), 0) % 360;
}
export function avatarInitials(name) {
  return name.split(/\s+/).slice(0, 2).map(p => p[0] || '').join('').toUpperCase();
}
```

Per-surface JS imports: `import { STATUS, statusFromRisk, statusLabel, reasonsToSentence, avatarHue, avatarInitials } from '/static/status.js';`

## Storage keys (single namespace)

All client storage uses the `kc-` hyphenated prefix to match the already-shipped `kc-theme` key:

| Key | Type | Purpose |
|-----|------|---------|
| `kc-role` | localStorage | `'seminarian'` or `'director'` — set on first door click; cleared by `Switch role` |
| `kc-theme` | localStorage | `'dark'` or unset (already shipped in `frontend/app.js`) |
| `kc-student-id` | localStorage | demo identity for the current role (`'stu-marcus-r'` / `'fd-theresa'`) |

No `kc_*` underscore variants. No cookies in P1.

## Frontend file layout (P1)

```
frontend/
├── index.html              ← engineer workbench (existing, unchanged content)
├── door.html               ← / landing
├── me.html
├── chat.html
├── cohort_triage.html
├── student_profile.html
├── tokens.css              ← all CSS variables from DESIGN.md (light + dark + status)
├── components.css          ← buttons, status pills, chat bubbles, avatars, modal
├── door.css / me.css / chat.css / triage.css / profile.css   ← per-surface layout only
├── status.js               ← shared helpers (status, reasons, avatars)
├── cohort_data.js          ← P1 fake cohort + profile fixtures
├── chrome.js               ← shared header/subnav rendering (see CSS strategy below)
├── door.js / me.js / chat.js / triage.js / profile.js          ← per-surface entry points
└── app.js                  ← engineer workbench (existing, unchanged)
```

15 files. Flat directory keeps the existing `app.mount("/static", StaticFiles(directory=FRONTEND_DIR))` trivial; revisit nesting if file count exceeds ~20.

## Frontend stack

- Vanilla HTML/CSS/JS, no framework.
- Single `app.js` becomes a tiny client-side router (hash-routes or History API).
- CSS split into `tokens.css` (design system from `DESIGN.md`) + per-surface stylesheets.
- Drag-drop in P2: HTML5 dragstart/drop or `Sortable.js` (CDN, ~30KB) — decide at implementation time.

## NOT in scope (deferred design decisions)

| Decision | Why deferred |
|----------|--------------|
| Authentication / sign-in | Backend has no auth today. P1 hard-codes a demo seminarian (`stu-marcus-r`) and a demo director (`fd-theresa`). Real auth is a separate plan. |
| Calendar integration on `Schedule →` | P1 uses `mailto:` with prefilled subject. Real calendar API after auth lands. |
| Push notifications / email digests | Engagement layer, not a core surface. P3 at earliest. |
| Time-bounded shared challenges (Lent journey, REC-8) | Real cohort engagement engine, but premature without auth and stable user base. P3. |
| Mobile native apps | Web responsive is sufficient for both personas in P1. |
| Localization / RTL | English-only seminary deployments first. |
| Spiritual director / admin personas | Plan covers seminarian + formation director only. Director and admin are similar enough that admin can use the director surface initially. |
| Vector memory deletion UI on `/me/chat` | "Manage memory" is in scope; the deletion endpoint isn't wired backend-side yet. P1 shows the link disabled with tooltip "Coming soon." |

## What already exists (reuse, don't rebuild)

- **DESIGN.md** — color tokens, type scale, motion, status palette. Inherit verbatim. The new components specced above will be promoted into DESIGN.md after implementation.
- **design-preview.html** — visual reference for `/me` and `/cohort/triage`. Copy patterns wholesale; the implementer should treat the preview as the spec, not the freehand description.
- **Backend endpoints** — `/predictive/dropout-risk`, `/curriculum/recommendations`, `/orchestration/actions`, `/outcomes`, `/ws/chat`, `/health`. None require changes for P1.
- **Existing chat panel components** (`#chat-form`, `#chat-result`, WebSocket logic in `frontend/app.js`) — gut and rebuild as `/me/chat`. The WS protocol and JSON envelopes survive unchanged.
- **`backend/services/vector_memory.get_memory()`** — already returns top-k snippets per student. Render directly as memory pills.

## Test plan (P1)

22 paths. All E2E uses `wait_for_function` against actual content — never `wait_for()` on already-visible elements (race-flake lesson from commit `3087bda`).

### New test files

| File | Tests | Notes |
|------|-------|-------|
| `tests/test_routes.py` | 6 route handlers return 200 + correct HTML title and a canonical test-id per page | Pytest TestClient. ~30 lines total. |
| `tests/test_status_helper.py` | Playwright opens a tiny harness page, evaluates `statusFromRisk`/`statusLabel`/`reasonsToSentence`/`avatarHue` against fixtures | Avoids needing Node/Bun for JS unit testing. |
| `tests/test_e2e_door.py` | `seminarian → /me`, `director → /cohort`, `skip on revisit`, `Switch role` clears flag | 4 tests. |
| `tests/test_e2e_me.py` | `morning renders status + path`, `first-run no status pill`, `status card error state`, `talk-to-mentor link nav` | 4 tests. |
| `tests/test_e2e_chat.py` | `first message no pills`, `second message renders memory pills`, `disconnect shows reconnecting`, `pipeline error surfaces` | 4 tests. Reuses `LLM_FAKE_RESPONSE` env. |
| `tests/test_e2e_triage.py` | `three students with named status`, `empty state when all thriving`, `click profile navigates` | 3 tests. |
| `tests/test_e2e_profile.py` | `log outcome two clicks`, `modal focus trap + ESC closes`, `save failure keeps modal open`, `tab keyboard arrows` | 4 tests. |
| `tests/test_admin_workbench.py` | **REGRESSION** — port the entire `tests/test_e2e.py::test_e2e_formation_dashboard_common_and_edge_cases` here, retargeted at `/admin/workbench` | 1 large E2E. |

### Updated test files

| File | Change |
|------|--------|
| `tests/test_ui.py` | Replace assertions on `/` (`dropout-form`, `chat-result` test-ids) with assertions for the door page (`role-card-seminarian`, `role-card-director`). Move `submitDropoutRisk` script-content assertion to `test_admin_workbench.py`. |
| `tests/test_e2e.py` | Existing test moves to `test_admin_workbench.py`. The chat-flow test in this file also moves there OR is split into a fresh `test_e2e_chat.py` for the new `/me/chat` surface — recommend split: chat-flow E2E becomes the new test on `/me/chat`, and the workbench keeps just the 4-form coverage. |
| `tests/test_ws_chat.py` | Add `test_ws_emits_memory_envelope_before_chunks` — verifies the new `{memory: [...]}` envelope is the first message after a request and existing `{chunk}/{done}/{error}` envelopes still work. |

### Test plan artifact (`/qa` consumes this)

Written to `~/.gstack/projects/kingdom-come/jialiang.wu-main-eng-review-test-plan-{date}.md`.

## Failure modes

| Codepath | Realistic failure | Test? | Error handling? | User experience |
|----------|-------------------|-------|-----------------|-----------------|
| `/me` fetch `/predictive/dropout-risk` | Endpoint 500 | YES (`test_status_card_error_state`) | YES (per-card error) | "Couldn't load your status. Try again in a minute." |
| `/me/chat` WS connect | Server down | YES (`test_ws_disconnect_shows_status`) | YES (header pill "Reconnecting…") | Visible status, send button stays enabled |
| `/me/chat` LLM 429 | OpenAI quota | YES (existing `test_ws_pipeline_error_is_surfaced_as_json` covers the surface) | YES (mentor bubble accent-outlined) | "I'm not able to think clearly just now. Try again in a moment." |
| `/me/chat` memory envelope timing race | Memory yields after first chunk by mistake | YES (`test_ws_emits_memory_envelope_before_chunks` is exactly this) | N/A — protocol assertion | Pills appear after chunks (visible bug) |
| `/cohort/triage` empty cohort | All thriving, no rows | YES (`test_empty_state_when_all_thriving`) | YES (italic empty state) | "No one needs a check-in this week. The cohort is steady." |
| `/students/:id` outcome save | `/outcomes` POST fails | YES (`test_save_failure_keeps_modal_open`) | YES (modal stays + error toast) | Form values preserved, retry possible |
| `/students/:id` invalid student ID | Hand-typed URL | NO TEST | NO HANDLING | **Critical gap — page renders empty profile silently.** |
| Door client-side redirect | `localStorage` blocked (private browsing edge) | NO TEST | NO HANDLING | **Critical gap — `/me` renders without identity, throws on `student_id` access.** |

**Two critical gaps** flagged. Both have a single-line fix in the per-page JS:

- `/students/:id` invalid id → check fixture exists, otherwise render "Student not found in this cohort." with a back link to `/cohort/triage`.
- Door localStorage failure → wrap `localStorage.getItem` in a try/catch; on failure, always render the door (no redirect). Identity-dependent pages render a "Pick a role" banner that links back to `/`.

Add both to the test plan as `tests/test_routes.py::test_invalid_student_id_renders_not_found` and `tests/test_e2e_door.py::test_localstorage_blocked_falls_back_to_door`.

## Worktree parallelization

Three independent lanes after the shared `tokens.css` + `status.js` + `chrome.js` foundation lands:

| Step | Modules touched | Depends on |
|------|----------------|------------|
| 0. Foundation | `frontend/{tokens.css,components.css,status.js,chrome.js,cohort_data.js}`, `backend/app.py` (route handlers) | — |
| A1. Marcus surfaces | `frontend/{door.html,me.html,chat.html,door.{js,css},me.{js,css},chat.{js,css}}`, `backend/api/ws_chat.py` (memory envelope) | 0 |
| A2. Theresa surfaces | `frontend/{cohort_triage.html,student_profile.html,triage.{js,css},profile.{js,css}}` | 0 |
| A3. Test migration | `tests/test_admin_workbench.py`, `tests/test_ui.py` updates | 0 (independent of A1/A2 since it's repointing existing assertions) |

**Lanes:**
- Lane Foundation: step 0 (sequential, blocks everything).
- Lane Marcus: A1.
- Lane Theresa: A2.
- Lane Tests: A3.

A1, A2, A3 can run in **3 parallel worktrees** after Foundation merges. Conflict risk: A1 and A3 both touch test files that reference WS protocol; A1 changes the WS envelope, A3 just repoints existing tests. Coordinate by landing A1 first if there's a conflict on `tests/test_ws_chat.py`.

## NOT in scope (eng additions)

| Item | Why deferred |
|------|--------------|
| Backend `/cohort/students` endpoint | P1 uses fake `cohort_data.js`; real endpoint when real student data lands. |
| Backend `/students/:id` profile aggregation endpoint | Same — P1 uses `PROFILE_FIXTURES`. |
| `/memory/{student_id}` HTTP endpoint for chat pills | Folded into the WS protocol via the `{memory: [...]}` envelope (no new HTTP). |
| Memory deletion endpoint | "Manage memory" link disabled with tooltip in P1. |
| Server-side templating (Jinja2) | See E3 below — recommended in P1 but only if you accept the small framework expansion. |
| SSR / SSG / pre-rendering | All pages are dynamic per-request; SSR adds zero value at this scale. |
| Service worker / offline mode | Out of scope for a seminary cohort tool. |
| HTTP/2 server push | Browser-side preconnect to `fonts.gstatic.com` is in DESIGN.md; that's the right level. |

## What already exists (reuse, don't rebuild)

- **`backend/app.py`** — `app.mount("/static", StaticFiles(...))` already serves all of `frontend/`. New route handlers slot in alongside existing ones.
- **`backend/api/ws_chat.py`** — entire WS handler reused. Only addition: emit `{memory: [...]}` envelope before chunks.
- **`backend/services/ai_pipeline.py:handle_chat_ws`** — surfaces memory if we pass it through; ~3-line change.
- **`tests/test_ws_chat.py`** — existing 5 tests prove WS contract. Add 1 test for the new envelope.
- **`design-preview.html`** — visual reference for `/me` and `/cohort/triage` and the chat block. Implementer treats this as the spec.
- **Existing chat WS protocol** (`{chunk}/{done}/{error}` envelopes) — backwards-compatible.

## Resolved eng decisions (E1–E4)

All accepted as recommended on 2026-05-05.

| # | Decision | Resolution |
|---|----------|------------|
| E1 | Cohort/profile data source | **Fake data in `frontend/cohort_data.js`.** When real student database lands, fetch calls replace the `import`; frontend interface stays identical. |
| E2 | Memory pills protocol | **WS envelope.** `handle_chat_ws` yields the memory list as the first message; `ws_chat.py` wraps it as `{memory: [...]}` JSON before the chunk loop. Backwards-compat preserved. |
| E3 | Layout chrome DRY | **Jinja2 templates.** `Jinja2Templates(directory=FRONTEND_DIR)`. One `_base.html` extended by 5 surface templates. Adds `jinja2` to deps. |
| E4 | CSS architecture | **`tokens.css` + `components.css` + per-surface `*.css`.** Shared component styles in one file; layout-only per surface. |

These are the contract for implementation.

## Resolved design decisions (U1–U7)

All accepted as recommended on 2026-05-05.

| # | Decision | Resolution |
|---|----------|------------|
| U1 | Auth model for P1 | **Hard-coded demo identities** — `stu-marcus-r` for the seminarian, `fd-theresa` for the director. Identity chip shows the persona; `Switch role` link toggles a `localStorage` flag. Real auth is a follow-up plan. |
| U2 | SPA vs. multi-page | **Multi-page from FastAPI** — one HTML file per surface (e.g., `me.html`, `cohort_triage.html`, `student_profile.html`), shared `tokens.css`, small per-page JS modules. Native back-button. |
| U3 | Chat surface | **Standalone `/me/chat`** — full vertical room for the thread, persistent history, memory pills above input. |
| U4 | Memory pills | **Visible by default** — trust signal that the mentor is grounded. "Manage memory" link top-right of the chat surface (deletion endpoint is P2; link disabled with tooltip in P1). |
| U5 | Outcome logging | **Modal** — backdrop preserves the profile feed underneath; focus traps in modal; ESC closes. |
| U6 | `/` revisit behavior | **Skip-on-revisit** — `localStorage.kc_role` stored on first door click; subsequent visits redirect `/` → `/me` or `/cohort` (302 client-side). `Switch role` link in the header clears the flag. |
| U7 | Status threshold mapping | **Score 0=Thriving · 1=Steady · 2=Needs check-in · 3+=At risk.** Front-end-only mapping in `frontend/status.js`. Calibration revisited after real cohort data lands. |

These are the contract for implementation. Any deviation needs a fresh design decision.

## Approved Mockups

| Screen | Mockup path | Direction | Notes |
|--------|-------------|-----------|-------|
| `/me` (Marcus's morning) | `design-preview.html` (left mockup column) | Editorial Pastoral, three stacked cards, Fraunces italic name in liturgical rose | Visual is the spec. Implementer should match colors, type, and spacing exactly. |
| `/cohort/triage` (Director triage) | `design-preview.html` (right mockup column) | Per-row layout: avatar + name+reason + status pill + ghost action | Visual is the spec. Sort order: at-risk → needs check-in → steady → thriving. |
| `/me/chat` (chat block preview) | `design-preview.html` (chat-block section) | Memory pills above input, Source Serif 4 bubbles, mentor left + student right | Visual is the spec. Streaming behavior already wired via WS. |

P1 surfaces with no current visual mockup: `/`, `/students/:id`. Specs above are detailed enough to implement without; if visual evidence becomes useful, the gstack designer can generate it (currently quota-blocked on the OpenAI key).

## Final ratings (after fixes)

| Pass | Before | After |
|------|--------|-------|
| 1. Information Architecture | 6 | 9 |
| 2. Interaction State Coverage | 4 | 9 |
| 3. User Journey & Emotional Arc | 5 | 9 |
| 4. AI Slop Risk | 8 | 9 |
| 5. Design System Alignment | 8 | 9 |
| 6. Responsive & Accessibility | 3 | 9 |
| 7. Decisions | n/a | 7 surfaced, all resolved as recommended (2026-05-05) |
| **Overall** | **6** | **10** |

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — (skipped: OpenAI key quota-blocked) | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAN (pending E1–E4) | 12 issues found (5 arch, 5 code-quality, 0 perf, 22 test gaps), 2 critical failure modes flagged with single-line fixes |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAN | score: 6/10 → 10/10, 7 decisions surfaced and all resolved on 2026-05-05 |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**UNRESOLVED:** 4 eng-review choice-points (E1–E4) pending user resolution.
**VERDICT:** Eng review CLEAR pending E1–E4. Once resolved, plan is implementation-ready.
