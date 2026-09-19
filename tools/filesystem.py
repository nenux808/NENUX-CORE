from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = (PROJECT_ROOT / "workspace").resolve()


def _safe_path(relative_path: str = ".") -> Path:
    target = (WORKSPACE / relative_path).resolve()

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