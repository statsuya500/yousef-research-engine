"""Tapar zonas del vídeo (logos, subtítulos incrustados) y quemar subtítulos."""

from __future__ import annotations

from dataclasses import dataclass

MODES = ("blur", "delogo", "box")

DEFAULT_SUB_STYLE = (
    "FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
    "BorderStyle=1,Outline=2,Shadow=0,MarginV=30"
)


@dataclass
class Mask:
    mode: str
    x: int
    y: int
    w: int
    h: int


def parse_mask(spec: str) -> Mask:
    """'blur:x,y,ancho,alto', 'delogo:...', 'box:...' o solo 'x,y,ancho,alto' (blur)."""
    mode, _, coords = spec.partition(":") if ":" in spec else ("blur", "", spec)
    mode = mode.strip().lower()
    if mode not in MODES:
        raise ValueError(f"Modo '{mode}' no válido; usa uno de {MODES}")
    try:
        x, y, w, h = (int(float(v)) for v in coords.split(","))
    except ValueError as e:
        raise ValueError(f"Zona '{spec}' no válida; formato: modo:x,y,ancho,alto") from e
    if w <= 0 or h <= 0:
        raise ValueError(f"Zona '{spec}': ancho y alto deben ser > 0")
    return Mask(mode, x, y, w, h)


def clamp(mask: Mask, width: int, height: int) -> Mask:
    """Ajusta la zona al fotograma, con valores pares y 1 px de margen (delogo lo exige)."""
    x = max(2, min(mask.x, width - 6)) // 2 * 2
    y = max(2, min(mask.y, height - 6)) // 2 * 2
    w = max(4, min(mask.w, width - 2 - x)) // 2 * 2
    h = max(4, min(mask.h, height - 2 - y)) // 2 * 2
    return Mask(mask.mode, x, y, w, h)


def _escape_filter_path(path: str) -> str:
    return path.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def build_video_filter(
    masks: list[Mask],
    width: int,
    height: int,
    subtitles: str | None = None,
    style: str = DEFAULT_SUB_STYLE,
) -> str | None:
    """Devuelve un filter_complex que termina en [vout], o None si no hay nada que hacer."""
    parts: list[str] = []
    cur = "[0:v]"
    for k, raw in enumerate(masks):
        m = clamp(raw, width, height)
        out = f"[m{k}]"
        if m.mode == "blur":
            r = max(1, min(20, min(m.w, m.h) // 4))
            parts.append(
                f"{cur}split[base{k}][src{k}];"
                f"[src{k}]crop={m.w}:{m.h}:{m.x}:{m.y},boxblur={r}:2[blur{k}];"
                f"[base{k}][blur{k}]overlay={m.x}:{m.y}{out}"
            )
        elif m.mode == "delogo":
            parts.append(f"{cur}delogo=x={m.x}:y={m.y}:w={m.w}:h={m.h}{out}")
        else:  # box
            parts.append(f"{cur}drawbox=x={m.x}:y={m.y}:w={m.w}:h={m.h}:color=black@1:t=fill{out}")
        cur = out
    if subtitles:
        parts.append(
            f"{cur}subtitles='{_escape_filter_path(subtitles)}':force_style='{style}'[vsub]"
        )
        cur = "[vsub]"
    if not parts:
        return None
    parts.append(f"{cur}format=yuv420p[vout]")
    return ";".join(parts)
