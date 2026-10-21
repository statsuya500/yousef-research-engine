"""Segmentos de diálogo: tiempos, texto original y traducción."""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Segment:
    start: float
    end: float
    source: str  # texto original (p. ej. chino)
    text: str = ""  # traducción (p. ej. español)


def save_segments(segments: list[Segment], path: Path) -> None:
    data = [asdict(s) for s in segments]
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_segments(path: Path) -> list[Segment]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    segments = [
        Segment(float(d["start"]), float(d["end"]), d.get("source", ""), d.get("text", ""))
        for d in data
    ]
    return sorted(segments, key=lambda s: s.start)


def format_timestamp(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(
    segments: list[Segment], width: int = 42, field: str = "text", max_lines: int = 2
) -> str:
    """SRT de la traducción (field="text") o del texto original (field="source").

    Si una frase ocupa más de `max_lines` líneas, se parte en varios subtítulos
    seguidos y el tiempo del segmento se reparte según los caracteres de cada uno.
    """
    blocks = []
    for seg in segments:
        lines = textwrap.wrap(getattr(seg, field).strip(), width)
        if not lines:
            continue
        chunks = [lines[k : k + max_lines] for k in range(0, len(lines), max_lines)]
        total = sum(len(" ".join(c)) for c in chunks)
        t = seg.start
        for chunk in chunks:
            end = t + (seg.end - seg.start) * len(" ".join(chunk)) / total
            blocks.append(
                f"{len(blocks) + 1}\n{format_timestamp(t)} --> {format_timestamp(end)}\n"
                + "\n".join(chunk)
                + "\n"
            )
            t = end
    return "\n".join(blocks)


def to_transcript(segments: list[Segment]) -> str:
    """Transcripción bilingüe legible: tiempo, original y traducción."""
    blocks = []
    for seg in segments:
        stamp = format_timestamp(seg.start)[:-4]
        blocks.append(f"[{stamp}] {seg.source.strip()}\n           {seg.text.strip()}")
    return "\n\n".join(blocks) + "\n"
