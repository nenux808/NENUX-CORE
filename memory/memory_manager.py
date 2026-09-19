import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CORE_IDENTITY_FILE = BASE_DIR / "core_identity.json"
USER_PROFILE_FILE = BASE_DIR / "user_profile.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_core_identity() -> dict:
    return load_json(CORE_IDENTITY_FILE)


def get_user_profile() -> dict:
    return load_json(USER_PROFILE_FILE)


def remember_user(key: str, value) -> None:
    profile = get_user_profile()
    profile[key] = value
    save_json(USER_PROFILE_FILE, profile)


def build_memory_context() -> str:
    core = get_core_identity()
    user = get_user_profile()

    return f"""
CORE IDENTITY:
{json.dumps(core, indent=2)}

USER PROFILE:
{json.dumps(user, indent=2)}
"""