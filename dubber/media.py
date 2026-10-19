"""Utilidades de FFmpeg: sondeo, extracción, decodificación y escritura de audio."""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100


def run(cmd: list[str], cwd: Path | None = None) -> bytes:
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", "replace")[-3000:]
        raise RuntimeError(f"Falló el comando: {' '.join(map(str, cmd))}\n{err}")
    return result.stdout


def probe(path: Path) -> dict:
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=codec_type,width,height",
        "-of", "json", path,
    ])
    return json.loads(out)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def video_size(path: Path) -> tuple[int, int]:
    for stream in probe(path).get("streams", []):
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise ValueError(f"No hay pista de vídeo en {path}")


def has_audio(path: Path) -> bool:
    return any(s.get("codec_type") == "audio" for s in probe(path).get("streams", []))


def extract_audio(video: Path, out: Path) -> Path:
    run(["ffmpeg", "-y", "-i", video, "-vn", "-ac", "2", "-ar", SAMPLE_RATE, out])
    return out


def decode_mono(path: Path, audio_filter: str | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if audio_filter:
        cmd += ["-af", audio_filter]
    cmd += ["-f", "f32le", "-ac", "1", "-ar", SAMPLE_RATE, "-"]
    return np.frombuffer(run(cmd), dtype=np.float32).copy()


def write_wav(samples: np.ndarray, path: Path) -> Path:
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return path


def atempo_filter(speed: float) -> str:
    """Cadena atempo (cada filtro admite 0.5–2.0) para cambiar la velocidad sin cambiar el tono."""
    parts = []
    while speed > 2.0:
        parts.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        parts.append(0.5)
        speed /= 0.5
    parts.append(speed)
    return ",".join(f"atempo={p:.4f}" for p in parts)
