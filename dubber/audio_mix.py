"""Montaje de la pista de voz doblada y del fondo (música/ambiente)."""

from __future__ import annotations

import shutil
import subprocess
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
    """Coloca cada frase en su tiempo sin que dos voces se pisen.

    Si una frase no cabe hasta la siguiente, se acelera (hasta `max_speed`); si aun así
    no cabe, la siguiente empieza un poco más tarde y el retraso se recupera en las pausas.
    """
    sr = media.SAMPLE_RATE
    gap = int(0.08 * sr)  # pequeña pausa entre frases
    track = np.zeros(int(total_duration * sr) + 1, dtype=np.float32)
    cursor = 0
    sped = delayed = 0

    for i, (seg, clip) in enumerate(zip(segments, clips)):
        if clip is None:
            continue
        start = max(int(seg.start * sr), cursor)
        if start > int(seg.start * sr) + sr // 10:
            delayed += 1
        next_start = int(segments[i + 1].start * sr) if i + 1 < len(segments) else len(track)
        slot = max(int(0.3 * sr), next_start - start)
        samples = media.decode_mono(clip)
        if len(samples) > slot * 1.02:
            speed = min(len(samples) / slot, max_speed)
            samples = media.decode_mono(clip, media.atempo_filter(speed))
            sped += 1
        end = min(len(track), start + len(samples))
        if end > start:
            track[start:end] += samples[: end - start]
        cursor = start + len(samples) + gap

    print(f"[mezcla] {sped} frases aceleradas, {delayed} desplazadas para no pisarse")
    if delayed > len(segments) // 4:
        print("[mezcla] consejo: si se nota desfase, acorta traducciones en segments.json "
              "o usa --rate +10%")
    return media.write_wav(track, out)


def separate_background(audio: Path, workdir: Path) -> Path:
    """Quita la voz original con Demucs y devuelve solo música/ambiente."""
    target = workdir / "background.wav"
    if target.exists():
        print("[fondo] reutilizando la separación anterior")
        return target
    out_dir = workdir / "demucs"
    cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs",
           "-o", str(out_dir), str(audio)]
    try:
        import torch

        if torch.cuda.is_available():
            cmd[3:3] = ["-d", "cuda"]
    except ImportError:
        pass
    # Sin capturar la salida para que se vea la barra de progreso.
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError("Demucs falló; prueba --background duck")
    shutil.copy(out_dir / "htdemucs" / audio.stem / "no_vocals.wav", target)
    return target
