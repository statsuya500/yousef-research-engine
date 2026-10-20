"""Guion numerado: exportar el texto original para traducirlo fuera y volver a importarlo."""

from __future__ import annotations

import re
from pathlib import Path

from .segments import Segment

HEADER = """\
# Guion de {name} ({count} frases)
#
# Instrucciones para traducir (también sirven como prompt para ChatGPT o Claude):
# Traduce al español cada línea. Mantén el número [001] al principio de cada línea
# y el mismo número de líneas, sin unirlas ni partirlas. Usa el contexto de todo el
# texto para que suene natural, pero procura que cada línea no sea mucho más larga
# que el original (se va a doblar con el mismo tiempo).
# Las líneas que empiezan por # se ignoran.
"""

_LINE = re.compile(r"^\s*\[?\s*(\d{1,5})\s*\]?\s*[.):\-]?\s*(.*?)\s*$")


def export_script(segments: list[Segment], path: Path, name: str) -> Path:
    width = max(3, len(str(len(segments))))
    lines = [HEADER.format(name=name, count=len(segments))]
    lines += [f"[{i:0{width}d}] {seg.source.strip()}" for i, seg in enumerate(segments, start=1)]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Path(path)


def parse_script(text: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for raw in text.splitlines():
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        result[int(m.group(1))] = m.group(2)
    return result


def apply_translation(segments: list[Segment], path: Path) -> list[Segment]:
    """Pone en cada segmento la línea traducida con su mismo número."""
    lines = parse_script(Path(path).read_text(encoding="utf-8"))
    missing = [i for i in range(1, len(segments) + 1) if i not in lines]
    extra = sorted(i for i in lines if i < 1 or i > len(segments))
    if missing:
        shown = ", ".join(str(i) for i in missing[:15]) + (" …" if len(missing) > 15 else "")
        raise ValueError(
            f"Faltan {len(missing)} de {len(segments)} líneas en {path}: {shown}. "
            "Revisa que el traductor no haya unido o borrado líneas numeradas."
        )
    if extra:
        print(f"[guion] aviso: se ignoran líneas con número fuera de rango: {extra[:10]}")
    for i, seg in enumerate(segments, start=1):
        seg.text = lines[i]
    print(f"[guion] {len(segments)} líneas traducidas cargadas de {path}")
    return segments
