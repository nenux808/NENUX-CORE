"""Continuous Clara voice interface for NENUX Core."""

import tempfile
from pathlib import Path

from config import VOICE_ASSISTANT_NAME
from interface.microphone import record_wav
from interface.neural_tts import KokoroTTS
from interface.session import append_session_turn
from interface.speech_to_text import FasterWhisperSTT
from interface.wake_word import extract_wake_command
from main import process_user_request
from memory.database import init_database
from memory.semantic_memory import init_semantic_memory


STOP_COMMANDS = {
    "stop listening",
    "stop",
    "goodbye",
    "go offline",
    "exit",
    "quit",
}


def is_stop_command(command: str) -> bool:
    """Return True when Clara was explicitly asked to end the voice session."""
    normalized = command.strip().lower().rstrip(" .!?")
    return normalized in STOP_COMMANDS


def main():
    init_database()
    init_semantic_memory()

    stt = FasterWhisperSTT()
    tts = KokoroTTS()
    session_history: list[dict] = []

    print("=" * 56)
    print("              CLARA CONTINUOUS VOICE MODE")
    print("                 NENUX CORE v0.11-dev")
    print("=" * 56)
    print("Say 'Hey Clara' followed by your request.")
    print("Say 'Hey Clara, stop listening' to exit.")
    print("Press Ctrl+C at any time to stop.\n")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "clara_turn.wav"

            while True:
                print("[VOICE] Listening...")
                record_wav(audio_path)
                print("[VOICE] Transcribing...")

                transcript = stt.transcribe_file(audio_path)
                print(f"YOU > {transcript or '[no speech]'}")

                if not transcript:
                    continue

                command = extract_wake_command(transcript)

                if command is None:
                    print("[WAKE] Clara was not addressed.\n")
                    continue

                if not command:
                    print("[WAKE] Clara activated, but no command was provided.\n")
                    continue

                print("[WAKE] Clara activated.")
                print(f"[COMMAND] {command}")

                if is_stop_command(command):
                    reply = "Okay, I'll stop listening."
                    print(f"CLARA > {reply}")
                    tts.speak(reply)
                    break

                print("[CORE] Processing command...")
                reply, status, _ = process_user_request(
                    command,
                    session_history,
                    interface_name=VOICE_ASSISTANT_NAME,
                )

                session_history = append_session_turn(
                    session_history,
                    command,
                    reply,
                )

                print(f"\nCLARA > {reply}")
                print(f"[STATUS] {status.upper()}")
                print("[VOICE] Speaking response...")
                tts.speak(reply)
                print()

    except KeyboardInterrupt:
        print("\n[VOICE] Clara stopped.")


if __name__ == "__main__":
    main()
