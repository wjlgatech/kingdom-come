from __future__ import annotations

import json
import os
from typing import Any

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    url = os.getenv("REDIS_URL")
    if url:
        import redis

        _client = redis.Redis.from_url(url)
    else:
        import fakeredis

        _client = fakeredis.FakeRedis()
    return _client


def publish_event(channel: str, data: dict[str, Any]) -> int:
    return int(_get_client().publish(channel, json.dumps(data)))


def reset_for_tests() -> None:
    global _client
    _client = None
