import json
from ollama import chat


MODEL = "qwen3:4b-instruct"


EVALUATOR_PROMPT = """
You are the execution evaluator for NENUX Core.

Your job is to determine whether each PLANNED STEP was actually carried out.

IMPORTANT DISTINCTION:

STEP COMPLETION and TOOL SUCCESS are NOT the same thing.

Example:

Planned step:
"Execute broken_test.py"

If run_python was actually called on broken_test.py,
then that step is COMPLETED even if the program itself returned an error.

The execution failure is evidence needed for later diagnostic or recovery steps.

Use these meanings:

completed:
- The planned action was actually carried out.
- This may include an action whose tool result itself contained an expected error.
- Example: executing a broken script successfully fulfills the step "execute the broken script."

failed:
- The planned action could not actually be carried out.
- Example: execution was denied, the tool was unavailable, the target file did not exist,
  or the requested action could not be performed.

pending:
- There is not enough evidence that the planned action happened.

RECOVERY WORKFLOW RULES:

For tasks like:

1. execute broken code
2. inspect the error
3. repair the code
4. execute again
5. verify the fixed result

the initial failed program execution should normally count as:

STEP STATUS = completed

because the execution DID happen.

Do NOT mark a step failed merely because the program being tested produced an error.

Instead, evaluate whether the action described in the step actually occurred.

Examples:

Step:
"Execute broken_test.py"

Evidence:
run_python called for broken_test.py, return_code=1

Status:
completed

Reason:
The script was executed and produced a real failure result.

---

Step:
"Read the error message"

Evidence:
stderr contains a traceback and NameError

Status:
completed

---

Step:
"Modify broken_test.py"

Evidence:
write_file succeeded

Status:
completed

---

Step:
"Execute the modified script again"

Evidence:
a later run_python succeeded

Status:
completed

---

Step:
"Verify Result = 42"

Evidence:
stdout contains Result = 42

Status:
completed

MEMORY TASK RULE

If a planned step explicitly asks to answer from long-term memory,
tool execution is NOT required.

For a memory-retrieval step, a relevant final answer supported by
stored memory may be sufficient evidence that the step completed.

Do not mark a memory-only step pending merely because tool_trace is empty.

RULES:

1. Judge whether the planned action happened.
2. Base decisions primarily on actual TOOL RESULTS.
3. Do not trust unsupported claims in the final answer.
4. Reading source code is not proof of execution.
5. A failed program run can still prove that the execution step happened.
6. Mark "failed" only if the planned action itself could not be performed.
7. Mark "pending" if there is insufficient evidence.
8. Later successful recovery may complete the overall task.
9. Do not penalize a recovery task merely because the initial broken program failed as expected.

Return ONLY valid JSON.

Format:

{
  "steps": [
    {
      "step_id": 1,
      "status": "completed",
      "reason": "The script was executed and returned a real NameError."
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

        data, _ = decoder.raw_decode(
            raw[start:]
        )

        steps = data.get(
            "steps",
            []
        )

        if isinstance(steps, list):
            return steps

    except (
        json.JSONDecodeError,
        ValueError
    ):
        pass

    return []
