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


def to_srt(segments: list[Segment], width: int = 42) -> str:
    blocks = []
    for i, seg in enumerate((s for s in segments if s.text.strip()), start=1):
        lines = textwrap.wrap(seg.text.strip(), width)
        blocks.append(
            f"{i}\n{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n"
            + "\n".join(lines)
            + "\n"
        )
    return "\n".join(blocks)
