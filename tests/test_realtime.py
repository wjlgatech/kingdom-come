import json

import pytest

from backend.services import event_engine, realtime


@pytest.fixture(autouse=True)
def fakeredis_only(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    realtime.reset_for_tests()
    yield
    realtime.reset_for_tests()


def test_publish_event_routes_through_fakeredis_when_no_url():
    client = realtime._get_client()
    pubsub = client.pubsub()
    pubsub.subscribe("activity")
    pubsub.get_message(timeout=0.1)

    delivered = realtime.publish_event("activity", {"hello": "world"})

    msg = pubsub.get_message(timeout=1.0)
    assert delivered == 1
    assert msg is not None
    assert json.loads(msg["data"]) == {"hello": "world"}
    pubsub.close()


def test_event_engine_truncates_long_messages():
    client = realtime._get_client()
    pubsub = client.pubsub()
    pubsub.subscribe("activity")
    pubsub.get_message(timeout=0.1)

    event_engine.process_events("stu-1", "x" * 500)

    msg = pubsub.get_message(timeout=1.0)
    payload = json.loads(msg["data"])
    assert payload["student_id"] == "stu-1"
    assert len(payload["message"]) == 200
    pubsub.close()
