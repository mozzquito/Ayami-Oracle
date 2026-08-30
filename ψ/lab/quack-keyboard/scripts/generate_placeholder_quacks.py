#!/usr/bin/env python3
"""
Generates rough placeholder "quack-ish" WAV files (stdlib only, no deps) so the
app has something audible to build and test against. These are synthesized
approximations, NOT real duck recordings -- swap them for licensed/CC0 duck
quack samples (e.g. from freesound.org) before shipping a paid product.
"""
import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 22050
OUT_DIR = Path(__file__).resolve().parent.parent / "Resources" / "Sounds"


def synth_quack(duration=0.22, base_freq=340.0, seed=0):
    random.seed(seed)
    n_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        progress = i / n_samples

        # Pitch falls sharply then wobbles -- rough quack contour.
        freq = base_freq * (1.0 - 0.55 * progress) + 15 * math.sin(2 * math.pi * 28 * t)

        # A couple of harmonics stacked on a sawtooth-ish wave for a "buzzy" honk.
        phase = 2 * math.pi * freq * t
        wave_val = (
            0.6 * math.sin(phase)
            + 0.25 * math.sin(2 * phase)
            + 0.15 * math.sin(3 * phase)
        )
        wave_val += (random.random() - 0.5) * 0.25  # texture/noise

        # Fast attack, exponential-ish decay envelope.
        envelope = min(1.0, progress * 18) * math.exp(-3.2 * progress)

        samples.append(max(-1.0, min(1.0, wave_val * envelope)))

    return samples


def write_wav(path: Path, samples):
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        frames = b"".join(struct.pack("<h", int(s * 32767)) for s in samples)
        f.writeframes(frames)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    variations = [
        (0.20, 360.0, 1),
        (0.24, 320.0, 2),
        (0.18, 400.0, 3),
    ]
    for idx, (dur, freq, seed) in enumerate(variations, start=1):
        samples = synth_quack(duration=dur, base_freq=freq, seed=seed)
        out_path = OUT_DIR / f"quack{idx}.wav"
        write_wav(out_path, samples)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
