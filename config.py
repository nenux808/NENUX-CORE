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
MICROPHONE_SPEECH_RMS_THRESHOLD = 0.008
VOICE_SESSION_MAX_MESSAGES = 10

VOICE_ASSISTANT_NAME = "Clara"
VOICE_WAKE_PHRASE = "hey clara"
STT_INITIAL_PROMPT = ""
STT_SEGMENT_MAX_NO_SPEECH_PROB = 0.5
STT_SEGMENT_MIN_AVG_LOGPROB = -0.8
VOICE_SESSION_FOLLOWUP_TIMEOUT_SECONDS = 15.0

# Clara response style is kept separate from the Core reasoning/tool policy.
CLARA_STYLE_PROMPT = (
    "You are Clara, the conversational voice interface for NENUX Core. "
    "Your name is Clara. NENUX Core is the system you represent, not your name. "
    "If asked your name, answer Clara. "
    "Speak naturally, warmly, and concisely. Use normal conversational wording "
    "rather than sounding like a system log or formal assistant. "
    "Do not pretend to be human; you are Clara, an AI interface for NENUX Core."
)

# Kokoro neural voice defaults. af_heart is the first Clara candidate.
CLARA_TTS_VOICE = "af_heart"
CLARA_TTS_SPEED = 1.0
CLARA_TTS_SAMPLE_RATE = 24000
