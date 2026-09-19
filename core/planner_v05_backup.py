import json

from ollama import chat


MODEL = "qwen3:4b-instruct"


PLANNER_PROMPT = """
You are the planning module for NENUX Core.

Convert the user's goal into a small ordered list of practical steps.

Return ONLY valid JSON in this format:

{
  "steps": [
    "First step",
    "Second step",
    "Third step"
  ]
}

Rules:
- Use between 1 and 6 steps.
- Do not invent capabilities.
- Keep steps concrete.
- Do not use markdown.
"""


def create_plan(goal: str) -> list[str]:
    response = chat(
        model=MODEL,
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

    try:
        data = json.loads(raw)
        steps = data.get("steps", [])

        if isinstance(steps, list):
            return [
                str(step).strip()
                for step in steps
                if str(step).strip()
            ]

    except json.JSONDecodeError:
        pass

    return [goal]