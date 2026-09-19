"""Central configuration for the NENUX Core runtime."""

CORE_NAME = "NENUX Core"
CORE_VERSION = "0.11-dev"
NODE_NAME = "TITANX"

CHAT_MODEL = "qwen3:4b-instruct"
EMBED_MODEL = "nomic-embed-text"

MAX_AGENT_STEPS = 15
SEMANTIC_MEMORY_LIMIT = 5
PYTHON_TIMEOUT_SECONDS = 15

# Local speech-to-text defaults. CPU/int8 keeps GPU memory available to Ollama.
STT_MODEL = "small.en"
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"

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
STT_HOTWORDS = "Clara NENUX"
VOICE_SESSION_FOLLOWUP_TIMEOUT_SECONDS = 15.0

# Clara response style is kept separate from the Core reasoning/tool policy.
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

# Kokoro neural voice defaults. af_heart is the first Clara candidate.
CLARA_TTS_VOICE = "af_heart"
CLARA_TTS_SPEED = 1.0
CLARA_TTS_SAMPLE_RATE = 24000
