"""Helpers for Clara's in-memory voice session."""

from config import VOICE_SESSION_MAX_MESSAGES


def append_session_turn(
    history: list[dict],
    user_text: str,
    assistant_text: str,
    max_messages: int = VOICE_SESSION_MAX_MESSAGES,
) -> list[dict]:
    """Append one voice turn and keep only the most recent session messages."""
    updated = list(history)
    updated.append({"role": "user", "content": user_text})
    updated.append({"role": "assistant", "content": assistant_text})

    if max_messages <= 0:
        return []

    return updated[-max_messages:]
