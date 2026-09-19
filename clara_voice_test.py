"""Audition candidate neural voices for Clara."""

from interface.neural_tts import KokoroTTS

SAMPLE = (
    "Hey, I'm Clara. I'm here and ready. "
    "What would you like to work on?"
)

VOICES = ("af_heart", "af_bella", "af_sarah")


def main():
    print("Clara neural voice audition")
    for voice in VOICES:
        print(f"\n[VOICE] {voice}")
        KokoroTTS(voice=voice).speak(SAMPLE)
        input("Press Enter for the next voice...")


if __name__ == "__main__":
    main()
