"""AI-assisted grading of spiritual formation reports (《属灵操练练习》报告).

Pipeline: extract report text -> structural checks (flags, never penalties) ->
LLM drafts a grade + pastoral comment in the professor's voice (learned from a
local, gitignored corpus of past comments) -> professor reviews and finalizes.

Hard invariant: nothing produced here reaches a student without the professor's
explicit finalize action. This module only drafts.
"""
