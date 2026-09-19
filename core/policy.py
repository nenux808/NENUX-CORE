def is_history_query(text: str) -> bool:
    text = text.lower().strip()

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
