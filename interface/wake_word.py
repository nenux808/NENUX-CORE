"""Wake-phrase parsing for the NENUX voice interface."""

from config import VOICE_WAKE_PHRASE


def extract_wake_command(
    transcript: str,
    wake_phrase: str = VOICE_WAKE_PHRASE,
) -> str | None:
    """Return the command after the wake phrase, or None when not addressed."""
    text = transcript.strip()
    lowered = text.lower()
    wake = wake_phrase.strip().lower()

    if not lowered.startswith(wake):
        return None

    command = text[len(wake):].lstrip(" ,.!?:;-").strip()
    return command
