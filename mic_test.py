"""Interactive microphone diagnostics for NENUX Core."""

import time

import numpy as np
import sounddevice as sd

from config import (
    MICROPHONE_CHANNELS,
    MICROPHONE_SAMPLE_RATE,
    MICROPHONE_WEBRTC_VAD_MODE,
)
from interface.microphone import rms_level, webrtc_voiced_ratio


def main():
    print("=" * 60)
    print("NENUX MICROPHONE DIAGNOSTIC")
    print("=" * 60)

    print(f"Default sounddevice devices: {sd.default.device}")
    print("\nAvailable input devices:")

    devices = sd.query_devices()
    for index, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            marker = ""
            default_input = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else sd.default.device
            if index == default_input:
                marker = "  <-- DEFAULT INPUT"
            print(
                f"[{index}] {device['name']} | "
                f"inputs={device['max_input_channels']} | "
                f"default_sr={device['default_samplerate']}{marker}"
            )

    print("\nNow speak normally for about 8 seconds.")
    print("You should see RMS and VAD increase while speaking.\n")

    chunk_seconds = 0.2
    frames = int(MICROPHONE_SAMPLE_RATE * chunk_seconds)

    for i in range(40):
        audio = sd.rec(
            frames,
            samplerate=MICROPHONE_SAMPLE_RATE,
            channels=MICROPHONE_CHANNELS,
            dtype="int16",
        )
        sd.wait()
        audio = np.asarray(audio, dtype=np.int16)

        rms = rms_level(audio)
        voiced = webrtc_voiced_ratio(
            audio,
            sample_rate=MICROPHONE_SAMPLE_RATE,
            mode=MICROPHONE_WEBRTC_VAD_MODE,
        )

        print(
            f"{i + 1:02d} | RMS={rms:.4f} | "
            f"VAD={voiced:.2f}"
        )

        time.sleep(0.02)


if __name__ == "__main__":
    main()
