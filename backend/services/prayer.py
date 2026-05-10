"""Prayer + prophecy track-record service.

Two parallel ledgers with longitudinal track records:

- **Prayer ledger.** Petitions submitted by a student, optionally tied to a
  scripture reference, with a visibility policy. Each prayer can be marked
  answered with a structured status (`answered_yes` / `partial` / `no` /
  `superseded`) and a free-text testimony. Small-group peers can record
  intercessions ("I'm praying for you" + optional encouragement).

- **Prophecy ledger.** Prophetic words spoken by a student, addressed to a
  recipient (self / person / group), weighed by 2-of-3 designated weighers
  (peer + peer + leader; 1 Cor 14:29). Once weighed, a prophecy moves to
  `confirmed` / `refined` / `rejected`. Confirmed prophecies enter
  fulfillment tracking and resolve to `fulfilled` / `partial` / `unfulfilled`
  with a testimony.

State is in-process (matches the project convention; see
`vector_memory._store`). Tests must call `prayer.reset()` between cases.

Cohort-level policy (`tradition`, `validation_rule`) lives here too — same
data model serves Catholic-contemplative and charismatic-Pentecostal
cohorts; a flag flips defaults and copy.
"""
from __future__ import annotations

import uuid
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal


PrayerStatus = Literal["open", "watching", "answered_yes", "partial", "no", "superseded"]
ANSWER_STATUSES: set[str] = {"answered_yes", "partial", "no", "superseded"}
RESOLVED_FAVORABLE: set[str] = {"answered_yes", "partial"}

ProphecyStatus = Literal["spoken", "weighing", "confirmed", "refined", "rejected"]
WeighJudgment = Literal["confirm", "refine", "reject"]
FulfillmentStatus = Literal["pending", "fulfilled", "partial", "unfulfilled"]

Visibility = Literal["private", "small_group", "cohort"]
Tradition = Literal["catholic", "charismatic"]


@dataclass
class PrayerRequest:
    id: str
    student_id: str
    petition: str
    visibility: Visibility
    recipient_ids: list[str]
    scripture: str | None
    status: PrayerStatus
    created_at: str
    answer: dict[str, Any] | None = None  # set by mark_answered


@dataclass
class Intercession:
    prayer_id: str
    peer_id: str
    message: str
    created_at: str


@dataclass
class Prophecy:
    id: str
    speaker_id: str
    addressed_to: str
    word: str
    weigher_ids: list[str]
    visibility: Visibility
    status: ProphecyStatus
    created_at: str
    weighings: list[dict[str, Any]] = field(default_factory=list)
    fulfillment: dict[str, Any] | None = None


@dataclass
class CohortPolicy:
    cohort_id: str
    tradition: Tradition = "catholic"


_DEFAULT_TRADITION: Tradition = "catholic"

_state: dict[str, Any] = {
    "prayers": {},          # id -> PrayerRequest
    "intercessions": [],    # list[Intercession]
    "prophecies": {},       # id -> Prophecy
    "policies": {},         # cohort_id -> CohortPolicy
}


def reset() -> None:
    _state["prayers"].clear()
    _state["intercessions"].clear()
    _state["prophecies"].clear()
    _state["policies"].clear()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ---------- cohort policy ----------

def get_policy(cohort_id: str) -> CohortPolicy:
    if cohort_id not in _state["policies"]:
        _state["policies"][cohort_id] = CohortPolicy(cohort_id=cohort_id, tradition=_DEFAULT_TRADITION)
    return _state["policies"][cohort_id]


def set_policy(cohort_id: str, tradition: Tradition) -> CohortPolicy:
    if tradition not in ("catholic", "charismatic"):
        raise ValueError(f"unknown tradition: {tradition}")
    policy = CohortPolicy(cohort_id=cohort_id, tradition=tradition)
    _state["policies"][cohort_id] = policy
    return policy


# ---------- prayer ledger ----------

def submit_prayer(
    *,
    student_id: str,
    petition: str,
    visibility: Visibility = "small_group",
    recipient_ids: list[str] | None = None,
    scripture: str | None = None,
) -> PrayerRequest:
    if not petition or not petition.strip():
        raise ValueError("petition must not be empty")
    if visibility not in ("private", "small_group", "cohort"):
        raise ValueError(f"unknown visibility: {visibility}")
    if visibility == "small_group" and not recipient_ids:
        raise ValueError("small_group visibility requires recipient_ids")
    pr = PrayerRequest(
        id=_uid("pr"),
        student_id=student_id,
        petition=petition.strip(),
        visibility=visibility,
        recipient_ids=list(recipient_ids or []),
        scripture=scripture,
        status="open",
        created_at=_now(),
    )
    _state["prayers"][pr.id] = pr
    return pr


def watch_prayer(prayer_id: str) -> PrayerRequest:
    pr = _require_prayer(prayer_id)
    if pr.status in ANSWER_STATUSES:
        raise ValueError(f"prayer {prayer_id} is already resolved as {pr.status}")
    pr.status = "watching"
    return pr


def mark_answered(
    prayer_id: str,
    *,
    status: PrayerStatus,
    testimony: str,
    witnesses: list[str] | None = None,
) -> PrayerRequest:
    if status not in ANSWER_STATUSES:
        raise ValueError(f"answer status must be one of {ANSWER_STATUSES}, got {status}")
    if not testimony or not testimony.strip():
        raise ValueError("testimony must not be empty")
    pr = _require_prayer(prayer_id)
    pr.status = status
    pr.answer = {
        "status": status,
        "testimony": testimony.strip(),
        "witnesses": list(witnesses or []),
        "answered_at": _now(),
    }
    return pr


def add_intercession(prayer_id: str, peer_id: str, message: str = "") -> Intercession:
    _require_prayer(prayer_id)
    intercession = Intercession(
        prayer_id=prayer_id,
        peer_id=peer_id,
        message=(message or "").strip(),
        created_at=_now(),
    )
    _state["intercessions"].append(intercession)
    return intercession


def list_prayers(
    *,
    student_id: str | None = None,
    status: PrayerStatus | None = None,
    visible_to: str | None = None,
) -> list[PrayerRequest]:
    """List prayer requests. `visible_to` enforces the visibility policy:
    a viewer sees their own prayers, prayers where they're in `recipient_ids`,
    and (for cohort visibility) any prayer in their cohort. Pass None to skip
    the filter (admin / director-aggregate use)."""
    rows = list(_state["prayers"].values())
    if student_id is not None:
        rows = [p for p in rows if p.student_id == student_id]
    if status is not None:
        rows = [p for p in rows if p.status == status]
    if visible_to is not None:
        rows = [p for p in rows if _visible_to(p, visible_to)]
    rows.sort(key=lambda p: p.created_at, reverse=True)
    return rows


def list_intercessions(prayer_id: str) -> list[Intercession]:
    return [i for i in _state["intercessions"] if i.prayer_id == prayer_id]


def get_prayer(prayer_id: str) -> PrayerRequest:
    return _require_prayer(prayer_id)


# ---------- prophecy ledger ----------

def submit_prophecy(
    *,
    speaker_id: str,
    addressed_to: str,
    word: str,
    weigher_ids: list[str],
    visibility: Visibility = "small_group",
) -> Prophecy:
    if not word or not word.strip():
        raise ValueError("word must not be empty")
    if not addressed_to:
        raise ValueError("addressed_to is required")
    weigher_ids = [w for w in weigher_ids if w]
    if len(set(weigher_ids)) < 3:
        raise ValueError("weigher_ids must list 3 distinct weighers (2 peers + 1 leader)")
    if speaker_id in weigher_ids:
        raise ValueError("the speaker cannot weigh their own prophecy")
    p = Prophecy(
        id=_uid("ph"),
        speaker_id=speaker_id,
        addressed_to=addressed_to,
        word=word.strip(),
        weigher_ids=list(weigher_ids),
        visibility=visibility,
        status="spoken",
        created_at=_now(),
    )
    _state["prophecies"][p.id] = p
    return p


def weigh_prophecy(
    prophecy_id: str,
    *,
    weigher_id: str,
    judgment: WeighJudgment,
    notes: str = "",
) -> Prophecy:
    if judgment not in ("confirm", "refine", "reject"):
        raise ValueError(f"unknown judgment: {judgment}")
    p = _require_prophecy(prophecy_id)
    if weigher_id not in p.weigher_ids:
        raise ValueError(f"weigher {weigher_id} is not on the council for {prophecy_id}")
    if any(w["weigher_id"] == weigher_id for w in p.weighings):
        raise ValueError(f"weigher {weigher_id} has already weighed {prophecy_id}")
    p.weighings.append({
        "weigher_id": weigher_id,
        "judgment": judgment,
        "notes": (notes or "").strip(),
        "weighed_at": _now(),
    })
    if p.status == "spoken":
        p.status = "weighing"
    p.status = _resolve_prophecy_status(p)
    return p


def record_fulfillment(
    prophecy_id: str,
    *,
    status: FulfillmentStatus,
    testimony: str,
    witnesses: list[str] | None = None,
) -> Prophecy:
    if status not in ("pending", "fulfilled", "partial", "unfulfilled"):
        raise ValueError(f"unknown fulfillment status: {status}")
    if status != "pending" and not (testimony or "").strip():
        raise ValueError("testimony must not be empty for non-pending fulfillment")
    p = _require_prophecy(prophecy_id)
    if p.status != "confirmed":
        raise ValueError(
            f"only confirmed prophecies can record fulfillment; {prophecy_id} is {p.status}"
        )
    p.fulfillment = {
        "status": status,
        "testimony": (testimony or "").strip(),
        "witnesses": list(witnesses or []),
        "recorded_at": _now(),
    }
    return p


def list_prophecies(
    *,
    speaker_id: str | None = None,
    status: ProphecyStatus | None = None,
    addressed_to: str | None = None,
    visible_to: str | None = None,
) -> list[Prophecy]:
    rows = list(_state["prophecies"].values())
    if speaker_id is not None:
        rows = [p for p in rows if p.speaker_id == speaker_id]
    if addressed_to is not None:
        rows = [p for p in rows if p.addressed_to == addressed_to]
    if status is not None:
        rows = [p for p in rows if p.status == status]
    if visible_to is not None:
        rows = [p for p in rows if _prophecy_visible_to(p, visible_to)]
    rows.sort(key=lambda p: p.created_at, reverse=True)
    return rows


def get_prophecy(prophecy_id: str) -> Prophecy:
    return _require_prophecy(prophecy_id)


# ---------- track records ----------

def prayer_track_record(student_id: str) -> dict[str, Any]:
    rows = [p for p in _state["prayers"].values() if p.student_id == student_id]
    counts = Counter(p.status for p in rows)
    resolved = sum(counts[s] for s in ANSWER_STATUSES)
    favorable = sum(counts[s] for s in RESOLVED_FAVORABLE)
    answer_rate = (favorable / resolved) if resolved else None
    return {
        "student_id": student_id,
        "total": len(rows),
        "by_status": {s: counts.get(s, 0) for s in ("open", "watching", *ANSWER_STATUSES)},
        "resolved": resolved,
        "answered_favorable": favorable,
        "answer_rate": answer_rate,
    }


def prophecy_track_record(speaker_id: str) -> dict[str, Any]:
    rows = [p for p in _state["prophecies"].values() if p.speaker_id == speaker_id]
    by_status = Counter(p.status for p in rows)
    confirmed = [p for p in rows if p.status == "confirmed"]
    fulfillment_counts = Counter(
        (p.fulfillment or {}).get("status", "pending") for p in confirmed
    )
    weighed = sum(by_status[s] for s in ("confirmed", "refined", "rejected"))
    confirmation_rate = (by_status["confirmed"] / weighed) if weighed else None
    fulfilled = fulfillment_counts.get("fulfilled", 0) + fulfillment_counts.get("partial", 0)
    fulfillment_resolved = sum(
        fulfillment_counts.get(s, 0) for s in ("fulfilled", "partial", "unfulfilled")
    )
    fulfillment_rate = (fulfilled / fulfillment_resolved) if fulfillment_resolved else None
    return {
        "speaker_id": speaker_id,
        "total_spoken": len(rows),
        "by_status": dict(by_status),
        "confirmation_rate": confirmation_rate,
        "fulfillment": {
            "confirmed_count": len(confirmed),
            "by_fulfillment_status": dict(fulfillment_counts),
            "fulfillment_rate": fulfillment_rate,
        },
    }


def cohort_rhythm(student_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Director-facing aggregate. Counts only — no content. Each row is a
    student's submission/answer/weighing rhythm."""
    out: list[dict[str, Any]] = []
    sids = list(student_ids)
    for sid in sids:
        prayers = [p for p in _state["prayers"].values() if p.student_id == sid]
        prophecies = [p for p in _state["prophecies"].values() if p.speaker_id == sid]
        weighings_done = sum(
            1 for p in _state["prophecies"].values()
            for w in p.weighings if w["weigher_id"] == sid
        )
        intercessions_offered = sum(1 for i in _state["intercessions"] if i.peer_id == sid)
        out.append({
            "student_id": sid,
            "prayers_submitted": len(prayers),
            "prayers_answered": sum(1 for p in prayers if p.status in ANSWER_STATUSES),
            "prophecies_spoken": len(prophecies),
            "weighings_done": weighings_done,
            "intercessions_offered": intercessions_offered,
        })
    return out


# ---------- helpers ----------

def _require_prayer(prayer_id: str) -> PrayerRequest:
    if prayer_id not in _state["prayers"]:
        raise KeyError(f"prayer {prayer_id} not found")
    return _state["prayers"][prayer_id]


def _require_prophecy(prophecy_id: str) -> Prophecy:
    if prophecy_id not in _state["prophecies"]:
        raise KeyError(f"prophecy {prophecy_id} not found")
    return _state["prophecies"][prophecy_id]


def _visible_to(p: PrayerRequest, viewer_id: str) -> bool:
    if p.student_id == viewer_id:
        return True
    if p.visibility == "private":
        return False
    if p.visibility == "small_group":
        return viewer_id in p.recipient_ids
    return True  # cohort visibility — any viewer in the cohort can see


def _prophecy_visible_to(p: Prophecy, viewer_id: str) -> bool:
    if p.speaker_id == viewer_id:
        return True
    if viewer_id in p.weigher_ids or viewer_id == p.addressed_to:
        return True
    if p.visibility == "private":
        return False
    if p.visibility == "small_group":
        return False  # only speaker / weighers / recipient
    return True  # cohort


def _resolve_prophecy_status(p: Prophecy) -> ProphecyStatus:
    """2-of-3 rule. Once two judgments agree on confirm OR reject, the status
    locks. A single `refine` judgment moves the status to `refined` regardless,
    since refinement signals the word needs reshaping; the speaker can then
    submit a refined version as a new prophecy."""
    judgments = [w["judgment"] for w in p.weighings]
    if not judgments:
        return p.status
    confirms = sum(1 for j in judgments if j == "confirm")
    rejects = sum(1 for j in judgments if j == "reject")
    refines = sum(1 for j in judgments if j == "refine")
    if rejects >= 2:
        return "rejected"
    if confirms >= 2:
        return "confirmed"
    if refines >= 1 and len(judgments) >= 2:
        return "refined"
    return "weighing"


# ---------- serialization ----------

def to_dict(obj: Any) -> dict[str, Any]:
    """Convert dataclass instances to plain dicts (deep)."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: deepcopy(getattr(obj, k)) for k in obj.__dataclass_fields__}
    return deepcopy(obj)
