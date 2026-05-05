def dropout_risk(student):
    engagement = student.get('engagement', 1.0)
    reflection_count = student.get('reflection_count', 2)

    if not 0 <= engagement <= 1:
        raise ValueError("engagement must be between 0 and 1")
    if reflection_count < 0:
        raise ValueError("reflection_count must be zero or greater")

    score = 0
    reasons = []
    if engagement < 0.3:
        score += 2
        reasons.append("low_engagement")
    if reflection_count < 2:
        score += 1
        reasons.append("few_reflections")

    if score >= 3:
        level = "high"
    elif score >= 1:
        level = "medium"
    else:
        level = "low"

    return {"score": score, "level": level, "reasons": reasons}
