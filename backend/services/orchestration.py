def class_orchestrator(groups):
    actions = []
    for g in groups:
        group_id = g.get("id") if isinstance(g, dict) else None
        members = g.get("members", []) if isinstance(g, dict) else g
        member_count = len(members)
        if member_count < 3:
            actions.append({
                "action": "merge_group",
                "group_id": group_id,
                "reason": "group_below_minimum_size",
                "member_count": member_count,
            })
    return actions
