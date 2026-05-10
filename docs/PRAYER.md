# Prayer + prophecy track records

Two parallel ledgers, both with longitudinal track records:

1. **Prayer** — petitions submitted, intercessions logged, answers recorded.
2. **Prophecy** — prophetic words spoken, weighed by 2-of-3 designated weighers (1 Cor 14:29), then tracked through to fulfillment or non-fulfillment.

The point isn't a prayer feed or a worship room. The point is a **track record** for both — was this prayer answered? was this prophecy confirmed? was it ultimately fulfilled? — kept rigorously enough that a director can see, over a year, how a student's discernment is maturing.

## Prayer ledger

### Status flow

```
open → (watching) → answered_yes / partial / no / superseded
```

Every resolved prayer carries:

- **status** — one of the four resolution buckets (powers track-record stats).
- **testimony** — free text describing how the prayer was answered (preserves the spiritual story).
- **witnesses** — optional list of student/director ids who can attest.
- **answered_at** — when the answer was recorded.

### Visibility

Three levels: `private` (default for prayer — interior life is private until the petitioner shares it), `small_group` (speaker explicitly designates recipient peers), `cohort`. The `visible_to=<viewer_id>` filter on list endpoints enforces the policy from the viewer's perspective. A director can audit aggregate counts without ever reading content via `/api/cohorts/{id}/prayer-rhythm`. Prophecy uses the same three levels but defaults to `small_group`, since a prophecy is spoken to others by definition.

### Intercessions

Anyone in the small-group recipient list (or the cohort, for cohort-visible prayers) can log an intercession against a prayer. The intercession is `{peer_id, message, created_at}`. Empty messages are allowed — the act of recording the intercession is itself the witness.

## Prophecy ledger

### Status flow

```
spoken → weighing → confirmed / refined / rejected
                        ↓ (confirmed only)
                    pending → fulfilled / partial / unfulfilled
```

### 2-of-3 weighing rule (1 Cor 14:29)

When a prophecy is submitted, the speaker designates exactly 3 weighers (commonly 2 peers + 1 leader; the speaker cannot weigh their own word). Each weigher casts one judgment: `confirm`, `refine`, or `reject`.

The status resolves as soon as the threshold is hit:

- 2 confirms → `confirmed`
- 2 rejects → `rejected`
- any `refine` after the second judgment → `refined` (signals the word needs reshaping; the speaker can submit a refined version as a new prophecy)

Until two judgments have landed, the prophecy stays in `weighing`.

### Fulfillment tracking

Only **confirmed** prophecies enter fulfillment tracking. Status is one of `pending`, `fulfilled`, `partial`, `unfulfilled`. Non-pending status requires a testimony — the witness of "let none of his words fall to the ground" (1 Sam 3:19) is the whole point.

## Track records

Two views per student:

- **Prayer track record** — total submitted, by-status counts, resolved count, favorable count, and answer rate (`(answered_yes + partial) / resolved`).
- **Prophecy track record** — total spoken, by-status counts, confirmation rate (`confirmed / weighed`), and per-confirmed-prophecy fulfillment breakdown + fulfillment rate.

Cohort-level aggregate (`/api/cohorts/{id}/prayer-rhythm`) is per-student counts only — never content. This is the surface the formation director uses to notice that a student has gone quiet spiritually without invading their interior life.

## Cohort tradition policy

The same data model serves Catholic-contemplative cohorts and charismatic-Pentecostal cohorts. A cohort-level flag (`tradition`, default `catholic`) is stored at `/api/cohorts/{id}/policy` and flips defaults and (eventually) UI copy. The 2-of-3 weighing rule applies regardless of tradition; the tradition flag governs framing, scripture defaults, and the language used around prophecy.

## API quick reference

```
POST   /api/prayer/requests
GET    /api/prayer/requests?student_id=&status=&visible_to=
GET    /api/prayer/requests/{prayer_id}
POST   /api/prayer/requests/{prayer_id}/watch
POST   /api/prayer/requests/{prayer_id}/answer
POST   /api/prayer/requests/{prayer_id}/intercessions

POST   /api/prophecies
GET    /api/prophecies?speaker_id=&addressed_to=&status=&visible_to=
GET    /api/prophecies/{prophecy_id}
POST   /api/prophecies/{prophecy_id}/weighings
POST   /api/prophecies/{prophecy_id}/fulfillment

GET    /api/prayer/track-record/{student_id}
GET    /api/cohorts/{cohort_id}/prayer-rhythm
GET    /api/cohorts/{cohort_id}/policy
PUT    /api/cohorts/{cohort_id}/policy
```

## MCP tools

The prayer/prophecy ledgers are exposed as 11 MCP tools so any agent harness can submit, weigh, mark answered, record fulfillment, and pull track records. Tool names mirror the API: `submit_prayer_request`, `list_prayer_requests`, `mark_prayer_answered`, `add_intercession`, `submit_prophecy`, `weigh_prophecy`, `record_prophecy_fulfillment`, `list_prophecies`, `get_prayer_track_record`, `get_cohort_prayer_rhythm`, `set_cohort_tradition`. See [`AGENTS.md`](AGENTS.md) for wiring.

## Persistence note

The current implementation keeps state in-process (matches the project's pattern; see `vector_memory._store`). Tests must call `prayer.reset()` between cases. Real persistence (SQLAlchemy-backed) is the natural next step — the dataclass shapes in `backend/services/prayer.py` map cleanly onto `MinistryOutcome`-style models.

## Out of scope (future)

- Lectionary integration (daily readings driving the scripture field on prayer entries).
- Risk signal integration (prayer/intercession rhythm as a positive `dropout_risk` factor).
- AI mentor integration (prayer-journal entries as opt-in vector-memory snippets for `chat_with_mentor`).
- Real-time prayer rooms over WebSocket.
- Anonymous prayer mode.
