---
name: morning-check-in
description: Run a seminarian's morning check-in — the conversational twin of the /me page. Use when a seminarian (or someone acting for one) asks "how am I doing", "what's my status", "start my morning", or wants their reflection prompt, formation status, and next step. Requires the kingdom-come MCP tools.
---

# Morning check-in (Marcus's `/me`, as a conversation)

Recreate the webapp's morning surface: greeting → reflection prompt →
formation status in plain English → next step → open prayer items → an
offer to talk it through with the mentor.

## Steps

1. **Identify the student.** Default demo identity: `stu-marcus-r`. Use
   `get_student(student_id)` for name, calling, engagement, reflection count.
2. **Status.** Call `dropout_risk(engagement, reflection_count)`. Map the
   score to the same named status the webapp shows — never show the raw score:

   | score | status |
   |-------|--------|
   | 0 | Thriving |
   | 1 | Steady |
   | 2 | Needs check-in |
   | 3+ | At risk |

   Translate reason codes to plain English exactly like `frontend/status.js`:
   `low_engagement` → "Engagement has dropped this week." ·
   `few_reflections` → "Hasn't reflected in N days." ·
   `calling_drift` → "Recent reflections lean away from earlier discernment." ·
   `high_engagement` / `frequent_reflections` → positive phrasing.
3. **Next step.** `curriculum_recommend(calling, completed_content)` — present
   the top recommendation as one sentence, not a list dump.
4. **Prayer thread.** `list_prayer_requests(student_id=..., status="open")`
   and `list_prophecies(visible_to=...)`. Mention open petitions and any word
   awaiting the student's weighing ("One word is waiting for your discernment").
5. **Offer the mentor.** If the student wants to reflect, send their words via
   `chat_with_mentor(student_id, message)` and relay the reply. Surface what
   the mentor remembered (the `memory` part of the response) as a one-line
   "Mentor remembers: …" — the webapp's memory pills.

## Voice

Pastoral but precise — like the webapp's copy. One typographic anchor:
open with "Good morning, {first name}." Never clinical ("user", "risk
score 0.18"), never saccharine. Status is information offered, not judgment.
