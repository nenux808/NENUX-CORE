"""Wake-phrase parsing for the NENUX voice interface."""

import re

from config import VOICE_WAKE_ALIASES, VOICE_WAKE_PHRASE


def _wake_variants(wake_phrase: str) -> tuple[str, ...]:
    """Return configured aliases when using the default Clara wake phrase."""
    if wake_phrase.strip().lower() == VOICE_WAKE_PHRASE.strip().lower():
        return tuple(alias.strip().lower() for alias in VOICE_WAKE_ALIASES)

    return (wake_phrase.strip().lower(),)


def extract_wake_command(
    transcript: str,
    wake_phrase: str = VOICE_WAKE_PHRASE,
) -> str | None:
    """Return the command after a recognized wake phrase, or None."""
    text = transcript.strip()

    for wake in _wake_variants(wake_phrase):
        words = [re.escape(part) for part in wake.split()]
        pattern = r"^\s*" + r"[\s,!.?:;\-]*".join(words) + r"\b"
        match = re.match(pattern, text, flags=re.IGNORECASE)

        if match:
            return text[match.end():].lstrip(" ,.!?:;-").strip()

    return None
