"""Central configuration for the NENUX Core runtime.

Single source of truth for models, paths, limits, voice, and sandbox policy.
Environment overrides allow model/runtime changes without editing code.
"""

import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip() or default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Identity
CORE_NAME = "NENUX Core"
CORE_VERSION = "0.11-dev"
NODE_NAME = _env("NENUX_NODE", "TITANX")

# Backward-compatible aliases retained for older v0.11 modules/scripts.
AGENT_NAME = CORE_NAME
VERSION = CORE_VERSION

# Models
CHAT_MODEL = _env("NENUX_MODEL", "qwen3:4b-instruct")
MODEL = CHAT_MODEL
PLANNER_MODEL = _env("NENUX_PLANNER_MODEL", CHAT_MODEL)
EVALUATOR_MODEL = _env("NENUX_EVALUATOR_MODEL", CHAT_MODEL)
EMBED_MODEL = _env("NENUX_EMBED_MODEL", "nomic-embed-text")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(
    os.environ.get("NENUX_WORKSPACE", str(PROJECT_ROOT / "workspace"))
).resolve()
MEMORY_DIR = PROJECT_ROOT / "memory"
DB_PATH = Path(
    os.environ.get("NENUX_DB_PATH", str(MEMORY_DIR / "nenux_memory.db"))
).resolve()
CORE_IDENTITY_FILE = MEMORY_DIR / "core_identity.json"
USER_PROFILE_FILE = MEMORY_DIR / "user_profile.json"

# Agent loop / memory
MAX_AGENT_STEPS = _env_int("NENUX_MAX_STEPS", 15)
MAX_CONSECUTIVE_FAILURES = _env_int("NENUX_MAX_FAILURES", 3)
HISTORY_MESSAGE_LIMIT = _env_int("NENUX_HISTORY_LIMIT", 12)
SEMANTIC_MEMORY_LIMIT = _env_int("NENUX_SEMANTIC_LIMIT", 5)
SEMANTIC_SEARCH_LIMIT = SEMANTIC_MEMORY_LIMIT
SEMANTIC_MIN_SCORE = _env_float("NENUX_SEMANTIC_MIN_SCORE", 0.25)

# Python execution sandbox
PYTHON_TIMEOUT_SECONDS = _env_int("NENUX_PY_TIMEOUT", 15)
PYTHON_CPU_SECONDS = _env_int("NENUX_PY_CPU", 10)
PYTHON_MEMORY_MB = _env_int("NENUX_PY_MEMORY_MB", 512)
PYTHON_FSIZE_MB = _env_int("NENUX_PY_FSIZE_MB", 32)
PYTHON_MAX_PROCESSES = _env_int("NENUX_PY_MAX_PROCS", 64)
PYTHON_OUTPUT_LIMIT = _env_int("NENUX_PY_OUTPUT_LIMIT", 10000)
PYTHON_BLOCK_NETWORK = _env_bool("NENUX_PY_BLOCK_NETWORK", True)
PYTHON_ENV_ALLOWLIST = (
    "PATH",
    "LANG",
    "LC_ALL",
    "TZ",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
)

# Local speech-to-text defaults. CPU/int8 keeps GPU memory available to Ollama.
STT_MODEL = _env("NENUX_STT_MODEL", "small.en")
STT_DEVICE = _env("NENUX_STT_DEVICE", "cpu")
STT_COMPUTE_TYPE = _env("NENUX_STT_COMPUTE", "int8")

MICROPHONE_SAMPLE_RATE = 16000
MICROPHONE_CHANNELS = 1
MICROPHONE_RECORD_SECONDS = 5
MICROPHONE_CHUNK_SECONDS = 0.1
MICROPHONE_START_TIMEOUT_SECONDS = 5.0
MICROPHONE_MAX_UTTERANCE_SECONDS = 20.0
MICROPHONE_SILENCE_SECONDS = 1.0
MICROPHONE_SPEECH_RMS_THRESHOLD = 0.002
MICROPHONE_NOISE_CALIBRATION_SECONDS = 0.6
MICROPHONE_NOISE_MULTIPLIER = 1.8
MICROPHONE_MAX_ADAPTIVE_THRESHOLD = 0.008
MICROPHONE_PRE_ROLL_SECONDS = 0.3
MICROPHONE_WEBRTC_VAD_MODE = 3
MICROPHONE_WEBRTC_FRAME_MS = 20
MICROPHONE_MIN_VOICED_RATIO = 0.35
MICROPHONE_MIN_UTTERANCE_SECONDS = 0.35
VOICE_SESSION_MAX_MESSAGES = 10

VOICE_ASSISTANT_NAME = "Clara"
VOICE_WAKE_PHRASE = "hey clara"
VOICE_WAKE_ALIASES = (
    "hey clara",
    "hey cara",
    "hey kara",
    "hey clera",
    "hey claraa",
)
STT_INITIAL_PROMPT = ""
STT_HOTWORDS = "Clara NENUX pause resume unpause mute unmute volume"
VOICE_SESSION_FOLLOWUP_TIMEOUT_SECONDS = 15.0

CLARA_STYLE_PROMPT = (
    "You are Clara, the conversational voice interface for NENUX Core. "
    "Your name is Clara. NENUX Core is the system you represent, not your name. "
    "If asked your name, answer Clara. "
    "For voice replies, be natural, direct, and brief: usually one to three sentences "
    "unless the user explicitly asks for detail. Avoid filler, excessive enthusiasm, "
    "emoji-heavy wording, and long introductions. "
    "If the user's speech appears incomplete, garbled, contradictory, or cut off, "
    "do not invent the missing meaning; ask one short clarification question instead. "
    "For simple acknowledgements, answer simply. "
    "Do not pretend to be human; you are Clara, an AI interface for NENUX Core."
)

# Kokoro neural voice defaults.
CLARA_TTS_VOICE = "af_heart"
CLARA_TTS_SPEED = 1.0
CLARA_TTS_SAMPLE_RATE = 24000
