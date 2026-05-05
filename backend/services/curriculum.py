def recommend_content(student):
    calling = student.get('calling') or []
    completed_content = set(student.get('completed_content') or [])

    if isinstance(calling, str):
        callings = {calling.lower()}
    else:
        callings = {item.lower() for item in calling}

    recommendations = []
    if "evangelism" in callings:
        recommendations.extend(["mission_theology", "field_practice"])
    if "pastoral care" in callings or "pastoral_care" in callings:
        recommendations.append("pastoral_counseling")
    recommendations.append("general_theology")

    return [item for item in recommendations if item not in completed_content]
