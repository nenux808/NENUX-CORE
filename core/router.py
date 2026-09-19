"""Conservative request routing for NENUX Core."""

import re


ACTION_PATTERNS = (
    r"\b(run|execute|test|verify|debug|fix|repair)\b",
    r"\b(read|open|inspect|list|write|create|modify|edit|delete)\b.*\b(file|folder|script|code|program|workspace)\b",
    r"\b(file|folder|script|code|program|workspace)\b.*\b(read|open|inspect|list|write|create|modify|edit|delete)\b",
)

MEMORY_PATTERNS = (
    r"\b(remember|recall)\b",
    r"\b(previous|previously|earlier|last time|before)\b",
)


def route_request(user_input: str) -> str:
    """Return conversation, memory, or agent_task.

    The router is intentionally conservative: anything that looks actionable
    falls back to the hardened agent pipeline.
    """
    text = user_input.strip().lower()

    if any(re.search(pattern, text) for pattern in ACTION_PATTERNS):
        return "agent_task"

    if any(re.search(pattern, text) for pattern in MEMORY_PATTERNS):
        return "memory"

    return "conversation"
