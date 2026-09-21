import re
import json
from ollama import chat

from config import PLANNER_MODEL, MODEL_CONTEXT_TOKENS
from core.policy import (
    extract_youtube_search_query,
    is_youtube_search_request,
)
from core.desktop_intent import (
    desktop_intent_plan,
    interpret_desktop_intent,
    should_try_desktop_intent,
)


PLANNER_PROMPT = """
You are the planning module for NENUX Core.

Convert the user's CURRENT goal into a small ordered list of practical steps.

NENUX currently has ONLY these tools:

- list_files: inspect workspace directories
- read_file: read a text file
- write_file: create or modify a text file
- run_python: execute a Python file
- web_search: retrieve current/public information from the web
- web_fetch: fetch readable text from a public web page for verification
- index_document: index one supported workspace text document
- index_workspace_documents: index supported text documents under workspace
- search_documents: retrieve relevant chunks from indexed workspace documents
- list_chrome_profiles: list existing local Chrome profiles
- set_default_chrome_profile: remember the Chrome profile to use by default
- open_chrome_url: open a verified HTTP(S) URL in a selected Chrome profile
- media_control: send approved media/volume keys
- open_chrome: launch Chrome
- focus_chrome: bring a visible Chrome window to foreground
- chrome_tab_control: next, previous, or close Chrome tab
- open_gmail: open Gmail in the selected/default Chrome profile
- open_vscode: launch Visual Studio Code
- open_youtube_search: open YouTube search results for a query in Chrome
- youtube_media_control: target pause/resume at a visible YouTube Chrome window

RULES:

1. Use between 1 and 6 steps.
2. Every step must be achievable using the available tools.
3. Never say things like:
   - open in an IDE
   - use a code editor
   - click something
   - browse the desktop
   unless such a tool actually exists.
4. Use "read the file" instead of "open in an IDE".
5. Use "execute the Python script" when run_python is appropriate.
6. Treat the request as a fresh task.
7. Previous conversation claims are NOT evidence that the current task has happened.
8. Keep steps concrete and verifiable.
9. For questions about a specific public person, organization, YouTube channel, website, product, place, event, or other external entity, prefer web_search over local filesystem tools unless the user explicitly mentions a local file.
10. Do NOT plan list_files/read_file merely because the user asks "what do you know about" an external entity.
11. For a simple retrieval question, normally use one step such as "Search the web for reliable information about <entity> and answer from the retrieved evidence."
12. For public web/media questions, never invent local file steps such as "read the file containing..." unless the user explicitly named a local file.
13. If verification from the actual source page is useful, plan web_search followed by web_fetch, not read_file.
14. For lyric requests, do not plan to reproduce full lyrics. Plan to verify the song/title/artist and provide only a brief summary or a very short verified excerpt if allowed by runtime policy.
15. For questions about the contents of local workspace documents, prefer search_documents when the documents are already indexed.
16. If indexing is explicitly requested, use index_document or index_workspace_documents before search_documents.
17. Do not use web_search for a question that is specifically about the user's local workspace documents unless the user also asks for external verification.
18. For media playback commands such as "play <song>" or "watch <video>", use web_search to find the most relevant official YouTube watch URL, then use open_chrome_url. Do not invent a YouTube URL.
18a. For commands like "search <query> on YouTube" or "find <query> in YouTube", use open_youtube_search directly. Do not use web_search and do not merely list links.
19. If open_chrome_url reports that multiple profiles exist and no default is saved, stop and ask the user which listed Chrome profile to use.
20. If the user explicitly says to remember a chosen Chrome profile as default, use set_default_chrome_profile.
21. For generic pause/resume/mute/volume/track controls, use media_control. When the user explicitly targets YouTube for pause/resume, use youtube_media_control.
22. For next/previous/close tab commands, use chrome_tab_control.
23. For "open Chrome", use open_chrome. For "focus Chrome", use focus_chrome.
24. For "open Gmail", use open_gmail. For "open VS Code", use open_vscode.
24. Never use run_python or filesystem tools for simple desktop controls when a dedicated PC tool exists.
25. The filesystem tool is already rooted inside the NENUX workspace. Use "." for the workspace root; never plan list_files with path "workspace".
26. For local code debugging, inspect the named/provided local code and reproduce the error before using web_search. Do not add generic debugging-tip web searches unless the user explicitly asks for external research or local evidence shows a dependency/API issue that needs verification.
27. Never guess which local code file "this code" refers to. The current request must explicitly identify the target.

Return ONLY valid JSON:

{
  "steps": [
    "First step",
    "Second step"
  ]
}
"""


def _desktop_control_plan(goal: str) -> list[str] | None:
    text = goal.lower().strip()

    if "youtube" in text:
        if "pause" in text:
            return [
                "Pause YouTube in the visible Chrome window using youtube_media_control"
            ]
        if any(term in text for term in ("resume", "unpause", "continue")):
            return [
                "Resume YouTube in the visible Chrome window using youtube_media_control"
            ]

    if any(phrase in text for phrase in ("pause", "pause it", "pause the video")):
        return ["Pause or resume current media using media_control"]

    if any(
        phrase in text
        for phrase in (
            "resume",
            "unpause",
            "play it",
            "play the video",
            "video play",
            "resume the video",
        )
    ):
        return ["Pause or resume current media using media_control"]

    if "unmute" in text:
        return ["Toggle system mute using media_control"]

    if re.search(r"\bmute\b", text):
        return ["Toggle system mute using media_control"]

    if "volume up" in text or "turn it up" in text:
        return ["Increase system volume using media_control"]

    if "volume down" in text or "turn it down" in text:
        return ["Decrease system volume using media_control"]

    if "next track" in text or re.search(r"\bskip\b", text):
        return ["Skip to next media track using media_control"]

    if "previous track" in text:
        return ["Go to previous media track using media_control"]

    if "next tab" in text:
        return ["Switch to the next Chrome tab using chrome_tab_control"]

    if "previous tab" in text:
        return ["Switch to the previous Chrome tab using chrome_tab_control"]

    if (
        "close all tabs" in text
        or "close all chrome tabs" in text
        or "close every chrome tab" in text
        or "shut all chrome tabs" in text
    ):
        return ["Close all tabs in the current Chrome window using chrome_tab_control"]

    if "close this tab" in text or "close tab" in text:
        return ["Close the current Chrome tab using chrome_tab_control"]

    if "open chrome" in text:
        return ["Open Google Chrome using open_chrome"]

    if "focus chrome" in text:
        return ["Bring Chrome to the foreground using focus_chrome"]

    if "open gmail" in text:
        return ["Open Gmail in Chrome using open_gmail"]

    if (
        "open vscode" in text
        or "open vs code" in text
        or "open visual studio code" in text
    ):
        return ["Open Visual Studio Code using open_vscode"]

    return None

def _is_chrome_profile_default_goal(goal: str) -> bool:
    text = goal.lower().strip()
    return (
        "profile" in text
        and any(term in text for term in ("default", "primary"))
        and any(term in text for term in ("set", "make", "use", "remember", "first", "second", "third"))
    )


def _is_chrome_profile_list_goal(goal: str) -> bool:
    text = goal.lower().strip()
    return (
        "chrome" in text
        and ("profile" in text or "profiles" in text)
        and any(term in text for term in ("list", "show", "which", "what", "available", "check"))
    )


def _is_browser_media_goal(goal: str) -> bool:
    text = goal.lower().strip()
    return bool(re.match(r"^(play|watch|listen to)\b", text))


def _is_workspace_index_goal(goal: str) -> bool:
    text = goal.lower().strip()
    return (
        "index" in text
        and "workspace" in text
        and any(term in text for term in ("document", "documents", "file", "files"))
    )


def _is_local_document_goal(goal: str) -> bool:
    text = goal.lower().strip()

    if any(term in text for term in ("web", "online", "internet")):
        return False

    local_terms = ("document", "documents", "file", "files", "report", "reports", "notes", "workspace")
    question_terms = (
        "what does",
        "what do",
        "what is in",
        "what's in",
        "find in",
        "search in",
        "according to",
        "does my",
        "say about",
        "mention",
        "contain",
    )

    return (
        any(term in text for term in local_terms)
        and any(term in text for term in question_terms)
    )


def create_plan(goal: str) -> list[str]:

    if is_youtube_search_request(goal):
        query = extract_youtube_search_query(goal)
        return [
            f'Open YouTube search results for "{query}" in Chrome using open_youtube_search'
        ]

    desktop_plan = _desktop_control_plan(goal)
    if desktop_plan:
        return desktop_plan

    if _is_chrome_profile_default_goal(goal):
        return [
            "List available local Chrome profiles using list_chrome_profiles",
            "Set the selected Chrome profile as default using set_default_chrome_profile",
        ]

    if _is_chrome_profile_list_goal(goal):
        return [
            "List available local Chrome profiles using list_chrome_profiles"
        ]

    if _is_browser_media_goal(goal):
        return [
            "Search the web for the most relevant official YouTube video for the requested media",
            "Open the verified YouTube video in Chrome using open_chrome_url",
        ]

    if _is_workspace_index_goal(goal):
        return [
            "Index all supported workspace documents using index_workspace_documents"
        ]

    if _is_local_document_goal(goal):
        return [
            "Search the indexed workspace documents using search_documents and answer from the retrieved evidence"
        ]

    if should_try_desktop_intent(goal):
        desktop = interpret_desktop_intent(goal)
        if (
            desktop.get("intent") != "none"
            and float(desktop.get("confidence", 0.0)) >= 0.72
        ):
            semantic_plan = desktop_intent_plan(desktop["intent"])
            if semantic_plan:
                return semantic_plan

    response = chat(
        model=PLANNER_MODEL,
        options={"num_ctx": MODEL_CONTEXT_TOKENS},
        messages=[
            {
                "role": "system",
                "content": PLANNER_PROMPT
            },
            {
                "role": "user",
                "content": goal
            }
        ]
    )

    raw = response.message.content.strip()

    decoder = json.JSONDecoder()

    try:
        start = raw.find("{")

        if start == -1:
            return [goal]

        data, _ = decoder.raw_decode(
            raw[start:]
        )

        steps = data.get(
            "steps",
            []
        )

        if isinstance(steps, list):

            cleaned = [
                str(step).strip()
                for step in steps
                if str(step).strip()
            ]

            if cleaned:
                return cleaned

    except (
        json.JSONDecodeError,
        ValueError
    ):
        pass

    return [goal]
