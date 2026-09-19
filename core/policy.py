import re

def is_lyrics_request(text: str) -> bool:
    text = text.lower().strip()
    return "lyric" in text or "lyrics" in text


def is_media_content_request(text: str) -> bool:
    text = text.lower().strip()

    media_terms = {
        "lyric",
        "lyrics",
        "song",
        "track",
        "album",
        "movie quote",
        "film quote",
        "book quote",
        "poem",
    }

    return any(term in text for term in media_terms)


def _recent_history_text(history: list[dict], limit: int = 4) -> str:
    recent = history[-limit:] if history else []
    return " ".join(
        str(item.get("content", ""))
        for item in recent
        if item.get("role") in {"user", "assistant"}
    ).lower()


def is_lyrics_context_followup(text: str, history: list[dict]) -> bool:
    """Keep lyric/media intent active across short conversational follow-ups."""
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    recent = _recent_history_text(history)

    if "lyric" not in recent:
        return False

    followups = {
        "yes",
        "yes please",
        "yeah",
        "yeah please",
        "sure",
        "okay",
        "ok",
        "please",
        "go ahead",
        "show me",
        "more",
        "tell me more",
    }

    return normalized in followups


def is_history_query(text: str) -> bool:
    text = text.lower().strip()

    if is_media_content_request(text):
        return False

    phrases = {
        "have we",
        "did we",
        "previously",
        "before",
        "last time",
        "in the past",
        "do you remember",
        "remember when",
        "what did we",
        "what were we",
        "have you previously",
        "have i previously",
    }

    return any(
        phrase in text
        for phrase in phrases
    )


def requires_fresh_verification(text: str) -> bool:
    text = text.lower().strip()

    phrases = {
        "verify now",
        "check now",
        "run again",
        "rerun",
        "re-run",
        "execute again",
        "execute it",
        "run it",
        "test it",
        "test again",
        "fresh verification",
        "current result",
        "current output",
        "right now",
    }

    return any(
        phrase in text
        for phrase in phrases
    )


def memory_only_mode(text: str) -> bool:
    return (
        is_history_query(text)
        and not requires_fresh_verification(text)
    )


def should_store_task_memory(text: str) -> bool:
    return not memory_only_mode(text)
