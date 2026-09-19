"""Continuous Clara voice interface for NENUX Core."""

import tempfile
import time
from pathlib import Path

from config import CORE_VERSION, VOICE_ASSISTANT_NAME, VOICE_SESSION_FOLLOWUP_TIMEOUT_SECONDS
from interface.microphone import calibrate_microphone_threshold, record_until_silence
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


def resolve_voice_command(
    transcript: str,
    session_active: bool,
) -> tuple[str | None, bool]:
    """Resolve a transcript into a command and updated session-active state."""
    wake_command = extract_wake_command(transcript)

    if wake_command is not None:
        return wake_command, True

    if session_active:
        return transcript.strip(), True

    return None, False


def main():
    init_database()
    init_semantic_memory()

    stt = FasterWhisperSTT()
    tts = KokoroTTS()
    session_history: list[dict] = []
    session_active = False
    last_activity_at: float | None = None

    print("[VOICE] Calibrating microphone. Keep quiet for a moment...")
    speech_threshold = calibrate_microphone_threshold()
    print(f"[VOICE] Adaptive speech threshold: {speech_threshold:.4f}")

    print("=" * 56)
    print("              CLARA CONTINUOUS VOICE MODE")
    print(f"                 NENUX CORE v{CORE_VERSION}")
    print("=" * 56)
    print("Start with 'Hey Clara' followed by your request.")
    print("After Clara is active, normal follow-up speech does not need the wake phrase.")
    print("Say 'stop listening' to exit the active session.")
    print("Press Ctrl+C at any time to stop.\n")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "clara_turn.wav"

            while True:
                print("[VOICE] Listening...")
                _, speech_detected = record_until_silence(
                    audio_path,
                    speech_threshold=speech_threshold,
                )

                if not speech_detected:
                    print("YOU > [no speech]\n")
                    continue

                print("[VOICE] Transcribing...")
                transcript = stt.transcribe_file(audio_path)
                print(f"YOU > {transcript or '[no speech]'}")

                if not transcript:
                    continue

                if (
                    session_active
                    and last_activity_at is not None
                    and time.monotonic() - last_activity_at
                    > VOICE_SESSION_FOLLOWUP_TIMEOUT_SECONDS
                ):
                    session_active = False
                    print("[SESSION] Follow-up window expired; wake phrase required.")

                command, session_active = resolve_voice_command(
                    transcript,
                    session_active,
                )

                if command is None:
                    print("[WAKE] Clara was not addressed.\n")
                    continue

                if not command:
                    last_activity_at = time.monotonic()
                    print("[WAKE] Clara activated, but no command was provided.\n")
                    continue

                if transcript.strip().lower().startswith("hey clara"):
                    print("[WAKE] Clara activated.")
                else:
                    print("[SESSION] Follow-up accepted.")

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
                last_activity_at = time.monotonic()

                print(f"\nCLARA > {reply}")
                print(f"[STATUS] {status.upper()}")
                print("[VOICE] Speaking response...")
                tts.speak(reply)
                print()

    except KeyboardInterrupt:
        print("\n[VOICE] Clara stopped.")


if __name__ == "__main__":
    main()
