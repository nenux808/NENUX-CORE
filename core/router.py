"""Request routing for NENUX Core."""

import re

from ollama import chat

from config import FAST_MODEL
from core.desktop_intent import (
    interpret_desktop_intent,
    should_try_desktop_intent,
)


ACTION_PATTERNS = (
    r"\b(pause|resume|unpause|mute|unmute|volume up|volume down|turn it up|turn it down|next track|previous track|skip)\b",
    r"\b(play it|play the video|video play|resume the video)\b",
    r"\b(next tab|previous tab|close (this )?tab|focus chrome|open chrome|open gmail|open vs ?code|open visual studio code)\b",
    r"^\s*(play|watch|listen to)\b",
    r"\b(list|show|check|which|what)\b.*\bchrome profiles?\b",
    r"\bchrome profiles?\b.*\b(list|show|check|available|have|use|default)\b",
    r"\b(set|make|use|remember)\b.*\b(profile|chrome profile)\b.*\b(default|primary)\b",
    r"\b(first|second|third|default|profile \d+)\b.*\bprofile\b.*\b(default|primary)\b",
    r"\b(latest|current|currently|today|tonight|right now|live|news|weather|forecast|price|score)\b",
    r"\b(search|look up|find online|on the web|internet)\b",
    r"\b(run|execute|test|verify|debug|fix|repair)\b",
    r"\b(read|open|inspect|list|write|create|modify|edit|delete|index)\b.*\b(file|folder|script|code|program|workspace|document|documents|notes|report|reports)\b",
    r"\b(file|folder|script|code|program|workspace|document|notes|report)\b.*\b(read|open|inspect|list|write|create|modify|edit|delete|say|mention|contain|about)\b",
    r"\b(what does|what do|find in|search in|according to)\b.*\b(file|document|notes|report|workspace)\b",
)

MEMORY_PATTERNS = (
    r"\b(remember|recall)\b",
    r"\b(previous|previously|earlier|last time|before)\b",
)

MEDIA_RETRIEVAL_PATTERNS = (
    r"\b(lyrics?|release date|released|album|who sings|who sang|who wrote|song meaning|track meaning)\b",
)

RETRIEVAL_HINT_PATTERNS = (
    r"\b(youtube|channel|website|site|company|business|brand|product|app|service|restaurant|hotel|place)\b",
    r"\b(who is|what is|what do you know about|tell me about|have you heard of)\b",
)

ROUTE_LABELS = {"conversation", "memory", "agent_task", "retrieval"}


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _model_route(user_input: str) -> str:
    """Classify ambiguous knowledge requests without executing any tool."""
    response = chat(
        model=FAST_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify one user request for NENUX Core. Return exactly one label: "
                    "conversation, memory, agent_task, or retrieval. "
                    "conversation = casual chat or stable common knowledge that the local model can answer. "
                    "memory = asks about the user's prior conversations/work. "
                    "agent_task = asks to execute, modify, read local resources, test, or perform an action. "
                    "retrieval = asks about a specific named person, organization, channel, website, product, "
                    "place, event, or fact where external lookup may be needed, or where freshness/verification "
                    "would materially improve accuracy. When uncertain between conversation and retrieval for "
                    "a specific real-world entity, choose retrieval. Do not answer the request."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    )
    label = response.message.content.strip().lower().split()[0].strip(".,:;")
    return label if label in ROUTE_LABELS else "conversation"


def route_request(user_input: str) -> str:
    """Return conversation, memory, agent_task, or retrieval."""
    text = user_input.strip().lower()

    if _matches(ACTION_PATTERNS, text):
        return "agent_task"

    if _matches(MEDIA_RETRIEVAL_PATTERNS, text):
        return "retrieval"

    if _matches(MEMORY_PATTERNS, text):
        return "memory"

    if _matches(RETRIEVAL_HINT_PATTERNS, text):
        return _model_route(user_input)

    if should_try_desktop_intent(user_input):
        desktop = interpret_desktop_intent(user_input)
        if (
            desktop.get("intent") != "none"
            and float(desktop.get("confidence", 0.0)) >= 0.72
        ):
            return "agent_task"

    return "conversation"
