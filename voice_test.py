"""One-shot real microphone transcription test for NENUX Core."""

import tempfile
from pathlib import Path

from interface.microphone import record_wav
from interface.speech_to_text import FasterWhisperSTT
from interface.wake_word import extract_wake_command


def main():
    print("NENUX microphone test")
    print("Speak after recording starts. You have 5 seconds.")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = Path(temp_dir) / "nenux_voice_test.wav"

        print("[VOICE] Recording...")
        record_wav(audio_path)
        print("[VOICE] Recording complete.")
        print("[VOICE] Transcribing...")

        stt = FasterWhisperSTT()
        transcript = stt.transcribe_file(audio_path)

        if transcript:
            print(f"\nYOU > {transcript}")

            command = extract_wake_command(transcript)

            if command is None:
                print("[WAKE] Clara was not addressed.")
            elif command:
                print(f"[WAKE] Clara activated.")
                print(f"[COMMAND] {command}")
            else:
                print("[WAKE] Clara activated. Waiting for a command.")
        else:
            print("\n[VOICE] No speech was detected.")


if __name__ == "__main__":
    main()
