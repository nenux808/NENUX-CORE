from tools.filesystem import (
    list_files,
    read_file,
    write_file,
)

from tools.python_tool import run_python
from tools.web_search import web_search
from tools.web_fetch import web_fetch
from memory.document_index import (
    index_document,
    index_workspace_documents,
    search_documents,
)
from tools.windows_control import (
    list_chrome_profiles,
    open_chrome_url,
    open_youtube_search,
    set_default_chrome_profile,
)
from tools.windows_desktop_control import (
    chrome_tab_control,
    focus_chrome,
    inspect_drive,
    media_control,
    open_chrome,
    open_gmail,
    open_vscode,
    open_file_explorer,
    youtube_media_control,
)

from core.permissions import request_permission
from memory.database import log_action


TOOL_REGISTRY = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_python": run_python,
    "web_search": web_search,
    "web_fetch": web_fetch,
    "index_document": index_document,
    "index_workspace_documents": index_workspace_documents,
    "search_documents": search_documents,
    "list_chrome_profiles": list_chrome_profiles,
    "open_chrome_url": open_chrome_url,
    "open_youtube_search": open_youtube_search,
    "set_default_chrome_profile": set_default_chrome_profile,
    "media_control": media_control,
    "open_chrome": open_chrome,
    "focus_chrome": focus_chrome,
    "inspect_drive": inspect_drive,
    "chrome_tab_control": chrome_tab_control,
    "open_gmail": open_gmail,
    "open_vscode": open_vscode,
    "open_file_explorer": open_file_explorer,
    "youtube_media_control": youtube_media_control,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        result = {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

        log_action(tool_name, arguments, result, False)
        return result

    approved = request_permission(tool_name, arguments)

    if not approved:
        result = {
            "success": False,
            "error": "Execution was not approved."
        }

        log_action(tool_name, arguments, result, False)
        return result

    try:
        result = tool(**arguments)

    except TypeError as exc:
        result = {
            "success": False,
            "error": f"Invalid arguments: {exc}"
        }

    except Exception as exc:
        result = {
            "success": False,
            "error": str(exc)
        }

    log_action(tool_name, arguments, result, True)

    return result