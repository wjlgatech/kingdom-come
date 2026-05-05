# Competitive UX Research — Kingdom Come

*Research date: 2026-05-04 (updated with screenshots after installing `bun` + Playwright headless-shell)*
*Method: WebSearch verbatim mining + product pattern analysis + 8 homepage screenshots via gstack `browse`.*

---

## Executive Summary

The current Kingdom Come UI is an **API explorer disguised as a product** — every backend endpoint is one form on one page, and the student is asked to enter their own `engagement` score. Research across 8 adjacent products points to one consistent winning move in this category: **lead with the human job-to-be-done, not the data field.** Khanmigo opens with two tutor doors (not a settings panel); ClassDojo's student profile is portfolio-first (not metadata); Canvas New Analytics surfaces "students with low averages or who aren't submitting work on time" (not a query box). The single highest-leverage redesign decision is to replace the four endpoint-shaped forms with two role-shaped homes (Student / Director), each opening on the user's *next action*, and to push raw inputs into either auto-derived signals or admin-only views.

A second, equally strong signal: across Pi, ChatGPT, and Khanmigo, **chat is no longer a textarea — it's a named, continuing thread with visible memory**. Users explicitly value the feeling of being remembered ("Pi actually makes me feel like I'm being understood and learned"), and pattern leaders now expose "view, edit, or disable specific memories" as a first-class control. The current chat panel — a one-shot textarea with JSON-flavored output — fails this category convention.

---

## Competitors Analyzed

| # | Product | Category | Why included |
|---|---------|----------|--------------|
| 1 | Hallow | Formation / spiritual | Closest direct analog (Catholic formation app, community + cohorts) |
| 2 | Pray.com | Formation / spiritual | Mainstream prayer app with community wall + cohort features |
| 3 | Maven | Cohort-based learning | Instructor admin dashboard with status pipelines |
| 4 | Reforge | Cohort-based learning | "My Learning" student-side dashboard pattern |
| 5 | Khanmigo (Khan Academy) | AI tutor + teacher dashboard | Both sides covered: student tutor, teacher reports + flags |
| 6 | Pi.ai (Inflection) | Conversational AI mentor | Best-in-class "feels remembered" conversation UX |
| 7 | Canvas / IntelliBoard | LMS at-risk flagging | Gold standard for instructor risk-triage dashboards |
| 8 | ClassDojo | Roster + outcomes logging | Per-student profile UI + portfolio posting model |
| Bonus | Grouper.school | Group planning | Drag-drop student grouping (vs. typed structured text) |
| Bonus | ChatGPT (memory) | Conversational AI | Memory transparency / user controls — 2025 design pattern |

---

## Per-Competitor Analysis

### 1. Hallow

**Strengths**
- Minimal layout; clean focus on the meditation/prayer at hand. Bottom-nav for thumb reach.
- No ads (even on free tier) — reduces friction.
- "Pray 40 challenge" packages a 40-day journey as a *cohort goal*, not a content list.
- "Hallow Family" feature encourages connection through prayer intentions and shared experiences — community surface, not just content surface.

**Weaknesses (verbatim signal)**
- Reviews note the app is "not very intuitive" on first run; the *website* offers a "How to Pray" page to compensate. Onboarding gap.
- Heavily content-led; less personalized formation tracking.

**Pattern to steal:** *time-bounded shared challenges* (40-day) as a wrapper around individual practice, with social pressure as the engagement engine.

### 2. Pray.com

**Strengths**
- Content + community wall + audio Bible in one app.
- Push notifications keep daily routine front-of-mind ("UX elements like clean interfaces, short push-notifications, and reward animations increase daily engagement").

**Weaknesses (verbatim signal)**
- Trustpilot 2.0/5 with 17% recommend rate; users report navigation difficulty and billing/CS issues.
- "Some users find it difficult to navigate."

**Pattern to avoid:** stuffing too many surfaces into one app without clear primary action per session.

### 3. Maven

**Strengths**
- Students tab has explicit **status pipeline**: waitlisted → applied → application incomplete → accepted → enrolled → dropped off. Each status has automated email campaigns attached.
- CSV export for filtered student lists.
- Manual "+Add user" on the Students tab.

**Weaknesses**
- Admin-heavy; instructor view is more about funnel ops than weekly pastoral check-in.

**Pattern to steal:** *named statuses* (not numeric scores) for at-a-glance triage. Instead of "risk score 0.18," use status labels like "needs check-in," "missed two reflections," "thriving."

### 4. Reforge

**Strengths**
- "My Learning" dashboard surfaces *current course progress, completed courses, guides, artifacts, assigned learning plans* — answers "what's next?" on landing.

**Weaknesses**
- Built for self-directed adult learners; not optimized for instructor-mediated formation.

**Pattern to steal:** student home = "my next thing" + "my recent thing" + "my assigned thing" — three columns max.

### 5. Khanmigo (Khan Academy AI tutor)

**Strengths — student side**
- Welcome screen offers **two tutor options** (math/science vs. humanities) — not a textarea but a *door*. The choice IS the onboarding.
- Exploratory area: "choose a topic of interest, and then the AI assistant will offer some questions to explore."
- Tutor mode: never gives answers, *guides* the learner — pedagogically aligned.

**Strengths — teacher side**
- Teacher Dashboard top-left link → data + analytics area. Tabs for class progress, AI activities, chat history.
- **Reports show:** number of Khanmigo chats, whether any flagged for moderation, messages per conversation, activities per student.
- Moderation system flags emotional-distress signals → notifies teacher → mental-health counselor intervention.
- Email alerts to teacher for serious flags.

**Verbatim:** *"Khanmigo's interface borrows from classic Khan Academy simplicity: clean layouts, big buttons, and friendly color schemes. Key controls stay one click away."*

**Patterns to steal:**
- Student app opens on a **role-shaped door**, not a form.
- Teacher dashboard surfaces flagged conversations with reasons + recommended actions; intervention is one click, not a workflow.

### 6. Pi.ai (Inflection)

**Strengths**
- "Excellent memory that persists across all conversations and remembers details from days or weeks ago and brings them up naturally, creating a sense of genuine continuity."
- Voice mode with realistic pauses + emotional intonation — surpasses Replika and Character.AI per reviews.
- 2M+ users acquired purely word-of-mouth.

**Verbatim user quotes**
- *"Pi actually makes me feel like I'm being understood and learned."*
- *"This is the only app that I've found will give me the experience of speaking to the AI directly for a more organic conversation."*

**Weaknesses**
- Memory is implicit, not user-editable — a regression vs. ChatGPT's transparency model.
- Message caps in 2025 to balance infrastructure cost.

**Pattern to steal:** the *feeling* of being remembered is a category-defining moat for AI mentors. The pipeline already supports this server-side — the UI must surface it (e.g., "Mentor remembers: you mentioned leading a cohort last week").

### 7. Canvas / IntelliBoard (at-risk dashboards)

**Strengths**
- New Analytics: interactive graphs of grades, activity, communication.
- **Admin Analytics has three named dashboards: Overview, Course, Student** — separation of concerns by altitude.
- Student dashboard: "identify students with low averages or who aren't submitting work on time" — specific, action-prompting language.
- IntelliBoard layer: "automatically flagging course activity and engagement levels and students at risk" + message-students-by-status.

**Pattern to steal:** **three altitudes** (Cohort overview → Course/cohort detail → Individual student). Each level surfaces *the one thing the user does next* at that altitude.

### 8. ClassDojo

**Strengths**
- Student profile = name + avatar + **portfolio posts + teacher feedback points** — a unified per-student hub, not a settings page.
- Portfolio posts: text, photos, files, videos. Teacher *approves* before parent sees.
- Multiple low-friction student-login paths (QR, 6-letter code, Google, link).

**Patterns to steal:**
- Per-student page = chronological feed of artifacts (reflections, outcomes, mentor chats) — not a metadata table.
- **Teacher posts on a student's profile, not via a separate "log outcome" form.**

### Bonus: Grouper.school

**Pattern:** Algorithm proposes groups, human can drag-and-drop to adjust before finalizing. Direct manipulation > typing `alpha: Ana, Bo`.

### Bonus: ChatGPT (memory + projects)

**Pattern:** "User-controlled persistent memory with transparent project separation." User can view/edit/disable specific memories. *"Continuity is crucial for complex tasks... an agent that remembers helps organize thinking and feels more like a real tool rather than starting over each time."*

---

## Cross-Competitor Patterns

### Genre conventions (appear in ≥3 products)

| # | Pattern | Seen in | What it solves |
|---|---------|---------|----------------|
| P1 | **Role-shaped landing screen** (not a settings/form page) | Khanmigo, Reforge, ClassDojo | First-second of the session is decisive. Forms feel like work; doors feel like progress. |
| P2 | **Continuing AI thread with explicit memory** | Pi, ChatGPT, Khanmigo | Conversational repetition is the #1 friction in AI assistants. |
| P3 | **At-risk flags with named reasons + suggested action** | Canvas/IntelliBoard, Khanmigo, Early Alert systems | A score by itself doesn't drive intervention. A *reason* does. |
| P4 | **Per-student unified profile** (portfolio + observations + chats) | ClassDojo, anecdotal note tools, Khanmigo | The student is the unit, not the form. Posts go *on the profile*. |
| P5 | **Status labels over scores** for triage | Maven (status pipeline), Canvas, Early Alert | "Needs check-in" beats "0.18" — names a job-to-be-done. |
| P6 | **Direct manipulation for grouping** (drag/drop or roster pick) | Grouper, edX, Moodle Groupings | Typing structured text loses on every metric. |
| P7 | **Time-bounded shared challenges** | Hallow (Pray 40), Maven cohorts, Reforge cohorts | Cohort + deadline = engagement engine. |

### Anti-patterns (multiple products do badly OR get complaint volume)

| # | Anti-pattern | Evidence | What to avoid in Kingdom Come |
|---|--------------|----------|-------------------------------|
| AP1 | Stuffed multi-feature home with no primary action | Pray.com 2.0/5 + "difficult to navigate" complaints | Don't put all 4 forms on one page |
| AP2 | Implicit AI memory (works but invisible) | Pi.ai noted as a regression vs. ChatGPT's transparency | Show *what* the mentor remembers |
| AP3 | Numeric risk scores without explanation | Generic LMS "0–1 risk" widely reported as low-actionability | Always render the *reason* with the flag |
| AP4 | First-run intuition gap requiring external help docs | Hallow's "How to Pray" web page exists *because* the app needs explaining | Onboarding belongs in the product |
| AP5 | Free-text ID fields in a system with a known roster | (current Kingdom Come outcome form) | Pick from roster, never type student_id |

---

## Unpopulated Space — Where Kingdom Come Can Win

Mapping jobs-to-be-done across the genre:

| Job-to-be-done | Solved well by | Gap / opportunity |
|----------------|----------------|--------------------|
| "What should I work on this morning?" | Reforge ("My Learning"), Khanmigo doors | None solve it for *spiritual formation* specifically |
| "Talk to a mentor that remembers me" | Pi.ai (best feel), ChatGPT (best transparency) | None grounded in *formation curriculum + cohort context* |
| "Which 2-3 students need a check-in?" | Canvas/IntelliBoard, Early Alert, Khanmigo | None expressed in *pastoral* language ("low engagement" → "carrying heaviness") |
| "Plan small groups by hand" | Grouper.school | Not integrated with formation curricula or risk signals |
| "Log a ministry outcome in two clicks" | ClassDojo (portfolio model) | Not integrated with predictive engines or curriculum |
| "Show me my own formation arc over time" | None | **Wide open.** Memory + outcomes + curriculum recommendations all exist in V8 backend; nothing surfaces them as a narrative. |

The **arc-over-time view** ("Marcus's formation timeline") is the single biggest greenfield. The data exists; no competitor renders it.

---

## Recommendations — Mapped to the 5 User Stories

Each recommendation has an evidence anchor, a user-impact statement, an implementable description, and priority.

### REC-1: Replace the engineer dashboard with two role-shaped homes
**Story:** #1 (Marcus morning snapshot), #3 (Theresa cohort triage)
**Evidence:** Khanmigo's two-door welcome screen; Reforge's "My Learning" home; Canvas's three-altitude dashboard (Overview/Course/Student); Pray.com's complaints when a single home tries to do everything.
**Why it matters:** First screen decides whether a user feels work-in-progress or work-in-front. Forms feel like work; doors feel like progress.
**What to build:**
- Landing screen at `/` shows two big cards: **"I'm a seminarian"** and **"I'm a formation director."**
- Each leads to a role-specific home, not the current 4-form workbench (which becomes `/admin/workbench` for engineers).
- Seminarian home: three columns — Today's reflection prompt · My next curriculum step · Talk to my mentor.
- Director home: three altitudes — Cohort overview (one number + one sentence) · Triage list (2–3 students with reasons) · Quick log.
**Priority:** P1 · **Effort:** M

### REC-2: Replace numeric risk scores with named reasons in pastoral language
**Story:** #1 (Marcus seeing his own flag), #3 (Theresa triage)
**Evidence:** Maven's status-pipeline labels (waitlisted/dropped/enrolled); Canvas's "students with low averages or who aren't submitting work on time"; Early Alert systems' "feedback and recommended actions" pattern; widespread anti-pattern of bare numeric scores.
**Why it matters:** "0.18 risk" doesn't tell Theresa what to do. "Marcus hasn't reflected in 9 days — a check-in this week would help" does. Same data, drastically different action rate.
**What to build:**
- Translate `dropout_risk` output to status labels: **Thriving · Steady · Needs check-in · At risk.**
- Each flag renders the *reasons array* in plain English ("low_engagement" → "Engagement has dropped this week").
- Each at-risk card includes a one-click **"Schedule check-in"** action that links to the chat or the student profile.
**Priority:** P1 · **Effort:** S (backend already returns `reasons`)

### REC-3: Promote chat to a continuing thread with visible memory
**Story:** #2 (Marcus mentor conversation)
**Evidence:** Pi.ai's "feels understood" verbatims (2M users on word-of-mouth alone); ChatGPT's user-controlled memory pattern as 2025 best practice; Khanmigo's chat-history-per-student surface.
**Why it matters:** The V8 vector memory works server-side, but the UI throws away the thread on each send. Users won't *feel* the memory unless we render it.
**What to build:**
- Chat surface = persistent thread per student, scroll-back visible.
- Above the input, a small "Mentor remembers:" pill list (top 3 recalled memory snippets) — direct port of `get_memory()` results.
- "Manage memory" link → list with delete buttons (ChatGPT pattern).
- Streaming bubble (already wired via WS chunks) renders inline, not in a JSON `<output>`.
**Priority:** P1 · **Effort:** M

### REC-4: Replace the orchestration textarea with a roster-based group planner
**Story:** #4 (Theresa class planning)
**Evidence:** Grouper.school's drag-and-drop pattern; widespread LMS group-management UIs (Moodle Groupings, edX cohorts); the typed-text format is unique to no successful product.
**Why it matters:** Typing `alpha: Ana, Bo` is a parse-failure waiting to happen and forecloses on a director who actually wants to *think* about who goes where.
**What to build:**
- Roster pane (left): list of students with avatars, drag handles.
- Groups pane (right): named columns (alpha/beta/...) accepting drops.
- "Suggest groups" button calls `/orchestration/actions` and pre-fills based on current cohort.
- Confirm button submits to the same endpoint with the structured payload.
**Priority:** P2 · **Effort:** M-L (drag-drop without a framework is non-trivial in vanilla JS — consider a tiny library like `Sortable.js` or HTML5 dragstart/drop)

### REC-5: Move outcome logging onto the student profile (two clicks)
**Story:** #5 (Theresa outcome logging)
**Evidence:** ClassDojo's portfolio-on-profile model; anecdotal-note tooling consensus that observations belong "on a digital tab for each student"; the principle that the *student is the unit, not the form*.
**Why it matters:** Friction kills logging. If Theresa has to remember a student_id, navigate to a separate form, and type a description, half the outcomes never get logged.
**What to build:**
- Each student in the cohort triage list → click → student profile page.
- Student profile = chronological feed of: reflections (from chat), outcomes (logged), mentor highlights, risk transitions.
- "+ Log outcome" button on the profile pre-fills `student_id`; director only enters `impact_score` and `description`.
- Two clicks: profile → "+ Log outcome" → submit.
**Priority:** P1 · **Effort:** M

### REC-6 (greenfield): Marcus's formation arc — the time-axis view nobody else does
**Story:** #1 stretch / #2 deeper resonance
**Evidence:** No competitor in the analyzed set renders a longitudinal *narrative* of formation. ChatGPT memory + Pi continuity + Canvas analytics each capture pieces but never assemble them.
**Why it matters:** The V8 backend already produces all the inputs (vector memory of conversations, outcomes log, curriculum recommendations, risk transitions). Synthesizing them as a timeline turns "yet another LLM chat app" into a **formation operating system**.
**What to build:**
- `/me/timeline` for the seminarian — vertical scroll of weekly cards: "this week's reflections, mentor highlights, ministry outcome, next curriculum step."
- Same view as `/students/<id>/timeline` for the director.
**Priority:** P2 (do after P1s land) · **Effort:** M

### REC-7: Three-altitude information architecture for the director
**Story:** #3 (cohort triage)
**Evidence:** Canvas Admin Analytics' explicit Overview / Course / Student split — the convention works because each level corresponds to a real job-to-be-done.
**Why it matters:** Directors do three different jobs at three different zooms. Mixing them on one screen creates the current "where do I start?" problem.
**What to build:**
- **Cohort overview:** one paragraph + one chart of the cohort's pulse.
- **Triage list:** 2–3 cards with reasons + actions (REC-2).
- **Student profile:** REC-5.
- Breadcrumbs between the three.
**Priority:** P1 · **Effort:** S structurally (it's a layout decision, not new features)

### REC-8 (lower-priority, watch): Time-bounded shared challenges
**Evidence:** Hallow's "Pray 40" + Maven/Reforge cohort model.
**Why it matters:** Cohort + deadline is a known engagement engine.
**What to build:** A "Lent journey" or "discernment 30-day" wrapper around the existing curriculum.
**Priority:** P3 · **Effort:** M

---

## Pattern Comparison Matrix

| Pattern | Hallow | Pray | Maven | Reforge | Khanmigo | Pi | Canvas | ClassDojo | **Kingdom Come (now)** | **Kingdom Come (target)** |
|---------|:------:|:----:|:-----:|:-------:|:--------:|:--:|:------:|:---------:|:----------------------:|:--------------------------:|
| Role-shaped landing | ◐ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | **✗** | **✓** (REC-1) |
| Continuing AI thread w/ memory | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | **✗** | **✓** (REC-3) |
| Named reasons w/ flags | ✗ | ✗ | ✓ | ◐ | ✓ | n/a | ✓ | ✗ | **✗** | **✓** (REC-2) |
| Per-student profile hub | ✗ | ✗ | ✓ | ✗ | ✓ | n/a | ✓ | ✓ | **✗** | **✓** (REC-5) |
| Status labels (not scores) | ✗ | ✗ | ✓ | ✗ | ◐ | n/a | ✓ | ◐ | **✗** | **✓** (REC-2) |
| Direct-manipulation grouping | ✗ | ✗ | ✗ | ✗ | ✗ | n/a | ◐ | ✗ | **✗** | **✓** (REC-4) |
| Cohort time challenges | ✓ | ◐ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | **✗** | **◐** (REC-8) |
| Longitudinal arc view | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ◐ | ✓ | **✗** | **✓** (REC-6) |

✓ = strong · ◐ = partial · ✗ = absent

---

## Sources

**Hallow / formation**
- [Catholic Prayer App, Hallow: 6-Month Review (Medium)](https://medium.com/catholicism-for-the-modern-world/catholic-prayer-app-hallow-6-month-review-88a699674229)
- [Hallow App Features](https://hallow.com/features/)
- [pray.com Reviews — Trustpilot](https://www.trustpilot.com/review/pray.com)

**Cohort learning**
- [Maven — Student Management in the Admin Dashboard](https://help.maven.com/en/articles/6069488-student-management-in-the-maven-admin-dashboard)
- [Maven.com Product Breakdown (Medium)](https://medium.com/@bramkrommenhoek/maven-com-product-breakdown-bdd506289780)
- [Reforge — New UI: My Learning](https://reforge.helpscoutdocs.com/article/236-new-reforge-ui-my-learning)

**AI tutors / mentors**
- [Khanmigo — Welcome to your AI teaching assistant](https://www.khanacademy.org/khan-for-educators/khanmigo-for-educators/xb4ad566b4fd3f04a:welcome-to-khanmigo-your-new-ai-teaching-assistant)
- [Khanmigo — Teacher reports on Classroom pilot](https://support.khanacademy.org/hc/en-us/articles/38554738905997-What-teacher-reports-are-available-on-the-Khanmigo-Classroom-pilot)
- [Khanmigo — How are administrators alerted to moderated chats?](https://support.khanacademy.org/hc/en-us/articles/21943797567629-How-are-administrators-alerted-to-moderated-Khanmigo-chats)
- [Pi AI Review 2025 — 30-Day Test (AI Companion Guides)](https://aicompanionguides.com/blog/30-days-with-pi-starting-empathy-experiment/)
- [Pi AI mobile vs web (DataStudios)](https://www.datastudios.org/post/pi-ai-mobile-vs-web-features-differences-and-performance-in-2025)
- [Designing Trustworthy AI Assistants — 9 UX Patterns (OrangeLoops)](https://orangeloops.com/2025/07/9-ux-patterns-to-build-trustworthy-ai-assistants/)
- [Design Patterns for Long-Term Memory in LLMs (Serokell)](https://serokell.io/blog/design-patterns-for-long-term-memory-in-llm-powered-architectures)

**At-risk / instructor dashboards**
- [Canvas New Analytics — overview](https://www.liverpool.ac.uk/media/livacuk/centre-for-innovation-in-education/digiguides/introduction-to-new-analytics/introduction-to-new-analytics.pdf)
- [Canvas Admin Analytics — Instructure press release](https://www.instructure.com/press-release/instructure-launches-canvas-admin-analytics-providing-powerful-lms-engagement)
- [Better Together — Canvas + IntelliBoard](https://www.instructure.com/resources/blog/better-together-unlocking-learning-analytics-with-canvas-lms-and-intelliboard)
- [Designing Early-Alert Systems That Actually Help](https://cfder.org/designing-early-alert-systems-that-actually-help-at-risk-students/)
- [Awareness to Action: Student Knowledge of Early Alert (MDPI)](https://www.mdpi.com/2076-3417/15/11/6316)

**Roster / outcomes**
- [ClassDojo — What are Student Profiles](https://help.classdojo.com/hc/en-us/articles/204422155-What-are-ClassDojo-Student-Profiles)
- [ClassDojo — How to Post on a Student's Portfolio](https://help.classdojo.com/hc/en-us/articles/360024315052-How-to-Post-on-a-Student-s-Portfolio)

**Group planning**
- [Creating Student Groups with Grouper (AVID)](https://avidopenaccess.org/resource/creating-student-groups-with-grouper/)

---

## Visual Evidence — Screenshots

Captured to `.gstack/ux-research/screenshots/` (1440×900 viewport).

| File | Page | Visual pattern reinforced |
|------|------|---------------------------|
| `khanmigo-home.png` | khanmigo.ai home | **Three explicit role-doors** in hero ("For districts / For teachers / For learners"), each with its own preview tile. Confirms REC-1. |
| `khanmigo-teachers.png` | khanmigo.ai/teachers | Hero shows a **chat preview with class/student selector inside the chat itself** — chat is a *workspace*, not a textarea. Reinforces REC-3. Also: "5 classes of 35 students? Khanmigo can help with that" — direct numerical positioning that maps cleanly to Theresa's 24-student cohort. |
| `maven-home.png` | maven.com home | Hero **tabbed action bar with 3 doors**: "Cohort-based Courses / 1-day workshops / Free Lightning Lessons." Same role-/intent-shaped landing pattern as Khanmigo. |
| `reforge-home.png` | reforge.com home | Cohort-based learning hero centered on instructor faces + course cards (trust signal: who's teaching, not what's the platform). |
| `classdojo-home.png` | classdojo.com home | **Warm, illustrated, community-framing aesthetic** — tactile cards with rounded corners and avatar-led trust. "Where classrooms become communities" headline. Worth borrowing the *register* (community of formation, not enterprise dashboard) even if not the K-12 visual idiom. |
| `hallow-home.png` | hallow.com home | Spiritual-formation product visual register: subdued navy + cream palette, calm typography, single-CTA hero. Less is more. |
| `pray-home.png` | pray.com home | Content-heavy stacked carousels — illustrates the AP1 anti-pattern (no clear primary action). |
| `canvas-home.png` | instructure.com/canvas | Enterprise LMS marketing surface; not the dashboard itself, but confirms the "by altitude" segmentation language ("for higher ed / K-12 / districts"). |

**Pi.ai screenshots not captured** — both `pi.ai/talk` and `heypi.com/talk` returned 403 (Cloudflare bot block). Verbatim research from Track B already covered this product strongly enough for the report.

## New visual patterns added to the recommendations

After reviewing the screenshots, two refinements:

- **REC-1 refinement.** The role-door pattern (Khanmigo, Maven) doesn't just label the door — it *previews what's behind it* with a small tile (chat preview, course list, etc.). Apply this to Kingdom Come: the seminarian door previews "today's reflection prompt"; the director door previews "2 students need a check-in this week."
- **New REC: Aesthetic register matters in this space.** Hallow's calm/contemplative palette and ClassDojo's warm/communal aesthetic both succeed because they signal *what kind of activity this is* before any text loads. The current Kingdom Come palette reads as enterprise SaaS (cool grays, sharp grids), which mis-cues a formation product. This is a `/design-consultation` deliverable, not an REC line item, but worth flagging upstream.

---

## Status: DONE

- All 8 successful screenshots captured at 1440×900 after installing `bun` and symlinking the older Playwright headless-shell (1208 → existing 1217). Stored at `.gstack/ux-research/screenshots/`.
- Pi.ai unreachable from this runtime (Cloudflare 403 on both `pi.ai/talk` and `heypi.com/talk`). Mitigated by strong text-track verbatim coverage. If a Pi screenshot is required, opening it in your authenticated browser and saving manually is the pragmatic path.
- Reddit-specific verbatim mining returned thinner results than expected — search adapted to G2/Trustpilot/blog sources. Qualitative signal landed (Pi user quotes, Pray.com Trustpilot rating, Hallow intuition complaints).
- All 8 priority recommendations are evidence-anchored to ≥1 verbatim or screenshot.
