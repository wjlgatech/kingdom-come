"""Write-through persistence for the prayer + prophecy ledgers (B1).

The in-process dicts stay the read path; these tests cover the durability
seam: every mutation upserts a JSON row, enable_persistence() replays rows
into _state (a simulated restart), and reset() clears both stores. Uses a
per-test sqlite file via an injected sessionmaker so the app engine and the
in-memory-only default other tests rely on are untouched.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.connection import Base
from backend.models.ledger import LedgerRecord
from backend.services import prayer


@pytest.fixture()
def persisted_prayer(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path/'ledger.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    prayer.reset()
    prayer.enable_persistence(factory)
    yield factory
    prayer.disable_persistence()
    prayer.reset()


def _simulate_restart(factory) -> None:
    """New process: empty in-memory state, then replay from the DB."""
    prayer.disable_persistence()
    prayer.reset()
    prayer.enable_persistence(factory)


def test_mutations_write_rows(persisted_prayer):
    pr = prayer.submit_prayer(student_id="stu-a", petition="Wisdom for the essay.")
    prayer.add_intercession(pr.id, "stu-b", "With you.")
    ph = prayer.submit_prophecy(
        speaker_id="stu-a",
        addressed_to="stu-b",
        word="A season of speaking is opening.",
        weigher_ids=["stu-c", "stu-d", "fd-x"],
    )
    prayer.set_policy("cohort-1", "charismatic")

    with persisted_prayer() as session:
        kinds = {r.kind for r in session.query(LedgerRecord).all()}
        count = session.query(LedgerRecord).count()
    assert kinds == {"prayer", "intercession", "prophecy", "policy"}
    assert count == 4
    assert ph.id in prayer._state["prophecies"]


def test_state_survives_restart(persisted_prayer):
    pr = prayer.submit_prayer(
        student_id="stu-a",
        petition="Courage for morning prayer.",
        visibility="small_group",
        recipient_ids=["stu-b"],
        scripture="Joshua 1:9",
    )
    prayer.add_intercession(pr.id, "stu-b", "Praying at lauds.")
    prayer.mark_answered(pr.id, status="answered_yes", testimony="Led it twice.")
    ph = prayer.submit_prophecy(
        speaker_id="stu-b",
        addressed_to="stu-a",
        word="The lectern will not frighten you.",
        weigher_ids=["stu-c", "stu-d", "fd-x"],
    )
    prayer.weigh_prophecy(ph.id, weigher_id="stu-c", judgment="confirm")
    prayer.weigh_prophecy(ph.id, weigher_id="fd-x", judgment="confirm")
    prayer.record_fulfillment(ph.id, status="fulfilled", testimony="It came true.")

    _simulate_restart(persisted_prayer)

    reloaded = prayer.get_prayer(pr.id)
    assert reloaded.status == "answered_yes"
    assert reloaded.answer["testimony"] == "Led it twice."
    assert reloaded.recipient_ids == ["stu-b"]
    assert [i.peer_id for i in prayer.list_intercessions(pr.id)] == ["stu-b"]

    reloaded_ph = prayer.get_prophecy(ph.id)
    assert reloaded_ph.status == "confirmed"
    assert len(reloaded_ph.weighings) == 2
    assert reloaded_ph.fulfillment["status"] == "fulfilled"

    record = prayer.prayer_track_record("stu-a")
    assert record["answered_favorable"] == 1


def test_updates_overwrite_not_duplicate(persisted_prayer):
    pr = prayer.submit_prayer(student_id="stu-a", petition="Patience.")
    prayer.watch_prayer(pr.id)
    prayer.mark_answered(pr.id, status="partial", testimony="Some days.")

    with persisted_prayer() as session:
        rows = session.query(LedgerRecord).filter_by(kind="prayer").all()
    assert len(rows) == 1  # merge upserts the same row, three writes → one record

    _simulate_restart(persisted_prayer)
    assert len(prayer.list_prayers(student_id="stu-a")) == 1
    assert prayer.get_prayer(pr.id).status == "partial"


def test_reset_clears_db_too(persisted_prayer):
    prayer.submit_prayer(student_id="stu-a", petition="Anything.")
    prayer.reset()
    with persisted_prayer() as session:
        assert session.query(LedgerRecord).count() == 0
    _simulate_restart(persisted_prayer)
    assert prayer.list_prayers() == []


def test_in_memory_default_writes_nothing(tmp_path):
    """Without enable_persistence, mutations must not touch any DB."""
    prayer.reset()
    prayer.submit_prayer(student_id="stu-a", petition="Quietly.")
    assert prayer._session_factory is None
    prayer.reset()
