from pathlib import Path, PureWindowsPath

from config import WORKSPACE


WORKSPACE.mkdir(parents=True, exist_ok=True)


def _safe_path(relative_path: str = ".") -> Path:
    """Resolve a path inside the workspace, or refuse.

    Normalises separators first so the guard behaves identically on POSIX
    and Windows. Without this, "..\\main.py" is a traversal on Windows but
    an ordinary filename on Linux.
    """
    if not isinstance(relative_path, str):
        raise PermissionError("Access denied: path must be a string.")

    candidate = relative_path.replace("\\", "/").strip()

    if not candidate:
        candidate = "."

    # The tool is already jailed inside WORKSPACE. Accept a redundant
    # "workspace/" prefix as a harmless alias instead of treating it as
    # a nested directory that usually does not exist.
    lowered = candidate.lower()
    if lowered == "workspace":
        candidate = "."
    elif lowered.startswith("workspace/"):
        candidate = candidate[len("workspace/"):] or "."

    if candidate.startswith("/") or PureWindowsPath(candidate).is_absolute():
        raise PermissionError(
            "Access denied: absolute paths are not permitted."
        )

    if any(part == ".." for part in candidate.split("/")):
        raise PermissionError(
            "Access denied: parent directory traversal is not permitted."
        )

    target = (WORKSPACE / candidate).resolve()

    try:
        target.relative_to(WORKSPACE)
    except ValueError:
        raise PermissionError(
            "Access denied: NENUX Core may only access its workspace."
        )

    return target


def list_files(path: str = ".") -> dict:
    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {path}"
        }

    if not target.is_dir():
        return {
            "success": False,
            "error": f"Not a directory: {path}"
        }

    items = []

    for item in sorted(target.iterdir()):
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None
        })

    return {
        "success": True,
        "path": str(target.relative_to(WORKSPACE)),
        "items": items
    }


def read_file(path: str) -> dict:
    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"File does not exist: {path}"
        }

    if not target.is_file():
        return {
            "success": False,
            "error": f"Not a file: {path}"
        }

    try:
        content = target.read_text(encoding="utf-8")

        return {
            "success": True,
            "path": path,
            "content": content
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "File is not UTF-8 text."
        }


def write_file(path: str, content: str) -> dict:
    target = _safe_path(path)

    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(
        content,
        encoding="utf-8"
    )

    return {
        "success": True,
        "path": path,
        "bytes_written": len(content.encode("utf-8"))
    }
