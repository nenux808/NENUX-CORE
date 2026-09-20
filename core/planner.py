import re
import json
from ollama import chat

from config import CHAT_MODEL


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
19. If open_chrome_url reports that multiple profiles exist and no default is saved, stop and ask the user which listed Chrome profile to use.
20. If the user explicitly says to remember a chosen Chrome profile as default, use set_default_chrome_profile.

Return ONLY valid JSON:

{
  "steps": [
    "First step",
    "Second step"
  ]
}
"""


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

    response = chat(
        model=CHAT_MODEL,
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
