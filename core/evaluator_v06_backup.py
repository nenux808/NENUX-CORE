import json
from ollama import chat


MODEL = "qwen3:4b-instruct"


EVALUATOR_PROMPT = """
You are the execution evaluator for NENUX Core.

Your job is to determine whether planned task steps were ACTUALLY completed.

You will receive:
- the original goal
- planned steps
- real tool execution results
- the agent's final response

RULES:

1. Only mark a step "completed" when there is clear evidence it happened.
2. Successful tool results are strong evidence.
3. Reading source code is NOT proof that code executed.
4. If execution failed, mark the related step "failed".
5. If there is insufficient evidence, mark the step "pending".
6. Do not trust unsupported claims from the agent.
7. Base decisions primarily on actual TOOL RESULTS.
8. A run_python result with success=true and return_code=0 is evidence of successful execution.
9. stdout may be used to verify expected results.

Return ONLY valid JSON.

Format:

{
  "steps": [
    {
      "step_id": 1,
      "status": "completed",
      "reason": "Evidence explaining the decision"
    }
  ]
}

Allowed statuses:
- completed
- failed
- pending
"""


def evaluate_steps(
    goal: str,
    planned_steps: list,
    tool_trace: list,
    final_response: str
) -> list:

    payload = {
        "goal": goal,
        "planned_steps": planned_steps,
        "tool_trace": tool_trace,
        "final_response": final_response
    }

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": EVALUATOR_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2
                )
            }
        ]
    )

    raw = response.message.content.strip()

    decoder = json.JSONDecoder()

    try:
        start = raw.find("{")

        if start == -1:
            return []

        data, _ = decoder.raw_decode(raw[start:])

        steps = data.get("steps", [])

        if isinstance(steps, list):
            return steps

    except (json.JSONDecodeError, ValueError):
        pass

    return []
