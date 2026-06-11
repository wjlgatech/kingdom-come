---
name: cohort-triage
description: Run a formation director's cohort triage — the conversational twin of /cohort and /cohort/triage. Use when a director asks "who needs me this week", "triage my cohort", "how is the cohort doing", or wants check-in suggestions and the cohort's prayer rhythm. Requires the kingdom-come MCP tools.
---

# Cohort triage (Sister Theresa's `/cohort/triage`, as a conversation)

Recreate the director's working surface: one-sentence cohort pulse → the
2-3 students who need attention with named statuses and plain-English
reasons → one-click-equivalent next actions → counts-only prayer rhythm.

## Steps

1. **Roster.** `list_students()` (optionally `cohort_id`). Note the cohort size.
2. **Score everyone.** For each student call
   `dropout_risk(engagement, reflection_count)`. Map scores to the webapp's
   named statuses (0 Thriving · 1 Steady · 2 Needs check-in · 3+ At risk) and
   translate reason codes to plain English (see `frontend/status.js`):
   never surface a numeric score or a raw code like `low_engagement`.
3. **Lead with the pulse.** One sentence first, like the webapp:
   "3 of 24 students need attention this week. 21 are thriving or steady."
4. **Triage list.** Show only flagged students, at-risk first. Per student:
   name · status · one-sentence reason · a concrete suggested action
   ("a check-in this week would help", "read her last reflection via
   `get_student` before you call").
5. **Drill down on request.** `get_student(id)` for reflections, outcomes,
   risk history. `log_outcome(student_id, impact_score, description)` when the
   director reports a ministry outcome — confirm the effectiveness band back.
6. **Prayer rhythm.** `get_cohort_prayer_rhythm(cohort_id)` — report counts
   only ("4 of 24 active in the ledgers; 12 petitions, 5 answered").
   **Never request or repeat petition/word content in the director context**
   — content is visibility-scoped to the people it was entrusted to.
7. **Groups (on request).** `orchestration_plan(groups)` to suggest
   merge/split actions for small groups.

## Voice

Theresa triages 24 students in five minutes. Scan-friendly: pulse sentence,
short list, no tables unless asked. Pastoral language — "carrying heaviness",
not "high churn risk".
