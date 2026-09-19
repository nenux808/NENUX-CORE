import subprocess
import sys

from tools.filesystem import _safe_path
from config import PYTHON_TIMEOUT_SECONDS


def run_python(path: str) -> dict:
    target = _safe_path(path)

    if not target.exists():
        return {
            "success": False,
            "error": f"Python file does not exist: {path}"
        }

    if target.suffix.lower() != ".py":
        return {
            "success": False,
            "error": "Only .py files may be executed."
        }

    try:
        result = subprocess.run(
            [sys.executable, str(target)],
            capture_output=True,
            text=True,
            timeout=PYTHON_TIMEOUT_SECONDS,
            cwd=str(target.parent)
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-10000:]
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution stopped after {PYTHON_TIMEOUT_SECONDS} seconds."
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }