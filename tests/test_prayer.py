"""Tests for the prayer + prophecy track-record service.

These cover both the service layer (`backend.services.prayer`) and the
HTTP API surface. Process-global ledger state means each test must call
`prayer.reset()` between runs — the `isolated_state` fixture handles it.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import prayer


@pytest.fixture(autouse=True)
def isolated_state():
    prayer.reset()
    yield
    prayer.reset()


client = TestClient(app)


# ---------- service: prayer ledger ----------

def test_submit_prayer_creates_open_request_with_id_and_timestamp():
    pr = prayer.submit_prayer(
        student_id="stu-marcus-r",
        petition="Wisdom about Mission Theology essay",
        recipient_ids=["stu-luca-b", "stu-grace-w"],
    )
    assert pr.id.startswith("pr-")
    assert pr.status == "open"
    assert pr.created_at  # ISO timestamp
    assert pr.recipient_ids == ["stu-luca-b", "stu-grace-w"]


def test_submit_prayer_rejects_empty_petition():
    with pytest.raises(ValueError, match="petition"):
        prayer.submit_prayer(student_id="stu-x", petition="   ", recipient_ids=["stu-y"])


def test_small_group_visibility_requires_recipients():
    with pytest.raises(ValueError, match="recipient_ids"):
        prayer.submit_prayer(
            student_id="stu-x", petition="...", visibility="small_group", recipient_ids=[]
        )


def test_mark_answered_records_structured_status_and_testimony():
    pr = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="Wisdom for finals", recipient_ids=["stu-luca-b"]
    )
    answered = prayer.mark_answered(
        pr.id,
        status="answered_yes",
        testimony="Got an A and the prof affirmed the angle.",
        witnesses=["stu-luca-b"],
    )
    assert answered.status == "answered_yes"
    assert answered.answer["testimony"].startswith("Got an A")
    assert answered.answer["witnesses"] == ["stu-luca-b"]


def test_mark_answered_rejects_unknown_status():
    pr = prayer.submit_prayer(
        student_id="stu-x", petition="...", recipient_ids=["stu-y"]
    )
    with pytest.raises(ValueError, match="answer status"):
        prayer.mark_answered(pr.id, status="kinda?", testimony="vague")


def test_mark_answered_rejects_empty_testimony():
    pr = prayer.submit_prayer(
        student_id="stu-x", petition="...", recipient_ids=["stu-y"]
    )
    with pytest.raises(ValueError, match="testimony"):
        prayer.mark_answered(pr.id, status="answered_yes", testimony="")


def test_intercessions_attach_to_prayer():
    pr = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", recipient_ids=["stu-luca-b"]
    )
    prayer.add_intercession(pr.id, "stu-luca-b", "Praying for you, brother.")
    prayer.add_intercession(pr.id, "stu-grace-w", "")
    rows = prayer.list_intercessions(pr.id)
    assert len(rows) == 2
    assert {r.peer_id for r in rows} == {"stu-luca-b", "stu-grace-w"}


def test_visibility_filter_hides_private_prayers_from_outsiders():
    private_pr = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", visibility="private", recipient_ids=[]
    )
    shared_pr = prayer.submit_prayer(
        student_id="stu-marcus-r",
        petition="...",
        visibility="small_group",
        recipient_ids=["stu-luca-b"],
    )
    cohort_pr = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", visibility="cohort", recipient_ids=[]
    )

    # Marcus sees all three (his own).
    assert {p.id for p in prayer.list_prayers(visible_to="stu-marcus-r")} == {
        private_pr.id, shared_pr.id, cohort_pr.id
    }
    # Luca sees the small-group one (he's a recipient) and the cohort one.
    assert {p.id for p in prayer.list_prayers(visible_to="stu-luca-b")} == {
        shared_pr.id, cohort_pr.id
    }
    # Outsider sees only the cohort one.
    assert {p.id for p in prayer.list_prayers(visible_to="stu-outsider")} == {
        cohort_pr.id
    }


# ---------- service: prophecy ledger ----------

def _submit_prophecy(speaker="stu-marcus-r"):
    return prayer.submit_prophecy(
        speaker_id=speaker,
        addressed_to="stu-anna-t",
        word="A season of unexpected leadership.",
        weigher_ids=["stu-luca-b", "stu-grace-w", "fd-theresa"],
    )


def test_submit_prophecy_requires_three_distinct_weighers():
    with pytest.raises(ValueError, match="3 distinct"):
        prayer.submit_prophecy(
            speaker_id="stu-x",
            addressed_to="stu-y",
            word="word",
            weigher_ids=["stu-a", "stu-a", "stu-b"],
        )


def test_speaker_cannot_weigh_their_own_prophecy():
    with pytest.raises(ValueError, match="cannot weigh"):
        prayer.submit_prophecy(
            speaker_id="stu-marcus-r",
            addressed_to="stu-y",
            word="word",
            weigher_ids=["stu-marcus-r", "stu-a", "stu-b"],
        )


def test_two_confirms_lock_prophecy_to_confirmed():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    p = prayer.weigh_prophecy(p.id, weigher_id="fd-theresa", judgment="confirm")
    assert p.status == "confirmed"


def test_two_rejects_lock_prophecy_to_rejected():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="reject")
    p = prayer.weigh_prophecy(p.id, weigher_id="fd-theresa", judgment="reject")
    assert p.status == "rejected"


def test_one_confirm_one_reject_with_a_refine_resolves_to_refined():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    p = prayer.weigh_prophecy(p.id, weigher_id="stu-grace-w", judgment="refine")
    assert p.status == "refined"


def test_single_judgment_keeps_prophecy_in_weighing():
    p = _submit_prophecy()
    p = prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    assert p.status == "weighing"


def test_weigher_outside_council_is_rejected():
    p = _submit_prophecy()
    with pytest.raises(ValueError, match="not on the council"):
        prayer.weigh_prophecy(p.id, weigher_id="stu-outsider", judgment="confirm")


def test_weigher_cannot_weigh_twice():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    with pytest.raises(ValueError, match="already weighed"):
        prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="reject")


def test_fulfillment_only_recordable_after_confirmation():
    p = _submit_prophecy()
    with pytest.raises(ValueError, match="only confirmed"):
        prayer.record_fulfillment(p.id, status="fulfilled", testimony="It happened")


def test_fulfillment_requires_testimony_for_non_pending():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    prayer.weigh_prophecy(p.id, weigher_id="fd-theresa", judgment="confirm")
    with pytest.raises(ValueError, match="testimony"):
        prayer.record_fulfillment(p.id, status="fulfilled", testimony="  ")


def test_full_prophecy_lifecycle_records_fulfillment():
    p = _submit_prophecy()
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    p = prayer.weigh_prophecy(p.id, weigher_id="fd-theresa", judgment="confirm")
    p = prayer.record_fulfillment(
        p.id,
        status="fulfilled",
        testimony="Anna was elected to the parish council in November.",
        witnesses=["fd-theresa"],
    )
    assert p.fulfillment["status"] == "fulfilled"
    assert "council" in p.fulfillment["testimony"]


# ---------- service: track records ----------

def test_prayer_track_record_computes_answer_rate():
    for _ in range(3):
        pr = prayer.submit_prayer(
            student_id="stu-marcus-r", petition="...", recipient_ids=["stu-luca-b"]
        )
        prayer.mark_answered(pr.id, status="answered_yes", testimony="yes")
    pr_no = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", recipient_ids=["stu-luca-b"]
    )
    prayer.mark_answered(pr_no.id, status="no", testimony="not this time")
    prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", recipient_ids=["stu-luca-b"]
    )  # remains open

    rec = prayer.prayer_track_record("stu-marcus-r")
    assert rec["total"] == 5
    assert rec["resolved"] == 4
    assert rec["answered_favorable"] == 3
    assert rec["answer_rate"] == 0.75
    assert rec["by_status"]["open"] == 1
    assert rec["by_status"]["answered_yes"] == 3
    assert rec["by_status"]["no"] == 1


def test_prophecy_track_record_computes_confirmation_and_fulfillment_rates():
    # Two confirmed (one fulfilled, one unfulfilled); one rejected.
    p1 = _submit_prophecy()
    prayer.weigh_prophecy(p1.id, weigher_id="stu-luca-b", judgment="confirm")
    prayer.weigh_prophecy(p1.id, weigher_id="fd-theresa", judgment="confirm")
    prayer.record_fulfillment(p1.id, status="fulfilled", testimony="happened")

    p2 = _submit_prophecy()
    prayer.weigh_prophecy(p2.id, weigher_id="stu-luca-b", judgment="confirm")
    prayer.weigh_prophecy(p2.id, weigher_id="fd-theresa", judgment="confirm")
    prayer.record_fulfillment(p2.id, status="unfulfilled", testimony="time passed")

    p3 = _submit_prophecy()
    prayer.weigh_prophecy(p3.id, weigher_id="stu-luca-b", judgment="reject")
    prayer.weigh_prophecy(p3.id, weigher_id="fd-theresa", judgment="reject")

    rec = prayer.prophecy_track_record("stu-marcus-r")
    assert rec["total_spoken"] == 3
    assert rec["by_status"]["confirmed"] == 2
    assert rec["by_status"]["rejected"] == 1
    # 2 confirmed of 3 weighed = 0.667
    assert round(rec["confirmation_rate"], 2) == 0.67
    # 1 fulfilled of 2 resolved confirmed = 0.5
    assert rec["fulfillment"]["fulfillment_rate"] == 0.5


def test_cohort_rhythm_counts_per_student_no_content():
    pr = prayer.submit_prayer(
        student_id="stu-marcus-r", petition="...", recipient_ids=["stu-luca-b"]
    )
    prayer.mark_answered(pr.id, status="answered_yes", testimony="yes")
    p = _submit_prophecy(speaker="stu-marcus-r")
    prayer.weigh_prophecy(p.id, weigher_id="stu-luca-b", judgment="confirm")
    prayer.add_intercession(pr.id, "stu-grace-w", "praying")

    rhythm = prayer.cohort_rhythm(["stu-marcus-r", "stu-luca-b", "stu-grace-w"])
    by_id = {r["student_id"]: r for r in rhythm}
    assert by_id["stu-marcus-r"]["prayers_submitted"] == 1
    assert by_id["stu-marcus-r"]["prayers_answered"] == 1
    assert by_id["stu-marcus-r"]["prophecies_spoken"] == 1
    assert by_id["stu-luca-b"]["weighings_done"] == 1
    assert by_id["stu-grace-w"]["intercessions_offered"] == 1
    # Crucially, no petition/word/testimony content is exposed.
    for row in rhythm:
        for forbidden in ("petition", "word", "testimony"):
            assert forbidden not in row


# ---------- cohort policy ----------

def test_default_policy_is_catholic():
    p = prayer.get_policy("any-cohort")
    assert p.tradition == "catholic"


def test_set_policy_flips_tradition():
    prayer.set_policy("st-aloysius-s26", "charismatic")
    assert prayer.get_policy("st-aloysius-s26").tradition == "charismatic"


def test_set_policy_rejects_unknown_tradition():
    with pytest.raises(ValueError):
        prayer.set_policy("c", "buddhist")


# ---------- HTTP API ----------

def test_post_prayer_request_returns_201_shape_via_api():
    response = client.post(
        "/api/prayer/requests",
        json={
            "student_id": "stu-marcus-r",
            "petition": "Wisdom for the Mission Theology essay.",
            "recipient_ids": ["stu-luca-b", "stu-grace-w"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"].startswith("pr-")
    assert body["status"] == "open"


def test_full_api_flow_submits_answers_and_lists():
    submit = client.post(
        "/api/prayer/requests",
        json={
            "student_id": "stu-marcus-r",
            "petition": "Wisdom for finals.",
            "recipient_ids": ["stu-luca-b"],
        },
    )
    pid = submit.json()["id"]

    intercession = client.post(
        f"/api/prayer/requests/{pid}/intercessions",
        json={"peer_id": "stu-luca-b", "message": "Praying for you, brother."},
    )
    assert intercession.status_code == 200

    answered = client.post(
        f"/api/prayer/requests/{pid}/answer",
        json={"status": "answered_yes", "testimony": "Got an A.", "witnesses": ["stu-luca-b"]},
    )
    assert answered.status_code == 200
    assert answered.json()["status"] == "answered_yes"

    detail = client.get(f"/api/prayer/requests/{pid}")
    assert detail.status_code == 200
    assert len(detail.json()["intercessions"]) == 1


def test_api_rejects_invalid_answer_status():
    submit = client.post(
        "/api/prayer/requests",
        json={
            "student_id": "stu-marcus-r",
            "petition": "...",
            "recipient_ids": ["stu-luca-b"],
        },
    )
    pid = submit.json()["id"]
    bad = client.post(
        f"/api/prayer/requests/{pid}/answer",
        json={"status": "kinda", "testimony": "..."},
    )
    assert bad.status_code == 422


def test_api_full_prophecy_flow_to_confirmed_and_fulfilled():
    submit = client.post(
        "/api/prophecies",
        json={
            "speaker_id": "stu-marcus-r",
            "addressed_to": "stu-anna-t",
            "word": "A season of unexpected leadership.",
            "weigher_ids": ["stu-luca-b", "stu-grace-w", "fd-theresa"],
        },
    )
    assert submit.status_code == 200
    phid = submit.json()["id"]

    for weigher in ("stu-luca-b", "fd-theresa"):
        r = client.post(
            f"/api/prophecies/{phid}/weighings",
            json={"weigher_id": weigher, "judgment": "confirm"},
        )
        assert r.status_code == 200

    confirmed = client.get(f"/api/prophecies/{phid}").json()
    assert confirmed["status"] == "confirmed"

    fulfill = client.post(
        f"/api/prophecies/{phid}/fulfillment",
        json={"status": "fulfilled", "testimony": "She was elected to the parish council."},
    )
    assert fulfill.status_code == 200
    assert fulfill.json()["fulfillment"]["status"] == "fulfilled"


def test_track_record_endpoint_returns_both_ledgers():
    submit = client.post(
        "/api/prayer/requests",
        json={
            "student_id": "stu-marcus-r",
            "petition": "...",
            "recipient_ids": ["stu-luca-b"],
        },
    )
    pid = submit.json()["id"]
    client.post(
        f"/api/prayer/requests/{pid}/answer",
        json={"status": "answered_yes", "testimony": "yes"},
    )

    response = client.get("/api/prayer/track-record/stu-marcus-r")
    assert response.status_code == 200
    body = response.json()
    assert body["prayer"]["total"] == 1
    assert body["prayer"]["answer_rate"] == 1.0
    assert body["prophecy"]["total_spoken"] == 0


def test_cohort_prayer_rhythm_endpoint_includes_real_cohort_students():
    # No content yet — but the cohort fixture has 24 students.
    response = client.get("/api/cohorts/st-aloysius-s26/prayer-rhythm")
    assert response.status_code == 200
    body = response.json()
    assert body["cohort_id"] == "st-aloysius-s26"
    assert len(body["rhythm"]) == 24
    assert all(row["prayers_submitted"] == 0 for row in body["rhythm"])


def test_cohort_prayer_rhythm_unknown_cohort_returns_404():
    response = client.get("/api/cohorts/bogus/prayer-rhythm")
    assert response.status_code == 404


def test_cohort_policy_get_and_put():
    get_default = client.get("/api/cohorts/st-aloysius-s26/policy")
    assert get_default.status_code == 200
    assert get_default.json()["tradition"] == "catholic"

    put = client.put(
        "/api/cohorts/st-aloysius-s26/policy",
        json={"tradition": "charismatic"},
    )
    assert put.status_code == 200
    assert put.json()["tradition"] == "charismatic"

    follow_up = client.get("/api/cohorts/st-aloysius-s26/policy")
    assert follow_up.json()["tradition"] == "charismatic"


def test_cohort_policy_rejects_unknown_tradition():
    bad = client.put(
        "/api/cohorts/st-aloysius-s26/policy",
        json={"tradition": "buddhist"},
    )
    assert bad.status_code == 422
