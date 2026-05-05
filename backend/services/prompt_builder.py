from __future__ import annotations


def build_prompt(memory: list[str], user_input: str) -> str:
    context = "\n".join(f"- {item}" for item in memory) if memory else "(no prior context)"
    return (
        "You are a seminary AI mentor for a formation program. "
        "Use the prior context, if relevant, to answer in a warm, pastoral tone.\n\n"
        f"Prior context for this student:\n{context}\n\n"
        f"Student message:\n{user_input}\n\n"
        "Respond in 2-4 sentences."
    )
