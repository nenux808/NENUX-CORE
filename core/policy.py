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


def _quoted_spans(text: str) -> list[str]:
    """Return simple quoted spans from generated text."""
    return re.findall(r'["“](.+?)["”]', text, flags=re.DOTALL)


def is_effective_lyrics_request(user_input: str, history: list[dict] | None = None) -> bool:
    """Treat short follow-ups as lyric requests when recent session context is lyrics."""
    return (
        is_lyrics_request(user_input)
        or bool(history) and is_lyrics_context_followup(user_input, history)
    )


def enforce_lyrics_output_policy(
    user_input: str,
    response: str,
    history: list[dict] | None = None,
) -> str:
    """Prevent long generated lyric reproduction while preserving useful help."""
    if not is_effective_lyrics_request(user_input, history):
        return response

    quoted = _quoted_spans(response)
    too_long_quote = any(len(span.split()) > 10 for span in quoted)

    # Multi-line lyric-shaped output is also treated as long-form reproduction.
    nonempty_lines = [line.strip() for line in response.splitlines() if line.strip()]
    lyric_shaped = len(nonempty_lines) >= 6

    if too_long_quote or lyric_shaped:
        return (
            "I found and verified the song, but I won’t reproduce a long lyric passage. "
            "I can give you a brief summary, explain the meaning, or share a short verified excerpt."
        )

    return response



def document_indexing_requested(text: str) -> bool:
    """Return True only when the user explicitly asks to index/reindex documents."""
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    index_terms = ("index", "reindex", "re index")
    document_terms = (
        "workspace",
        "document",
        "documents",
        "file",
        "files",
        "notes",
        "report",
        "reports",
    )
    return (
        any(term in normalized for term in index_terms)
        and any(term in normalized for term in document_terms)
    )



def is_browser_media_request(text: str) -> bool:
    """Detect direct browser media playback/watch requests."""
    normalized = text.lower().strip()
    return bool(re.match(r"^(play|watch|listen to)\b", normalized))


def recent_browser_media_request(history: list[dict]) -> str | None:
    """Return the most recent user playback request from session history."""
    for item in reversed(history or []):
        if item.get("role") != "user":
            continue
        content = str(item.get("content", "")).strip()
        if is_browser_media_request(content):
            return content
    return None


def is_chrome_profile_followup(text: str, history: list[dict]) -> bool:
    """Detect a short response to Clara asking which Chrome profile to use."""
    normalized = re.sub(r"[^a-z0-9@._ -]+", " ", text.lower()).strip()
    if not normalized or len(normalized.split()) > 8:
        return False

    recent_assistant = " ".join(
        str(item.get("content", ""))
        for item in (history or [])[-4:]
        if item.get("role") == "assistant"
    ).lower()

    return (
        "chrome profile" in recent_assistant
        or "which profile" in recent_assistant
        or "profile should i use" in recent_assistant
    ) and recent_browser_media_request(history) is not None



def is_browser_media_correction_followup(text: str, history: list[dict]) -> bool:
    """Keep playback intent active when the user corrects a wrong result."""
    if recent_browser_media_request(history) is None:
        return False

    normalized = re.sub(r"[^a-z0-9 -]+", " ", text.lower()).strip()

    correction_terms = (
        "wrong video",
        "wrong song",
        "wrong one",
        "search again",
        "search on youtube",
        "i need",
        "the song name is",
        "the artist name is",
        "the artist's name is",
        "it is a song",
        "it's a song",
        "single rap video",
    )

    if any(term in normalized for term in correction_terms):
        return True

    # Spelled-out corrections such as S-H-A-N-P-U-T-H-A or T-H-R-I-L-L-I-U-M.
    if re.fullmatch(r"(?:[a-z]-){2,}[a-z]", normalized):
        return True

    return False



def needs_code_target_clarification(
    text: str,
    history: list[dict] | None = None,
) -> bool:
    """Ask which code/file is meant instead of inventing a debugging target."""
    normalized = re.sub(r"\s+", " ", str(text).lower()).strip()

    deictic_debug_phrases = (
        "debug this code",
        "fix this code",
        "repair this code",
        "review this code",
        "investigate this code",
        "find the root cause in this code",
    )

    if not any(phrase in normalized for phrase in deictic_debug_phrases):
        return False

    explicit_target_markers = (
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        " file ",
        " workspace ",
        "traceback",
        "error:",
    )

    padded = f" {normalized} "
    if any(marker in padded for marker in explicit_target_markers):
        return False

    previous_user = ""
    for item in reversed(history or []):
        if item.get("role") == "user":
            previous_user = str(item.get("content", ""))
            break

    # "This code" may inherit only the immediately preceding user-provided
    # code/file/error target. Older history is context, not a pointing target.
    if (
        "```" in previous_user
        or "traceback" in previous_user.lower()
        or re.search(
            r"\b\w+\.(py|js|ts|tsx|jsx|java|cpp|c|cs|go|rs|php|rb)\b",
            previous_user.lower(),
        )
    ):
        return False

    return True
