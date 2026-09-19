import json

from ollama import chat

from memory.memory_manager import build_memory_context
from memory.database import (
    init_database,
    save_message,
    get_recent_messages,
)

from tools.registry import execute_tool

from core.planner import create_plan
from core.tasks import (
    create_task,
    complete_task,
    add_step,
    update_step,
)


MODEL = "qwen3:4b-instruct"


SYSTEM_PROMPT = """
You are NENUX Core v0.5 running locally on TITANX.

You are an AI agent operating through the NENUX Core runtime.

You have:
- persistent identity context
- persistent conversation history
- task planning
- tool execution
- permission-controlled actions

CURRENT TOOLS

1. list_files
Arguments:
{
    "path": "relative/path"
}

2. read_file
Arguments:
{
    "path": "relative/path/file.txt"
}

3. write_file
Arguments:
{
    "path": "relative/path/file.txt",
    "content": "text content"
}

4. run_python
Arguments:
{
    "path": "relative/path/script.py"
}

FILESYSTEM RULES

All filesystem operations are restricted to the NENUX workspace.

TOOL PROTOCOL

When you need to use a tool, respond ONLY with valid JSON.

Preferred format:

{
    "action": "tool",
    "tool": "tool_name",
    "arguments": {}
}

Examples:

{
    "action": "tool",
    "tool": "list_files",
    "arguments": {
        "path": "."
    }
}

{
    "action": "tool",
    "tool": "read_file",
    "arguments": {
        "path": "example.txt"
    }
}

{
    "action": "tool",
    "tool": "write_file",
    "arguments": {
        "path": "example.py",
        "content": "print('hello')"
    }
}

{
    "action": "tool",
    "tool": "run_python",
    "arguments": {
        "path": "example.py"
    }
}

Do not wrap tool JSON in markdown.

If you do not need a tool, respond normally.

When a tool result is returned:
- inspect the result
- decide whether another tool is needed
- continue until the task is complete
- never claim success unless the runtime actually returned success

Do not invent:
- file contents
- filesystem results
- execution results
- capabilities

Do not claim capabilities that have not been provided by the runtime.

Be concise, practical, and collaborative.

IMPORTANT:

Execute only ONE tool at a time.

Never return multiple tool calls in the same response.

After requesting one tool, wait for the TOOL RESULT.

Then decide what tool to use next.

Correct sequence:

1. Request write_file
2. Wait for TOOL RESULT
3. Request run_python
4. Wait for TOOL RESULT
5. Give final answer

Never output two JSON objects in one response.

EXECUTION VERIFICATION RULES

If the user asks you to:
- run code
- test code
- execute a script
- verify program output
- confirm that software works

you MUST use the appropriate execution tool.

Reading source code is NOT equivalent to executing it.

Never claim that code ran, passed, worked, or produced an output unless you received
a successful run_python TOOL RESULT proving it.

If you create or modify Python code and the user's goal requires testing it:
1. write_file
2. optionally read_file to inspect it
3. run_python
4. inspect stdout, stderr and return_code
5. only then report success or failure

If execution was not performed, explicitly say it has not yet been executed.
"""


def call_model(messages: list) -> str:
    response = chat(
        model=MODEL,
        messages=messages
    )

    return response.message.content.strip()


def parse_tool_request(response: str):
    response = response.strip()

    decoder = json.JSONDecoder()

    # Try to find and decode the first JSON object
    try:
        start = response.find("{")

        if start == -1:
            return None

        data, _ = decoder.raw_decode(response[start:])

    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    # Preferred format
    if data.get("action") == "tool" and "tool" in data:
        return {
            "action": "tool",
            "tool": data["tool"],
            "arguments": data.get("arguments", {}),
        }

    # Fallback format
    action = data.get("action")

    if action in {
        "list_files",
        "read_file",
        "write_file",
        "run_python",
    }:
        return {
            "action": "tool",
            "tool": action,
            "arguments": data.get("arguments", {}),
        }

    return None


def run_agent(user_input: str, history: list) -> str:
    memory_context = build_memory_context()

    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n\n"
                + memory_context
            )
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    max_steps = 15

    for step_number in range(max_steps):

        response = call_model(messages)

        tool_request = parse_tool_request(response)

        if tool_request is None:
            return response

        tool_name = tool_request["tool"]
        arguments = tool_request.get(
            "arguments",
            {}
        )

        print(
            f"\n[TOOL] {tool_name} "
            f"{json.dumps(arguments, ensure_ascii=False)}"
        )

        result = execute_tool(
            tool_name,
            arguments
        )

        print(
            "[RESULT]",
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )

        messages.append(
            {
                "role": "user",
                "content": (
                    "TOOL RESULT:\n"
                    + json.dumps(
                        result,
                        ensure_ascii=False
                    )
                )
            }
        )

    return (
        "I reached the maximum number of tool steps "
        "for this task."
    )


def create_tracked_task(goal: str):
    task_id = create_task(goal)

    steps = create_plan(goal)

    step_ids = []

    print("\n[TASK PLAN]")

    if not steps:
        steps = [goal]

    for index, step in enumerate(
        steps,
        start=1
    ):
        step_id = add_step(
            task_id,
            step
        )

        step_ids.append(step_id)

        print(
            f"{index}. {step}"
        )

    return task_id, step_ids


def main():
    init_database()

    history = get_recent_messages()

    print("=" * 52)
    print("               NENUX CORE v0.5")
    print("               TITANX NODE")
    print("        MEMORY + PLANNER ONLINE")
    print("=" * 52)

    while True:

        try:

            user_input = input(
                "\nCORE > "
            ).strip()

            if user_input.lower() in {
                "exit",
                "quit",
                "/bye"
            }:
                print(
                    "\nNENUX > Shutting down."
                )
                break

            if not user_input:
                continue

            save_message(
                "user",
                user_input
            )

            task_id, step_ids = (
                create_tracked_task(
                    user_input
                )
            )

            for step_id in step_ids:
                update_step(
                    step_id,
                    "in_progress"
                )

            reply = run_agent(
                user_input,
                history
            )

            for step_id in step_ids:
                update_step(
                    step_id,
                    "completed"
                )

            complete_task(
                task_id
            )

            save_message(
                "assistant",
                reply
            )

            history = get_recent_messages()

            print(
                f"\nNENUX > {reply}"
            )

        except KeyboardInterrupt:

            print(
                "\n\nNENUX > Shutting down."
            )

            break

        except Exception as exc:

            print(
                "\n[NENUX ERROR]"
            )

            print(
                str(exc)
            )


if __name__ == "__main__":
    main()