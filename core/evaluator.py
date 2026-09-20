import json
from ollama import chat

from config import CHAT_MODEL


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
10. Tool evidence must match the planned action. A web_search result does NOT prove that list_files or read_file occurred. A read_file result does NOT prove execution occurred.
11. Never reinterpret a planned filesystem step as a web-retrieval step after the fact. If the planned action was not actually performed, mark it pending or failed.
12. For a planned web-retrieval step, require a successful web_search result and ensure the final answer does not assert facts absent from the retrieved evidence.

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
        model=CHAT_MODEL,
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
            return _enforce_tool_action_matching(
                planned_steps,
                tool_trace,
                steps,
            )

    except (
        json.JSONDecodeError,
        ValueError
    ):
        pass

    return []



def _enforce_tool_action_matching(
    planned_steps: list,
    tool_trace: list,
    evaluation: list,
) -> list:
    """Prevent model evaluation from crediting a step to the wrong tool."""
    used_tools = {
        entry.get("tool")
        for entry in tool_trace
        if isinstance(entry, dict)
    }

    evaluation_map = {
        int(item.get("step_id")): item
        for item in evaluation
        if isinstance(item, dict) and str(item.get("step_id", "")).isdigit()
    }

    for step in planned_steps:
        step_id = int(step.get("step_id"))
        description = str(step.get("description", "")).lower()
        required_tool = None

        if "media_control" in description:
            required_tool = "media_control"
        elif "open_chrome" in description or "open google chrome" in description:
            required_tool = "open_chrome"
        elif "chrome_tab_control" in description:
            required_tool = "chrome_tab_control"
        elif "focus_chrome" in description:
            required_tool = "focus_chrome"
        elif "open_gmail" in description:
            required_tool = "open_gmail"
        elif "open_vscode" in description or "open visual studio code" in description:
            required_tool = "open_vscode"
        elif "set_default_chrome_profile" in description or "set the selected chrome profile as default" in description:
            required_tool = "set_default_chrome_profile"
        elif "list_chrome_profiles" in description or "list available local chrome profiles" in description:
            required_tool = "list_chrome_profiles"
        elif "open_chrome_url" in description or "open the verified youtube video" in description:
            required_tool = "open_chrome_url"
        elif "index_workspace_documents" in description or "index all supported workspace documents" in description:
            required_tool = "index_workspace_documents"
        elif "index_document" in description or "index the document" in description:
            required_tool = "index_document"
        elif "search_documents" in description or "search the indexed workspace documents" in description:
            required_tool = "search_documents"
        elif "web_fetch" in description or "fetch " in description or "fetch the" in description:
            required_tool = "web_fetch"
        elif "web_search" in description or "search the web" in description:
            required_tool = "web_search"
        elif "read the file" in description or "read_file" in description:
            required_tool = "read_file"
        elif "run_python" in description or "execute the python" in description or "execute the script" in description:
            required_tool = "run_python"

        if required_tool == "open_chrome_url" and required_tool in used_tools:
            open_results = [
                entry.get("result", {})
                for entry in tool_trace
                if isinstance(entry, dict) and entry.get("tool") == "open_chrome_url"
            ]
            if not any(
                result.get("success") and result.get("opened")
                for result in open_results
                if isinstance(result, dict)
            ):
                evaluation_map[step_id] = {
                    "step_id": step_id,
                    "status": "pending",
                    "reason": (
                        "Chrome has not opened the requested URL yet; "
                        "profile selection or another launch step is still required."
                    ),
                }
                continue

        if required_tool and required_tool not in used_tools:
            evaluation_map[step_id] = {
                "step_id": step_id,
                "status": "pending",
                "reason": (
                    f"The planned action requires {required_tool}, but that tool "
                    "was not executed during this attempt."
                ),
            }

    return [
        evaluation_map.get(
            int(step.get("step_id")),
            {
                "step_id": int(step.get("step_id")),
                "status": "pending",
                "reason": "No reliable execution evidence.",
            },
        )
        for step in planned_steps
    ]
