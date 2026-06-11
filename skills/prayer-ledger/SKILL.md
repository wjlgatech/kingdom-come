---
name: prayer-ledger
description: Work the prayer + prophecy ledgers — the conversational twin of /me/prayer. Use when someone wants to bring a petition, mark a prayer answered, intercede for a peer, speak a prophetic word, weigh a word (1 Cor 14:29), record fulfillment, or see a track record. Requires the kingdom-come MCP tools.
---

# Prayer ledger (the `/me/prayer` surface, as a conversation)

Two parallel ledgers with longitudinal track records. Same vocabulary and
guardrails as the webapp — the agent is another door into the same room.

## Petitions

- **Bring one:** `submit_prayer_request(student_id, petition, visibility,
  recipient_ids, scripture?)`. Visibility defaults to `private`;
  `small_group` requires explicitly named recipients (there is no persistent
  group — the speaker entrusts specific people). Confirm who will see it
  before submitting.
- **Intercede:** `add_intercession(prayer_id, peer_id, message)` — "praying
  with you", optionally with a line of encouragement.
- **Resolve:** `mark_prayer_answered(prayer_id, status, testimony, witnesses)`.
  Status vocabulary (use these labels, not the raw enums):
  `answered_yes` → "Answered" · `partial` → "Answered in part" ·
  `no` → "Not as asked" · `superseded` → "Superseded — the asking changed".
  A testimony is required; ask for what actually happened.

## Prophetic words

- **Speak:** `submit_prophecy(speaker_id, addressed_to, word, weigher_ids)`.
  Three distinct weighers (2 peers + 1 leader); the speaker cannot weigh
  their own word. Default visibility `small_group`.
- **Weigh:** `weigh_prophecy(prophecy_id, weigher_id, judgment, notes)` with
  `confirm` / `refine` / `reject`. The 2-of-3 rule resolves automatically:
  two confirms lock "Confirmed"; two rejects "Not confirmed"; a refine after
  a second judgment means "Refine & re-speak" — invite the speaker to
  re-submit a reshaped word rather than treating it as failure.
- **Fulfillment:** `record_prophecy_fulfillment(prophecy_id, status,
  testimony, witnesses)` — only for confirmed words; `fulfilled` / `partial`
  / `unfulfilled`, testimony required.

## Track records

`get_prayer_track_record(student_id)` — answer rate, confirmation rate,
fulfillment rate. Present as counts and rates ("7 petitions, 4 answered"),
never as a grade. `get_cohort_prayer_rhythm(cohort_id)` is the director
aggregate: **counts only, never content**.

## Guardrails

- Honor visibility: never relay a private petition's content to anyone but
  its owner; small-group content only to its named recipients.
- Never editorialize a "no" answer or an unfulfilled word into failure —
  the ledger exists so the record can be honest.
- When a user asks "was that prophecy right?", show the weighing + fulfillment
  record and let it speak.
