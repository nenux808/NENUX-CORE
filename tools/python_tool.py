"""Sandboxed Python execution tool."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from config import (
    PYTHON_BLOCK_NETWORK,
    PYTHON_CPU_SECONDS,
    PYTHON_ENV_ALLOWLIST,
    PYTHON_FSIZE_MB,
    PYTHON_MAX_PROCESSES,
    PYTHON_MEMORY_MB,
    PYTHON_OUTPUT_LIMIT,
    PYTHON_TIMEOUT_SECONDS,
)
from tools.filesystem import _safe_path

try:
    import resource

    RESOURCE_LIMITS_AVAILABLE = True
except ImportError:
    resource = None
    RESOURCE_LIMITS_AVAILABLE = False


NETWORK_BLOCK_SHIM = """
import socket


class NenuxNetworkBlocked(OSError):
    pass


def _blocked(*args, **kwargs):
    raise NenuxNetworkBlocked(
        "Network access is disabled inside the NENUX execution sandbox."
    )


socket.socket = _blocked
socket.create_connection = _blocked
socket.create_server = _blocked
socket.getaddrinfo = _blocked
socket.gethostbyname = _blocked
"""


def _build_child_environment(extra_pythonpath: str | None) -> dict:
    env = {
        name: os.environ[name]
        for name in PYTHON_ENV_ALLOWLIST
        if name in os.environ
    }
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONNOUSERSITE"] = "1"

    if extra_pythonpath:
        env["PYTHONPATH"] = extra_pythonpath

    return env


def _apply_resource_limits() -> None:
    if resource is None:
        return

    def _set(which, soft_limit):
        try:
            hard = resource.getrlimit(which)[1]
            if hard != resource.RLIM_INFINITY:
                soft_limit = min(soft_limit, hard)
            resource.setrlimit(which, (soft_limit, soft_limit))
        except (ValueError, OSError):
            pass

    _set(resource.RLIMIT_CPU, PYTHON_CPU_SECONDS)
    _set(resource.RLIMIT_AS, PYTHON_MEMORY_MB * 1024 * 1024)
    _set(resource.RLIMIT_FSIZE, PYTHON_FSIZE_MB * 1024 * 1024)
    _set(resource.RLIMIT_CORE, 0)

    if hasattr(resource, "RLIMIT_NPROC"):
        _set(resource.RLIMIT_NPROC, PYTHON_MAX_PROCESSES)

    try:
        os.setsid()
    except (AttributeError, OSError):
        pass


def _sandbox_report() -> dict:
    return {
        "timeout_seconds": PYTHON_TIMEOUT_SECONDS,
        "resource_limits": RESOURCE_LIMITS_AVAILABLE,
        "cpu_seconds": PYTHON_CPU_SECONDS if RESOURCE_LIMITS_AVAILABLE else None,
        "memory_mb": PYTHON_MEMORY_MB if RESOURCE_LIMITS_AVAILABLE else None,
        "network_blocked": PYTHON_BLOCK_NETWORK,
        "environment_scrubbed": True,
    }


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _truncate(text: str) -> str:
    if len(text) <= PYTHON_OUTPUT_LIMIT:
        return text
    return text[-PYTHON_OUTPUT_LIMIT:]


def run_python(path: str) -> dict:
    try:
        target = _safe_path(path)
    except PermissionError as exc:
        return {"success": False, "error": str(exc)}

    if not target.exists():
        return {
            "success": False,
            "error": f"Python file does not exist: {path}",
        }

    if not target.is_file():
        return {"success": False, "error": f"Not a file: {path}"}

    if target.suffix.lower() != ".py":
        return {
            "success": False,
            "error": "Only .py files may be executed.",
        }

    shim_dir = None

    try:
        extra_pythonpath = None

        if PYTHON_BLOCK_NETWORK:
            shim_dir = tempfile.mkdtemp(prefix="nenux_sandbox_")
            shim_path = Path(shim_dir) / "sitecustomize.py"
            shim_path.write_text(NETWORK_BLOCK_SHIM, encoding="utf-8")
            extra_pythonpath = shim_dir

        env = _build_child_environment(extra_pythonpath)
        preexec = _apply_resource_limits if RESOURCE_LIMITS_AVAILABLE else None

        result = subprocess.run(
            [sys.executable, str(target)],
            capture_output=True,
            text=True,
            timeout=PYTHON_TIMEOUT_SECONDS,
            cwd=str(target.parent),
            env=env,
            preexec_fn=preexec,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": _truncate(result.stdout),
            "stderr": _truncate(result.stderr),
            "sandbox": _sandbox_report(),
        }

    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "error": (
                f"Execution stopped after {PYTHON_TIMEOUT_SECONDS} seconds "
                "(sandbox wall-clock limit)."
            ),
            "stdout": _truncate(_as_text(exc.stdout)),
            "stderr": _truncate(_as_text(exc.stderr)),
            "sandbox": _sandbox_report(),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "sandbox": _sandbox_report(),
        }

    finally:
        if shim_dir:
            try:
                Path(shim_dir, "sitecustomize.py").unlink(missing_ok=True)
                os.rmdir(shim_dir)
            except OSError:
                pass
