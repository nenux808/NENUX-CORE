"""Whitelisted Windows desktop controls for NENUX Core."""

import ctypes
import os
import shutil
import subprocess
from ctypes import wintypes
from pathlib import Path

from tools.windows_control import (
    _find_chrome_executable,
    list_chrome_profiles,
    open_chrome_url,
    set_default_chrome_profile,
)


user32 = ctypes.WinDLL("user32", use_last_error=True)

KEYEVENTF_KEYUP = 0x0002

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_TAB = 0x09
VK_W = 0x57
VK_K = 0x4B

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


MEDIA_KEYS = {
    "play_pause": VK_MEDIA_PLAY_PAUSE,
    "pause": VK_MEDIA_PLAY_PAUSE,
    "resume": VK_MEDIA_PLAY_PAUSE,
    "next": VK_MEDIA_NEXT_TRACK,
    "previous": VK_MEDIA_PREV_TRACK,
    "mute": VK_VOLUME_MUTE,
    "unmute": VK_VOLUME_MUTE,
    "volume_down": VK_VOLUME_DOWN,
    "volume_up": VK_VOLUME_UP,
}


def _press_key(vk: int) -> None:
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _press_chord(keys: list[int]) -> None:
    for key in keys:
        user32.keybd_event(key, 0, 0, 0)

    for key in reversed(keys):
        user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)


def _visible_chrome_windows() -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    @callback_type
    def enum_callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        if _window_class(hwnd) != "Chrome_WidgetWin_1":
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
        found.append((hwnd, title_buffer.value))
        return True

    user32.EnumWindows(enum_callback, 0)
    return found


def _focus_window(hwnd: int) -> bool:
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)

    return bool(user32.SetForegroundWindow(hwnd))


def youtube_media_control(action: str) -> dict:
    """Target a visible YouTube Chrome window with YouTube's K shortcut."""
    normalized = str(action).strip().lower().replace(" ", "_")

    if normalized not in {"pause", "resume", "play_pause"}:
        return {
            "success": False,
            "error": "YouTube control currently supports pause/resume/play_pause only.",
        }

    windows = _visible_chrome_windows()
    youtube_windows = [
        (hwnd, title)
        for hwnd, title in windows
        if "youtube" in title.lower()
    ]

    if not youtube_windows:
        return {
            "success": False,
            "error": "No visible YouTube Chrome window was found.",
        }

    hwnd, title = youtube_windows[0]
    focused = _focus_window(hwnd)
    if not focused:
        return {
            "success": False,
            "error": "Found YouTube but could not bring its Chrome window to the foreground.",
            "title": title,
        }

    _press_key(VK_K)

    return {
        "success": True,
        "action": normalized,
        "target": "youtube",
        "focused_title": title,
        "dispatched": True,
        "verified_playback_state": False,
    }


def media_control(action: str) -> dict:
    """Send one approved Windows media/volume key."""
    normalized = str(action).strip().lower().replace(" ", "_")
    vk = MEDIA_KEYS.get(normalized)

    if vk is None:
        return {
            "success": False,
            "error": (
                "Unsupported media action. Allowed: "
                + ", ".join(sorted(MEDIA_KEYS))
            ),
        }

    _press_key(vk)

    return {
        "success": True,
        "action": normalized,
    }


def _window_class(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def focus_chrome() -> dict:
    """Bring a visible Chrome window to the foreground."""
    found = _visible_chrome_windows()

    if not found:
        return {
            "success": False,
            "error": "No visible Chrome window was found.",
        }

    hwnd, title = found[0]
    focused = _focus_window(hwnd)

    return {
        "success": focused,
        "title": title,
        **({} if focused else {"error": "Chrome was found but could not be focused."}),
    }


def chrome_tab_control(action: str) -> dict:
    """Control tabs in the foreground Chrome window using approved shortcuts."""
    normalized = str(action).strip().lower().replace(" ", "_")

    focus_result = focus_chrome()
    if not focus_result.get("success"):
        return focus_result

    if normalized == "next_tab":
        _press_chord([VK_CONTROL, VK_TAB])
    elif normalized == "previous_tab":
        _press_chord([VK_CONTROL, VK_SHIFT, VK_TAB])
    elif normalized == "close_tab":
        _press_chord([VK_CONTROL, VK_W])
    elif normalized == "close_all_tabs":
        _press_chord([VK_CONTROL, VK_SHIFT, VK_W])
    else:
        return {
            "success": False,
            "error": "Unsupported Chrome tab action.",
        }

    return {
        "success": True,
        "action": normalized,
        "focused_title": focus_result.get("title", ""),
    }


def open_chrome() -> dict:
    """Launch Chrome using the saved profile when available."""
    chrome = _find_chrome_executable()
    profile_result = list_chrome_profiles()

    if not profile_result.get("success"):
        return profile_result

    selected = profile_result.get("saved_default")
    args = [str(chrome)]

    if selected:
        args.append(f"--profile-directory={selected}")

    subprocess.Popen(args, close_fds=True)

    return {
        "success": True,
        "opened": True,
        "application": "Google Chrome",
        "profile_directory": selected,
    }


def open_gmail(profile_directory: str | None = None) -> dict:
    """Open Gmail in Chrome, falling back to the first profile if needed."""
    selected = (profile_directory or "").strip() or None

    if selected is None:
        profile_result = list_chrome_profiles()
        if not profile_result.get("success"):
            return profile_result

        selected = profile_result.get("saved_default")

        if not selected:
            profiles = profile_result.get("profiles", [])
            if not profiles:
                return {
                    "success": False,
                    "error": "No Chrome profiles are available.",
                }

            selected = profiles[0]["directory"]
            set_default_chrome_profile(selected)

    return open_chrome_url(
        "https://mail.google.com/",
        profile_directory=selected,
    )


def _find_vscode() -> str | None:
    direct = shutil.which("code")
    if direct:
        return direct

    candidates = []

    local = os.environ.get("LOCALAPPDATA", "").strip()
    program_files = os.environ.get("PROGRAMFILES", "").strip()

    if local:
        candidates.append(
            Path(local) / "Programs" / "Microsoft VS Code" / "Code.exe"
        )

    if program_files:
        candidates.append(
            Path(program_files) / "Microsoft VS Code" / "Code.exe"
        )

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    return None


def open_vscode() -> dict:
    """Launch Visual Studio Code from known installation locations."""
    executable = _find_vscode()

    if not executable:
        return {
            "success": False,
            "error": "Visual Studio Code was not found.",
        }

    subprocess.Popen([executable], close_fds=True)

    return {
        "success": True,
        "opened": True,
        "application": "Visual Studio Code",
    }



def open_file_explorer() -> dict:
    """Launch Windows File Explorer without exposing arbitrary shell access."""
    try:
        subprocess.Popen(
            ["explorer.exe"],
            close_fds=True,
        )
    except OSError as exc:
        return {
            "success": False,
            "error": f"Could not open File Explorer: {exc}",
        }

    return {
        "success": True,
        "opened": True,
        "application": "File Explorer",
    }



def inspect_drive(drive: str, max_items: int = 50) -> dict:
    """Inspect one Windows drive root without recursive traversal or mutation."""
    raw = str(drive).strip().upper().replace("\\", "").replace("/", "")
    if raw.endswith(":"):
        raw = raw[:-1]

    if len(raw) != 1 or not raw.isalpha():
        return {
            "success": False,
            "error": "Drive must be a single Windows drive letter such as C or D.",
        }

    root = Path(f"{raw}:/")
    if not root.exists():
        return {
            "success": False,
            "error": f"Drive does not exist or is unavailable: {raw}:",
        }

    try:
        usage = shutil.disk_usage(root)
    except OSError as exc:
        return {
            "success": False,
            "error": f"Could not read drive usage for {raw}: {exc}",
        }

    items = []
    try:
        for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if len(items) >= max(1, min(int(max_items), 100)):
                break

            try:
                kind = "directory" if entry.is_dir() else "file"
            except OSError:
                kind = "unknown"

            items.append({
                "name": entry.name,
                "type": kind,
            })
    except (OSError, PermissionError) as exc:
        return {
            "success": False,
            "error": f"Could not list drive root {raw}: {exc}",
        }

    return {
        "success": True,
        "drive": f"{raw}:",
        "root": str(root),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "items": items,
        "truncated": len(items) >= max(1, min(int(max_items), 100)),
        "scope": "drive_root_only",
    }
