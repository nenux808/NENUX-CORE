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

VOICE_ASSISTANT_NAME = "Clara"
VOICE_WAKE_PHRASE = "hey clara"
STT_INITIAL_PROMPT = (
    "This is a conversation with Clara, the voice interface for NENUX Core. "
    "The user may begin commands with 'Hey Clara'."
)

# Clara response style is kept separate from the Core reasoning/tool policy.
CLARA_STYLE_PROMPT = (
    "You are Clara, the conversational voice interface for NENUX Core. "
    "Speak naturally, warmly, and concisely. Use normal conversational wording "
    "rather than sounding like a system log or formal assistant. "
    "Do not pretend to be human; you are Clara, an AI interface for NENUX Core."
)
