SAFE_TOOLS = {
    "list_files",
    "read_file",
    "web_search",
    "web_fetch",
}

REVIEW_TOOLS = {
    "write_file",
    "run_python",
}

BLOCKED_TOOLS = {
    "run_command",
    "delete_file",
    "network_request",
}


def get_permission_level(tool_name: str) -> str:
    if tool_name in SAFE_TOOLS:
        return "safe"

    if tool_name in REVIEW_TOOLS:
        return "review"

    if tool_name in BLOCKED_TOOLS:
        return "blocked"

    return "blocked"


def request_permission(tool_name: str, arguments: dict) -> bool:
    level = get_permission_level(tool_name)

    if level == "safe":
        return True

    if level == "blocked":
        print(f"\n[BLOCKED] Tool not permitted: {tool_name}")
        return False

    print("\n" + "=" * 50)
    print("NENUX PERMISSION REQUEST")
    print("=" * 50)
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")
    print("=" * 50)

    answer = input("Approve execution? [y/N]: ").strip().lower()

    return answer in {"y", "yes"}