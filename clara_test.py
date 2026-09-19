"""One-shot Clara -> NENUX Core integration smoke test."""

import tempfile
from pathlib import Path

from main import process_user_request
from memory.database import get_recent_messages, init_database
from memory.semantic_memory import init_semantic_memory
from interface.microphone import record_wav
from interface.speech_to_text import FasterWhisperSTT
from interface.wake_word import extract_wake_command


def main():
    init_database()
    init_semantic_memory()

    print("CLARA -> NENUX CORE integration test")
    print("Speak after recording starts. You have 5 seconds.")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = Path(temp_dir) / "clara_core_test.wav"

        print("[VOICE] Recording...")
        record_wav(audio_path)
        print("[VOICE] Recording complete.")
        print("[VOICE] Transcribing...")

        transcript = FasterWhisperSTT().transcribe_file(audio_path)
        print(f"\nYOU > {transcript or '[no speech]'}")

        if not transcript:
            return

        command = extract_wake_command(transcript)

        if command is None:
            print("[WAKE] Clara was not addressed.")
            return

        if not command:
            print("[WAKE] Clara activated, but no command was provided.")
            return

        print("[WAKE] Clara activated.")
        print(f"[COMMAND] {command}")
        print("[CORE] Processing command...")

        history = get_recent_messages()
        reply, status, _ = process_user_request(
            command,
            history,
        )

        print(f"\nCLARA > {reply}")
        print(f"[STATUS] {status.upper()}")


if __name__ == "__main__":
    main()
