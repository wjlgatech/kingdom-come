"""The OEC integrity layer — Observability, Eval, Control — over public claims.

Born from the essay "We Hold Chatbots to Higher Prophetic Standards Than Prophets"
(agentic-portfolio, 2026-08-02) and the documented 2026 case it studies: a public
prophetic word was quietly re-characterized after it failed, contradictory words by
the same speaker coexisted for years, and the platform consequence arrived two
decades late. Each of those is an infrastructure gap, and this module closes the
three of them the way agentic systems do:

  O — OBSERVABILITY  every event is an APPEND-ONLY, hash-chained commit. Nothing is
      rewritten; a revision is a new event, so semantic retreat becomes a visible
      diff (`claim_history`), and tampering with the past breaks the chain
      (`verify_chain`). Dissent is first-class: an objection is recorded BESIDE the
      claim it contests, so the community sees a contested word as contested.
  E — EVAL  a claim declares its resolution criterion and horizon AT COMMIT TIME
      (Deuteronomy 18:22 is the grader; the ledger just enforces the paperwork).
      Three honest grades: fulfilled / failed / not_measurable — a word that can
      never be false can never be counted true. Two evals resolve without waiting
      for outcomes: structural contradiction (same speaker, same subject, opposite
      stance — the wedding test) and latency-to-correction (the timing tell).
  C — CONTROL  `platform_gate` turns the scorecard into a machine-checkable
      go/no-go (like every other gate in this repo: it can only fail on MEASURED
      evidence — unmeasurable words never pass or fail it), and an endorsement is
      a LIVING object that expires and re-verifies instead of outliving its
      evidence by twenty years.

Honesty notes, stated up front:
- Contradiction detection is STRUCTURAL (explicit subject + stance fields), not
  semantic. No NLP pretends to read theology; what's declared is what's tested.
- This registry complements — does not replace — the pastoral prophecy ledger in
  `prayer.py` (weighing, testimony, visibility). `commit_prophecy` bridges one
  into the chain. Ledgers raise the cost of fraud and collapse the cost of
  discernment; they do not regenerate hearts.
- In-memory with `reset()` like its sibling services; write-through persistence
  (LedgerRecord kind="chain") is a documented follow-up, not silently absent.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Stance = Literal["for", "against"]
Outcome = Literal["fulfilled", "failed", "not_measurable"]

GENESIS = "0" * 64


@dataclass
class ChainEntry:
    seq: int
    kind: str          # claim | resolve | correct | dissent | endorse
    ref_id: str        # the claim (or endorsement) this event belongs to
    payload: dict[str, Any]
    at: str
    prev_hash: str
    hash: str = ""


@dataclass
class Claim:
    id: str
    speaker_id: str
    word: str
    public: bool
    subject: str | None = None      # structural key for contradiction detection
    stance: Stance | None = None    # "for" / "against" the subject
    criterion: str | None = None    # what would count as fulfilled…
    horizon: str | None = None      # …and by when (ISO date)
    created_at: str = ""
    outcome: Outcome | None = None
    resolved_at: str = ""
    falsified_at: str = ""          # when the world settled the question
    corrected_at: str = ""          # when the speaker publicly corrected
    dissents: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GatePolicy:
    """Consequences subscribe to the scorecard. Defaults are deliberately strict."""
    max_open_contradictions: int = 0
    max_uncorrected_days: float = 30.0
    require_chain_ok: bool = True


_state: dict[str, Any] = {"chain": [], "claims": {}, "endorsements": {}, "seq": 0}


def reset() -> None:
    _state["chain"] = []
    _state["claims"] = {}
    _state["endorsements"] = {}
    _state["seq"] = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _entry_hash(seq: int, kind: str, ref_id: str, payload: dict[str, Any], at: str, prev: str) -> str:
    return hashlib.sha256(f"{seq}|{prev}|{kind}|{ref_id}|{_canonical(payload)}|{at}".encode()).hexdigest()


def _record(kind: str, ref_id: str, payload: dict[str, Any], at: str | None = None) -> ChainEntry:
    seq = _state["seq"]
    prev = _state["chain"][-1].hash if _state["chain"] else GENESIS
    stamped = at or _now()
    entry = ChainEntry(seq=seq, kind=kind, ref_id=ref_id, payload=payload, at=stamped, prev_hash=prev)
    entry.hash = _entry_hash(seq, kind, ref_id, payload, stamped, prev)
    _state["chain"].append(entry)
    _state["seq"] = seq + 1
    return entry


# ---------- O · observability ----------

def verify_chain() -> dict[str, Any]:
    """Recompute every link. Tampering with any past event names the break."""
    prev = GENESIS
    for e in _state["chain"]:
        expected = _entry_hash(e.seq, e.kind, e.ref_id, e.payload, e.at, prev)
        if e.hash != expected or e.prev_hash != prev:
            return {"ok": False, "length": len(_state["chain"]), "broken_at": e.seq}
        prev = e.hash
    return {"ok": True, "length": len(_state["chain"]), "broken_at": None}


def claim_history(claim_id: str) -> list[dict[str, Any]]:
    """Every event for a claim, in order — the visible diff a mutable memory denies."""
    return [asdict(e) for e in _state["chain"] if e.ref_id == claim_id]


def add_dissent(claim_id: str, by: str, note: str) -> Claim:
    """An objection recorded BESIDE the claim it contests (the mother's record)."""
    c = _require(claim_id)
    d = {"by": by, "note": note, "at": _now()}
    c.dissents.append(d)
    _record("dissent", claim_id, d)
    return c


# ---------- claims ----------

def commit_claim(
    speaker_id: str,
    word: str,
    *,
    public: bool = True,
    subject: str | None = None,
    stance: Stance | None = None,
    criterion: str | None = None,
    horizon: str | None = None,
) -> Claim:
    if not speaker_id or not word.strip():
        raise ValueError("a claim needs a speaker and a word")
    if stance is not None and subject is None:
        raise ValueError("a stance needs a subject")
    cid = f"clm_{_state['seq']:06d}"
    c = Claim(
        id=cid, speaker_id=speaker_id, word=word.strip(), public=public,
        subject=subject, stance=stance, criterion=criterion, horizon=horizon,
        created_at=_now(),
    )
    _state["claims"][cid] = c
    _record("claim", cid, {
        "speaker_id": speaker_id, "word": c.word, "public": public,
        "subject": subject, "stance": stance, "criterion": criterion, "horizon": horizon,
    })
    return c


def commit_prophecy(prophecy: Any, **kwargs: Any) -> Claim:
    """Bridge a pastoral-ledger prophecy (prayer.Prophecy) into the integrity chain."""
    return commit_claim(prophecy.speaker_id, prophecy.word, **kwargs)


def _require(claim_id: str) -> Claim:
    c = _state["claims"].get(claim_id)
    if c is None:
        raise ValueError(f"unknown claim {claim_id}")
    return c


# ---------- E · eval ----------

def resolve_claim(
    claim_id: str,
    outcome: Outcome,
    *,
    testimony: str = "",
    falsified_at: str | None = None,
) -> Claim:
    """Three honest grades. A claim with no declared criterion can only be
    not_measurable — a word that can never be false can never be counted true."""
    c = _require(claim_id)
    if c.outcome is not None:
        raise ValueError(f"claim {claim_id} already resolved as {c.outcome}")
    if outcome in ("fulfilled", "failed") and not c.criterion:
        raise ValueError(
            "a claim without a declared resolution criterion can only be graded not_measurable"
        )
    c.outcome = outcome
    c.resolved_at = _now()
    if outcome == "failed":
        c.falsified_at = falsified_at or c.resolved_at
    _record("resolve", claim_id, {"outcome": outcome, "testimony": testimony,
                                  "falsified_at": c.falsified_at})
    return c


def correct_claim(claim_id: str, note: str) -> Claim:
    """The public correction — the event whose LATENCY the timing tell measures."""
    c = _require(claim_id)
    if c.outcome != "failed":
        raise ValueError("only a failed claim carries a public correction")
    if c.corrected_at:
        raise ValueError("already corrected")
    c.corrected_at = _now()
    _record("correct", claim_id, {"note": note})
    return c


def detect_contradictions(speaker_id: str) -> list[dict[str, Any]]:
    """The wedding test: same speaker, same subject, opposite stance, neither
    corrected. Resolves the DAY of the second commit — no outcome needed."""
    rows = [c for c in _state["claims"].values()
            if c.speaker_id == speaker_id and c.subject and c.stance and not c.corrected_at]
    by_subject: dict[str, list[Claim]] = {}
    for c in rows:
        by_subject.setdefault(c.subject, []).append(c)
    out = []
    for subject, claims in by_subject.items():
        stances = {c.stance for c in claims}
        if {"for", "against"} <= stances:
            out.append({
                "subject": subject,
                "claim_ids": [c.id for c in claims],
                "detected_from": max(c.created_at for c in claims),
            })
    return out


def _days_between(a: str, b: str) -> float:
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400.0


def latency_report(speaker_id: str, *, now: str | None = None) -> list[dict[str, Any]]:
    """Per failed public claim: falsification → correction gap, or the still-open gap."""
    now_ts = now or _now()
    out = []
    for c in _state["claims"].values():
        if c.speaker_id != speaker_id or c.outcome != "failed" or not c.public:
            continue
        if c.corrected_at:
            out.append({"claim_id": c.id, "corrected": True,
                        "latency_days": round(_days_between(c.falsified_at, c.corrected_at), 3)})
        else:
            out.append({"claim_id": c.id, "corrected": False,
                        "open_days": round(_days_between(c.falsified_at, now_ts), 3)})
    return out


def integrity_record(speaker_id: str, *, now: str | None = None) -> dict[str, Any]:
    """The computed scorecard — from the ledger, never the highlight reel."""
    rows = [c for c in _state["claims"].values() if c.speaker_id == speaker_id]
    outcomes = Counter(c.outcome or "open" for c in rows)
    lat = latency_report(speaker_id, now=now)
    uncorrected = [r for r in lat if not r["corrected"]]
    return {
        "speaker_id": speaker_id,
        "total_claims": len(rows),
        "by_outcome": dict(outcomes),
        "measurable": sum(1 for c in rows if c.criterion),
        "open_contradictions": detect_contradictions(speaker_id),
        "failed_public_uncorrected": len(uncorrected),
        "worst_open_correction_days": max((r["open_days"] for r in uncorrected), default=0.0),
        "dissents": sum(len(c.dissents) for c in rows),
        "chain": verify_chain(),
    }


# ---------- C · control ----------

def platform_gate(speaker_id: str, policy: GatePolicy | None = None,
                  *, now: str | None = None) -> dict[str, Any]:
    """Go/no-go computed from measured evidence only. A clean speaker passes; a
    broken chain, an open contradiction, or a stale uncorrected public failure
    fails — and each failure names itself."""
    pol = policy or GatePolicy()
    rec = integrity_record(speaker_id, now=now)
    reasons: list[str] = []
    if pol.require_chain_ok and not rec["chain"]["ok"]:
        reasons.append(f"ledger integrity broken at seq {rec['chain']['broken_at']}")
    if len(rec["open_contradictions"]) > pol.max_open_contradictions:
        subjects = ", ".join(x["subject"] for x in rec["open_contradictions"])
        reasons.append(f"open contradiction(s) on: {subjects}")
    if rec["worst_open_correction_days"] > pol.max_uncorrected_days:
        reasons.append(
            f"failed public word uncorrected for "
            f"{rec['worst_open_correction_days']:.0f} days (policy: {pol.max_uncorrected_days:.0f})"
        )
    return {"pass": not reasons, "reasons": reasons, "record": rec}


def endorse(endorser_id: str, speaker_id: str, *, expires_at: str) -> dict[str, Any]:
    """An endorsement is a living object: it expires, and it re-verifies."""
    eid = f"end_{endorser_id}:{speaker_id}"
    e = {"id": eid, "endorser_id": endorser_id, "speaker_id": speaker_id,
         "expires_at": expires_at, "created_at": _now()}
    _state["endorsements"][eid] = e
    _record("endorse", eid, e)
    return e


def verify_endorsement(endorser_id: str, speaker_id: str,
                       policy: GatePolicy | None = None, *, now: str | None = None) -> dict[str, Any]:
    e = _state["endorsements"].get(f"end_{endorser_id}:{speaker_id}")
    if e is None:
        return {"status": "absent"}
    now_ts = now or _now()
    if now_ts >= e["expires_at"]:
        return {"status": "expired", "expired_at": e["expires_at"]}
    gate = platform_gate(speaker_id, policy, now=now)
    return {"status": "current" if gate["pass"] else "failing", "gate": gate}
