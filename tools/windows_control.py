"""Narrow Windows/Chrome control tools for NENUX Core."""

import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from memory.database import remember, recall


DEFAULT_PROFILE_KEY = "chrome_default_profile"


def _chrome_user_data_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA", "").strip()
    if not local:
        raise RuntimeError("LOCALAPPDATA is not available.")
    return Path(local) / "Google" / "Chrome" / "User Data"


def _find_chrome_executable() -> Path:
    candidates = []

    local = os.environ.get("LOCALAPPDATA", "").strip()
    program_files = os.environ.get("PROGRAMFILES", "").strip()
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "").strip()

    if program_files:
        candidates.append(
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )
    if program_files_x86:
        candidates.append(
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )
    if local:
        candidates.append(
            Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError("Google Chrome executable was not found.")


def _load_profile_info() -> dict:
    user_data = _chrome_user_data_dir()
    local_state = user_data / "Local State"

    if not local_state.is_file():
        return {}

    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return (
        data.get("profile", {})
        .get("info_cache", {})
    )


def list_chrome_profiles() -> dict:
    """List existing Chrome profiles without exposing cookies or history."""
    user_data = _chrome_user_data_dir()

    if not user_data.is_dir():
        return {
            "success": False,
            "error": f"Chrome user data directory was not found: {user_data}",
        }

    info_cache = _load_profile_info()
    saved_default = recall(DEFAULT_PROFILE_KEY)
    profiles = []

    candidate_dirs = []

    default_dir = user_data / "Default"
    if default_dir.is_dir():
        candidate_dirs.append(default_dir)

    candidate_dirs.extend(
        sorted(
            path
            for path in user_data.glob("Profile *")
            if path.is_dir()
        )
    )

    seen = set()

    for path in candidate_dirs:
        directory = path.name
        if directory in seen:
            continue
        seen.add(directory)

        info = info_cache.get(directory, {})
        profiles.append(
            {
                "directory": directory,
                "name": info.get("name") or directory,
                "email": info.get("user_name") or "",
                "is_default": directory == saved_default,
            }
        )

    return {
        "success": True,
        "profiles": profiles,
        "saved_default": saved_default,
    }


def _resolve_profile_selector(selector: str, profiles: list[dict]) -> str | None:
    normalized = str(selector).strip().lower()
    if not normalized:
        return None

    ordinal_map = {
        "first": 0,
        "1st": 0,
        "one": 0,
        "second": 1,
        "2nd": 1,
        "two": 1,
        "third": 2,
        "3rd": 2,
        "three": 2,
        "fourth": 3,
        "4th": 3,
        "fifth": 4,
        "5th": 4,
        "sixth": 5,
        "6th": 5,
    }

    if normalized in ordinal_map:
        index = ordinal_map[normalized]
        if index < len(profiles):
            return profiles[index].get("directory")
        return None

    for profile in profiles:
        candidates = {
            str(profile.get("directory", "")).strip().lower(),
            str(profile.get("name", "")).strip().lower(),
            str(profile.get("email", "")).strip().lower(),
        }
        if normalized in candidates:
            return profile.get("directory")

    return None


def set_default_chrome_profile(profile_directory: str) -> dict:
    """Remember which existing Chrome profile Clara should use by default."""
    profile_result = list_chrome_profiles()
    if not profile_result.get("success"):
        return profile_result

    selected = _resolve_profile_selector(
        profile_directory,
        profile_result.get("profiles", []),
    )

    if not selected:
        return {
            "success": False,
            "error": f"Chrome profile does not exist: {profile_directory}",
            "profiles": profile_result.get("profiles", []),
        }

    remember(DEFAULT_PROFILE_KEY, selected)

    return {
        "success": True,
        "profile_directory": selected,
    }


def _validate_public_url(url: str) -> str:
    url = str(url).strip()
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only valid HTTP(S) URLs may be opened.")

    return url


def open_chrome_url(
    url: str,
    profile_directory: str | None = None,
) -> dict:
    """Open an HTTP(S) URL in an existing Chrome profile."""
    url = _validate_public_url(url)
    chrome = _find_chrome_executable()
    profile_result = list_chrome_profiles()

    if not profile_result.get("success"):
        return profile_result

    profiles = profile_result.get("profiles", [])
    valid_directories = {
        item["directory"]
        for item in profiles
    }

    selector = (profile_directory or "").strip()
    selected = (
        _resolve_profile_selector(selector, profiles)
        if selector
        else profile_result.get("saved_default")
    )

    if not selected:
        if len(profiles) == 1:
            selected = profiles[0]["directory"]
        else:
            return {
                "success": True,
                "opened": False,
                "needs_profile_selection": True,
                "profiles": profiles,
                "message": "Multiple Chrome profiles are available. Ask the user which one to use.",
            }

    if selected not in valid_directories:
        return {
            "success": False,
            "error": f"Chrome profile does not exist: {selected}",
            "profiles": profiles,
        }

    subprocess.Popen(
        [
            str(chrome),
            f"--profile-directory={selected}",
            "--ignore-profile-directory-if-not-exists",
            url,
        ],
        close_fds=True,
    )

    return {
        "success": True,
        "opened": True,
        "profile_directory": selected,
        "url": url,
    }
