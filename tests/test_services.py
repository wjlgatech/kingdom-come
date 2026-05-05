import pytest

from backend.services.curriculum import recommend_content
from backend.services.orchestration import class_orchestrator
from backend.services.predictive import dropout_risk


def test_dropout_risk_scores_low_engagement_and_few_reflections():
    student = {"engagement": 0.2, "reflection_count": 1}

    assert dropout_risk(student) == {"score": 3, "level": "high", "reasons": ["low_engagement", "few_reflections"]}


def test_dropout_risk_accepts_missing_fields_with_defaults():
    assert dropout_risk({}) == {"score": 0, "level": "low", "reasons": []}


def test_dropout_risk_rejects_invalid_engagement():
    with pytest.raises(ValueError, match="engagement"):
        dropout_risk({"engagement": 1.4, "reflection_count": 2})


def test_recommend_content_normalizes_calling_and_prior_completed_content():
    student = {"calling": ["Evangelism", "Pastoral Care"], "completed_content": ["mission_theology"]}

    assert recommend_content(student) == ["field_practice", "pastoral_counseling", "general_theology"]


def test_recommend_content_returns_general_track_when_calling_missing():
    assert recommend_content({}) == ["general_theology"]


def test_class_orchestrator_returns_action_details():
    groups = [
        {"id": "alpha", "members": ["ana", "bo"]},
        {"id": "beta", "members": ["cy", "dee", "eli"]},
    ]

    assert class_orchestrator(groups) == [
        {"action": "merge_group", "group_id": "alpha", "reason": "group_below_minimum_size", "member_count": 2}
    ]
