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

Return ONLY valid JSON:

{
  "steps": [
    "First step",
    "Second step"
  ]
}
"""


def create_plan(goal: str) -> list[str]:

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
