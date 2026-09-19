from core.tasks import (
    get_latest_active_task,
    get_task_steps,
)


def find_resumable_task():

    task = get_latest_active_task()

    if not task:
        return None

    steps = get_task_steps(
        task["id"]
    )

    print("\n" + "=" * 56)
    print("             UNFINISHED TASK FOUND")
    print("=" * 56)

    print(f"Task #{task['id']}")
    print(f"Goal: {task['goal']}")

    print("\nSaved progress:")

    for index, step in enumerate(
        steps,
        start=1
    ):

        status = step["status"]

        if status == "completed":
            icon = "✓"
        elif status == "failed":
            icon = "✗"
        elif status == "in_progress":
            icon = "~"
        else:
            icon = " "

        print(
            f"[{icon}] {index}. "
            f"{step['description']} "
            f"({status})"
        )

    print("=" * 56)

    answer = input(
        "Resume this task? [Y/n]: "
    ).strip().lower()

    if answer in {"n", "no"}:
        return None

    step_records = []

    for index, step in enumerate(
        steps,
        start=1
    ):
        step_records.append({
            "step_id": index,
            "database_id": step["id"],
            "description": step["description"],
            "original_status": step["status"]
        })

    return {
        "task_id": task["id"],
        "goal": task["goal"],
        "step_records": step_records
    }


def build_resume_prompt(
    goal: str,
    step_records: list
):

    completed = []
    remaining = []

    for record in step_records:

        status = record.get(
            "original_status",
            "pending"
        )

        description = record["description"]

        if status == "completed":
            completed.append(description)
        else:
            remaining.append(description)

    completed_text = (
        "\n".join(
            f"- {item}"
            for item in completed
        )
        if completed
        else "- None"
    )

    remaining_text = (
        "\n".join(
            f"- {item}"
            for item in remaining
        )
        if remaining
        else "- None"
    )

    return f"""
RESUMED TASK

Original goal:
{goal}

Previously completed steps:
{completed_text}

Remaining or retry-required steps:
{remaining_text}

Continue this existing task.

Do not redo previously completed work unless it is genuinely necessary.

Use fresh tool evidence for any work you perform now.

Complete the remaining steps and verify the final result.
""".strip()
