"""Montaje de la pista de voz doblada y del fondo (música/ambiente)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np

from . import media
from .segments import Segment


def build_voice_track(
    segments: list[Segment],
    clips: list[Path | None],
    total_duration: float,
    out: Path,
    max_speed: float = 1.5,
) -> Path:
    """Coloca cada frase en su tiempo; acelera las que no caben hasta `max_speed`."""
    sr = media.SAMPLE_RATE
    track = np.zeros(int(total_duration * sr) + 1, dtype=np.float32)
    overflows = 0

    for i, (seg, clip) in enumerate(zip(segments, clips)):
        if clip is None:
            continue
        next_start = segments[i + 1].start if i + 1 < len(segments) else total_duration
        slot = max(0.2, next_start - seg.start)
        samples = media.decode_mono(clip)
        needed = len(samples) / sr
        if needed > slot * 1.02:
            speed = min(needed / slot, max_speed)
            samples = media.decode_mono(clip, media.atempo_filter(speed))
            if len(samples) / sr > slot * 1.05:
                overflows += 1
        start = int(seg.start * sr)
        end = min(len(track), start + len(samples))
        if end > start:
            track[start:end] += samples[: end - start]

    if overflows:
        print(f"[mezcla] aviso: {overflows} frases siguen siendo más largas que su hueco "
              f"(sube --max-speed o acorta la traducción en el JSON)")
    return media.write_wav(track, out)


def separate_background(audio: Path, workdir: Path) -> Path:
    """Quita la voz original con Demucs y devuelve solo música/ambiente."""
    out_dir = workdir / "demucs"
    media.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs",
               "-o", out_dir, audio])
    result = out_dir / "htdemucs" / audio.stem / "no_vocals.wav"
    target = workdir / "background.wav"
    shutil.copy(result, target)
    return target
