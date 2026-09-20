"""Semantic interpretation for approved desktop-control intents."""

import json

from ollama import chat

from config import CHAT_MODEL


DESKTOP_INTENTS = {
    "none",
    "media_pause",
    "media_resume",
    "media_mute",
    "media_unmute",
    "volume_up",
    "volume_down",
    "next_track",
    "previous_track",
    "next_tab",
    "previous_tab",
    "close_tab",
    "close_all_tabs",
    "open_chrome",
    "focus_chrome",
    "open_gmail",
    "open_vscode",
}


INTENT_PROMPT = """You classify natural-language Windows desktop commands for NENUX Core.

Return ONLY JSON:
{"intent":"one_allowed_intent","confidence":0.0}

Allowed intents:
none
media_pause
media_resume
media_mute
media_unmute
volume_up
volume_down
next_track
previous_track
next_tab
previous_tab
close_tab
close_all_tabs
open_chrome
focus_chrome
open_gmail
open_vscode

Interpret meaning, not exact wording. Be tolerant of speech-recognition mistakes when the
meaning is still clear.

Examples:
"can you shut every chrome tab" -> close_all_tabs
"close all chrome times" -> close_all_tabs if 'times' is plausibly a misheard 'tabs'
"get rid of this tab" -> close_tab
"bring chrome up" -> focus_chrome
"turn the sound back on" -> media_unmute
"make it louder" -> volume_up
"hold the video" -> media_pause
"continue the video" -> media_resume
"open my mail" -> open_gmail

Use none for ordinary conversation, questions, or requests outside the listed capabilities.
Do not invent unsupported capabilities.
"""


def interpret_desktop_intent(text: str) -> dict:
    """Map free-form language to one whitelisted desktop intent."""
    response = chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": str(text)},
        ],
    )

    raw = response.message.content.strip()

    try:
        start = raw.find("{")
        if start == -1:
            return {"intent": "none", "confidence": 0.0}

        data, _ = json.JSONDecoder().raw_decode(raw[start:])
    except (json.JSONDecodeError, ValueError):
        return {"intent": "none", "confidence": 0.0}

    intent = str(data.get("intent", "none")).strip().lower()
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    if intent not in DESKTOP_INTENTS:
        intent = "none"

    confidence = max(0.0, min(confidence, 1.0))

    return {
        "intent": intent,
        "confidence": confidence,
    }


def desktop_intent_plan(intent: str) -> list[str] | None:
    mapping = {
        "media_pause": ["Pause current media using media_control"],
        "media_resume": ["Resume current media using media_control"],
        "media_mute": ["Mute system audio using media_control"],
        "media_unmute": ["Unmute system audio using media_control"],
        "volume_up": ["Increase system volume using media_control"],
        "volume_down": ["Decrease system volume using media_control"],
        "next_track": ["Skip to next media track using media_control"],
        "previous_track": ["Go to previous media track using media_control"],
        "next_tab": ["Switch to the next Chrome tab using chrome_tab_control"],
        "previous_tab": ["Switch to the previous Chrome tab using chrome_tab_control"],
        "close_tab": ["Close the current Chrome tab using chrome_tab_control"],
        "close_all_tabs": ["Close all tabs in the current Chrome window using chrome_tab_control"],
        "open_chrome": ["Open Google Chrome using open_chrome"],
        "focus_chrome": ["Bring Chrome to the foreground using focus_chrome"],
        "open_gmail": ["Open Gmail in Chrome using open_gmail"],
        "open_vscode": ["Open Visual Studio Code using open_vscode"],
    }
    return mapping.get(intent)



def should_try_desktop_intent(text: str) -> bool:
    """Cheap gate before invoking the model-based desktop interpreter."""
    normalized = str(text).lower()
    hints = (
        "chrome",
        "browser",
        "tab",
        "gmail",
        "mail",
        "vscode",
        "vs code",
        "visual studio code",
        "pause",
        "resume",
        "video",
        "mute",
        "sound",
        "volume",
        "louder",
        "quieter",
        "track",
        "music",
        "close",
        "open",
        "shut",
        "bring",
    )
    return any(hint in normalized for hint in hints)


def desktop_intent_command(intent: str) -> str | None:
    """Convert an approved semantic intent into an explicit executable command."""
    mapping = {
        "media_pause": "pause the current media",
        "media_resume": "resume the current media",
        "media_mute": "mute the system audio",
        "media_unmute": "unmute the system audio",
        "volume_up": "increase the system volume",
        "volume_down": "decrease the system volume",
        "next_track": "play the next media track",
        "previous_track": "play the previous media track",
        "next_tab": "switch to the next Chrome tab",
        "previous_tab": "switch to the previous Chrome tab",
        "close_tab": "close the current Chrome tab",
        "close_all_tabs": "close all tabs in the current Chrome window",
        "open_chrome": "open Chrome",
        "focus_chrome": "focus Chrome",
        "open_gmail": "open Gmail",
        "open_vscode": "open VS Code",
    }
    return mapping.get(intent)



def desktop_intent_tool_call(intent: str) -> dict | None:
    """Map one approved semantic intent to one whitelisted tool call."""
    mapping = {
        "media_pause": {"tool": "media_control", "arguments": {"action": "pause"}},
        "media_resume": {"tool": "media_control", "arguments": {"action": "resume"}},
        "media_mute": {"tool": "media_control", "arguments": {"action": "mute"}},
        "media_unmute": {"tool": "media_control", "arguments": {"action": "unmute"}},
        "volume_up": {"tool": "media_control", "arguments": {"action": "volume_up"}},
        "volume_down": {"tool": "media_control", "arguments": {"action": "volume_down"}},
        "next_track": {"tool": "media_control", "arguments": {"action": "next"}},
        "previous_track": {"tool": "media_control", "arguments": {"action": "previous"}},
        "next_tab": {"tool": "chrome_tab_control", "arguments": {"action": "next_tab"}},
        "previous_tab": {"tool": "chrome_tab_control", "arguments": {"action": "previous_tab"}},
        "close_tab": {"tool": "chrome_tab_control", "arguments": {"action": "close_tab"}},
        "close_all_tabs": {"tool": "chrome_tab_control", "arguments": {"action": "close_all_tabs"}},
        "open_chrome": {"tool": "open_chrome", "arguments": {}},
        "focus_chrome": {"tool": "focus_chrome", "arguments": {}},
        "open_gmail": {"tool": "open_gmail", "arguments": {}},
        "open_vscode": {"tool": "open_vscode", "arguments": {}},
    }
    return mapping.get(intent)
