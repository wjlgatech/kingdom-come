"""The OEC integrity layer, tested against the documented case that motivated it.

Each test replays a situation from the July 2026 Shekinah Worship Center statement
(and the essay built on it) through the stack — including the honest-failure edges.
The names are the point: this suite IS the essay's thought experiment, executable.
"""
from datetime import datetime, timedelta, timezone

import pytest

from backend.services import integrity as itg


@pytest.fixture(autouse=True)
def _fresh():
    itg.reset()
    yield
    itg.reset()


def _iso(days_from_now: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days_from_now)).isoformat()


# ── replay 1: the wedding contradiction — caught instantly, no outcome needed ──

def test_wedding_contradiction_fires_same_day():
    # Privately: "this marriage is not the will of the Lord"
    itg.commit_claim("sp1", "This marriage is not the will of the Lord — wait six months.",
                     subject="marriage:couple-a", stance="against")
    # Wedding day: "an angel is assigned — no one can break this marriage apart"
    itg.commit_claim("sp1", "I see an angel assigned so this marriage will never fall apart.",
                     subject="marriage:couple-a", stance="for")
    found = itg.detect_contradictions("sp1")
    assert len(found) == 1 and found[0]["subject"] == "marriage:couple-a"
    # ...and the gate fails TODAY, decades before any fulfillment horizon.
    gate = itg.platform_gate("sp1")
    assert not gate["pass"]
    assert any("contradiction" in r for r in gate["reasons"])


def test_contradiction_clears_after_public_correction():
    itg.commit_claim("sp1", "against-word", subject="s", stance="against",
                     criterion="the marriage endures a year")
    c2 = itg.commit_claim("sp1", "for-word", subject="s", stance="for",
                          criterion="the marriage endures a year")
    assert itg.detect_contradictions("sp1")
    itg.resolve_claim(c2.id, "failed")
    itg.correct_claim(c2.id, "I spoke beyond what was given; I retract the wedding word.")
    assert itg.detect_contradictions("sp1") == []


# ── replay 2: unfalsifiable words never count as wins ─────────────────────────

def test_unfalsifiable_word_grades_not_measurable_only():
    c = itg.commit_claim("sp2", "A season of breakthrough is coming.")  # no criterion
    with pytest.raises(ValueError):
        itg.resolve_claim(c.id, "fulfilled")
    itg.resolve_claim(c.id, "not_measurable")
    rec = itg.integrity_record("sp2")
    assert rec["by_outcome"] == {"not_measurable": 1}
    # ...and unmeasured evidence can never fail (or pass) the gate on its own.
    assert itg.platform_gate("sp2")["pass"]


# ── replay 3: the timing tell — latency-to-correction is a number ─────────────

def test_latency_to_correction_is_computable():
    c = itg.commit_claim("sp3", "The named public figure is the prophesied one.",
                         public=True, criterion="identification proves out", horizon=_iso(365))
    itg.resolve_claim(c.id, "failed", falsified_at=_iso(-400))  # falsified 400 days ago
    open_report = itg.latency_report("sp3")
    assert open_report[0]["corrected"] is False and open_report[0]["open_days"] > 399
    gate = itg.platform_gate("sp3")  # default policy: 30 days
    assert not gate["pass"] and any("uncorrected" in r for r in gate["reasons"])
    itg.correct_claim(c.id, "public correction, on the record")
    after = itg.latency_report("sp3")[0]
    assert after["corrected"] is True and after["latency_days"] > 399
    assert itg.platform_gate("sp3")["pass"]  # corrected ⇒ the gate reopens


# ── replay 4: endorsement as a living object (the 20-year platform) ───────────

def test_endorsement_expires_and_reverifies():
    itg.endorse("pastor-a", "sp4", expires_at=_iso(365))
    assert itg.verify_endorsement("pastor-a", "sp4")["status"] == "current"
    # a failure appears — the SAME endorsement now reports failing, no new decision needed
    c = itg.commit_claim("sp4", "word", public=True, criterion="x", horizon=_iso(10))
    itg.resolve_claim(c.id, "failed", falsified_at=_iso(-90))
    assert itg.verify_endorsement("pastor-a", "sp4")["status"] == "failing"
    # and it cannot outlive its clock by twenty years
    itg.endorse("pastor-b", "sp5", expires_at=_iso(-1))
    assert itg.verify_endorsement("pastor-b", "sp5")["status"] == "expired"


# ── replay 5: dissent recorded beside the claim (the mother's record) ─────────

def test_dissent_is_logged_beside_the_claim():
    c = itg.commit_claim("sp6", "It is God's will that they marry now.",
                         subject="marriage:couple-b", stance="for")
    itg.add_dissent(c.id, by="mother", note="I do not consent; wait.")
    history = itg.claim_history(c.id)
    kinds = [e["kind"] for e in history]
    assert kinds == ["claim", "dissent"]
    assert itg.integrity_record("sp6")["dissents"] == 1


# ── observability: tamper-evidence and the visible diff ───────────────────────

def test_chain_tamper_is_detected_and_named():
    c = itg.commit_claim("sp7", "original wording", criterion="x")
    itg.resolve_claim(c.id, "failed")
    assert itg.verify_chain()["ok"]
    # the semantic-retreat move: quietly rewrite the past
    itg._state["chain"][0].payload["word"] = "a vision I merely described"
    broken = itg.verify_chain()
    assert broken["ok"] is False and broken["broken_at"] == 0
    # ...and a broken ledger fails the gate for everyone it covers
    assert not itg.platform_gate("sp7")["pass"]


def test_claim_history_is_the_visible_diff():
    c = itg.commit_claim("sp8", "word A", criterion="x")
    itg.resolve_claim(c.id, "failed")
    itg.correct_claim(c.id, "correction")
    kinds = [e["kind"] for e in itg.claim_history(c.id)]
    assert kinds == ["claim", "resolve", "correct"]  # append-only: nothing rewritten


# ── the clean path: a faithful speaker loses nothing ──────────────────────────

def test_gate_passes_a_clean_speaker():
    c = itg.commit_claim("sp9", "measurable word", criterion="event occurs", horizon=_iso(30))
    itg.resolve_claim(c.id, "fulfilled", testimony="it occurred")
    gate = itg.platform_gate("sp9")
    assert gate["pass"] and gate["reasons"] == []


# ── guardrails ────────────────────────────────────────────────────────────────

def test_double_resolution_and_orphan_stance_rejected():
    with pytest.raises(ValueError):
        itg.commit_claim("sp10", "word", stance="for")  # stance without subject
    c = itg.commit_claim("sp10", "word", criterion="x")
    itg.resolve_claim(c.id, "fulfilled")
    with pytest.raises(ValueError):
        itg.resolve_claim(c.id, "failed")
    with pytest.raises(ValueError):
        itg.correct_claim(c.id, "n/a")  # only failed claims carry corrections


# ── API surface: the same stack over HTTP ─────────────────────────────────────

def test_api_roundtrip_gate_and_history():
    from fastapi.testclient import TestClient
    from backend.app import app
    client = TestClient(app)
    r = client.post("/api/integrity/claims", json={
        "speaker_id": "spX", "word": "measurable public word",
        "criterion": "the event occurs", "horizon": _iso(30)})
    assert r.status_code == 200
    cid = r.json()["id"]
    assert client.post(f"/api/integrity/claims/{cid}/resolve",
                       json={"outcome": "failed", "falsified_at": _iso(-60)}).status_code == 200
    gate = client.get("/api/integrity/speakers/spX/gate").json()
    assert gate["pass"] is False and any("uncorrected" in x for x in gate["reasons"])
    assert client.post(f"/api/integrity/claims/{cid}/correct",
                       json={"note": "public correction"}).status_code == 200
    assert client.get("/api/integrity/speakers/spX/gate").json()["pass"] is True
    hist = client.get(f"/api/integrity/claims/{cid}/history").json()["events"]
    assert [e["kind"] for e in hist] == ["claim", "resolve", "correct"]
    assert client.get("/api/integrity/chain/verify").json()["ok"] is True


def test_api_rejects_unmeasurable_win_and_orphan_stance():
    from fastapi.testclient import TestClient
    from backend.app import app
    client = TestClient(app)
    r = client.post("/api/integrity/claims", json={"speaker_id": "spY", "word": "vague word"})
    cid = r.json()["id"]
    assert client.post(f"/api/integrity/claims/{cid}/resolve",
                       json={"outcome": "fulfilled"}).status_code == 422
    assert client.post("/api/integrity/claims",
                       json={"speaker_id": "spY", "word": "w", "stance": "for"}).status_code == 422
