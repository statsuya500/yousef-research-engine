"""Revisión automática de las imágenes de escena.

Cuenta caras y cabezas con un detector anime (imgutils, YOLO) y lo compara con
las personas que pide la descripción: «1boy, 1girl» son 2, «solo» es 1,
«no humans» es 0. Así se encuentran los fallos más típicos de SDXL con IP-Adapter:
personajes duplicados y personas que no deberían estar. Además prepara hojas
numeradas con todas las imágenes para revisarlas a ojo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .storyboard import Storyboard

CONFIDENCE = 0.4
_COUNT = re.compile(r"\b(\d)(?:girl|boy)s?\b")
_SKIP = re.compile(r"\b(crowd|villagers|customers|reporters|students|audience|people in background|staff in background)\b")
_HIDDEN = re.compile(r"\b(face not visible|back view|no face|from behind|silhouette)\b")


@dataclass
class Check:
    label: str  # número de escena, con letra si tiene varios planos: «007», «007b»
    image: Path
    expected: int | None  # None: escena con multitud, no se cuenta
    faces: int
    heads: int
    status: str  # OK, DUPLICADO, DUDOSO, SIN CARA, SIN CONTAR


def expected_people(prompt: str) -> int | None:
    if _SKIP.search(prompt):
        return None
    if "no humans" in prompt or "no face" in prompt:
        return 0
    counted = sum(int(n) for n in _COUNT.findall(prompt))
    if counted:
        return counted
    return 1 if "solo" in prompt else None


def check(board: Storyboard, images: list[list[Path]]) -> list[Check]:
    """images: los planos de cada escena, en el orden de board.scenes."""
    from imgutils.detect import detect_faces, detect_heads

    results = []
    for scene, shots in zip(board.scenes, images):
        for k, path in enumerate(shots):
            label = f"{scene.number:03d}" + (chr(ord("a") + k) if len(shots) > 1 else "")
            results.append(_check_one(scene.image, label, path, detect_faces, detect_heads))
    return results


def _check_one(prompt: str, label: str, path: Path, detect_faces, detect_heads) -> Check:
    expected = expected_people(prompt)
    faces = sum(1 for d in detect_faces(str(path)) if d[2] > CONFIDENCE)
    heads = sum(1 for d in detect_heads(str(path)) if d[2] > CONFIDENCE)
    if expected is None:
        status = "SIN CONTAR"
    elif faces > expected:
        status = "DUPLICADO"
    elif heads > expected:
        status = "DUDOSO"
    elif expected > 0 and faces == 0 and heads == 0 and not _HIDDEN.search(prompt):
        status = "SIN CARA"
    else:
        status = "OK"
    return Check(label, path, expected, faces, heads, status)


def contact_sheets(checks: list[Check], folder: Path, per_sheet: int = 8, width: int = 640) -> list[Path]:
    """Hojas de 2 columnas con el número de escena y el estado, para revisar a ojo."""
    from PIL import Image, ImageDraw, ImageFont

    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("hoja_*.jpg"):
        old.unlink()
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    sheets = []
    for k in range(0, len(checks), per_sheet):
        group = checks[k:k + per_sheet]
        thumbs = []
        for c in group:
            im = Image.open(c.image).convert("RGB")
            im = im.resize((width, round(im.height * width / im.width)))
            label = c.label + ("" if c.status in ("OK", "SIN CONTAR") else f"  {c.status}")
            draw = ImageDraw.Draw(im)
            draw.text((10, 8), label, fill="yellow" if c.status in ("OK", "SIN CONTAR") else "red",
                      font=font, stroke_width=3, stroke_fill="black")
            thumbs.append(im)
        h = thumbs[0].height
        rows = (len(thumbs) + 1) // 2
        sheet = Image.new("RGB", (width * 2, h * rows), "black")
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % 2) * width, (i // 2) * h))
        out = folder / f"hoja_{k // per_sheet + 1:02d}.jpg"
        sheet.save(out, quality=88)
        sheets.append(out)
    return sheets


def report(checks: list[Check]) -> str:
    bad = [c for c in checks if c.status not in ("OK", "SIN CONTAR")]
    lines = [f"Escenas revisadas: {len(checks)}. Posibles problemas: {len(bad)}."]
    for c in bad:
        lines.append(f"  [{c.label}] {c.status}: esperadas {c.expected}, caras {c.faces}, cabezas {c.heads}")
    crowd = [c.label for c in checks if c.status == "SIN CONTAR"]
    if crowd:
        lines.append(f"Sin contar (multitud o número sin indicar, revisar a ojo): {', '.join(crowd)}")
    return "\n".join(lines)
