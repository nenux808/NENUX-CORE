"""Whitelisted Windows desktop controls for NENUX Core."""

import ctypes
import os
import shutil
import subprocess
from ctypes import wintypes
from pathlib import Path

from tools.windows_control import open_chrome_url


user32 = ctypes.WinDLL("user32", use_last_error=True)

KEYEVENTF_KEYUP = 0x0002

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_TAB = 0x09
VK_W = 0x57

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
    found = []

    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def enum_callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        if _window_class(hwnd) == "Chrome_WidgetWin_1":
            length = user32.GetWindowTextLengthW(hwnd)
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
            found.append((hwnd, title_buffer.value))

        return True

    user32.EnumWindows(enum_callback, 0)

    if not found:
        return {
            "success": False,
            "error": "No visible Chrome window was found.",
        }

    hwnd, title = found[0]

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)

    user32.SetForegroundWindow(hwnd)

    return {
        "success": True,
        "title": title,
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


def open_gmail(profile_directory: str | None = None) -> dict:
    """Open Gmail in the selected/default Chrome profile."""
    return open_chrome_url(
        "https://mail.google.com/",
        profile_directory=profile_directory,
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
