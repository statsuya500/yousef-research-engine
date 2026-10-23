"""Miniaturas de YouTube: imagen con los personajes de la historia y texto grande encima.

La imagen se genera igual que una escena (mismas caras de las fichas), pero con
etiquetas de primer plano y contraste. El texto se coloca en el lado más despejado
de la imagen, con borde negro y la palabra entre *asteriscos* resaltada en amarillo.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from . import images
from .storyboard import Scene, Storyboard

SIZE = (1280, 720)  # tamaño recomendado por YouTube
MAX_BYTES = 2_000_000  # límite de YouTube para miniaturas
THUMB_TAGS = ("close-up, dramatic lighting, intense expression, high contrast, vivid colors, "
              "cinematic composition, depth of field")
THUMB_NEGATIVE = "text, letters, watermark, logo, signature"
FONT = Path(__file__).parent / "fonts" / "Anton-Regular.ttf"
WHITE = (255, 255, 255)
YELLOW = (255, 214, 0)
BLACK = (0, 0, 0)
TEXT_WIDTH = 0.46  # parte del ancho que puede ocupar el texto
TEXT_HEIGHT = 0.82
MAX_FONT = 260


# --- Imagen ------------------------------------------------------------------------

def thumbnail_scene(board: Storyboard) -> Scene:
    """La escena de @miniatura; si no hay, la primera escena con un solo personaje."""
    if board.thumbnail:
        return board.thumbnail
    return next((s for s in board.scenes if len(s.characters) == 1), board.scenes[0])


def jobs(board: Storyboard, folder: Path, portraits: Path, options: int, seed: int,
         model: str) -> list[images.Job]:
    scene = thumbnail_scene(board)
    faces = [images.chosen_portrait(portraits, c) for c in scene.characters]
    missing = [f.name for f in faces if not f.exists()]
    if missing:
        raise SystemExit(f"Miniatura: falta la ficha {', '.join(missing)} en {portraits}. "
                         "Ejecuta primero: python -m mangavid personajes <historia.txt>")
    framed = replace(scene, action=", ".join(p for p in (scene.action, THUMB_TAGS) if p))
    prompt = board.prompt(framed)
    negative = ", ".join(p for p in (board.negative_for(scene), THUMB_NEGATIVE) if p)
    scale = next(v for v in (scene.likeness, board.likeness, images.IP_SCALE) if v is not None)
    result = []
    for i in range(1, options + 1):
        job_seed = seed + i + 100_003 * scene.reroll
        key = images._hash(model, prompt, negative, job_seed, images.STEPS, images.GUIDANCE, scale,
                           images.ENCODER_VERSION, *(images._file_hash(f) for f in faces))
        result.append(images.Job(prompt, job_seed, folder / "base" / f"base_{i}_{key}.png",
                                 (images.WIDTH, images.HEIGHT), faces, negative, scale))
    return result


# --- Texto -------------------------------------------------------------------------

def parse_text(text: str) -> list[tuple[str, bool]]:
    """Palabras en mayúsculas y si van resaltadas. Sin *marcas*, se resalta la última."""
    words = [(w.strip("*").upper(), w.startswith("*") or w.endswith("*")) for w in text.split()]
    words = [(w, h) for w, h in words if w]
    if words and not any(h for _, h in words):
        words[-1] = (words[-1][0], True)
    return words


def _layouts(words: list) -> list[list[list]]:
    """Formas de repartir las palabras en 1, 2 o 3 líneas, sin desordenarlas."""
    n = len(words)
    options = [[words]]
    options += [[words[:i], words[i:]] for i in range(1, n)]
    options += [[words[:i], words[i:j], words[j:]] for i in range(1, n) for j in range(i + 1, n)]
    return options


def _line_width(draw, line, font) -> float:
    return draw.textlength(" ".join(w for w, _ in line), font=font)


def _fit(draw, layout, box_w: float, box_h: float):
    """Mayor tamaño de letra con el que la disposición cabe en la caja."""
    from PIL import ImageFont

    lo, hi = 20, MAX_FONT
    while lo < hi:
        size = (lo + hi + 1) // 2
        font = ImageFont.truetype(str(FONT), size)
        fits = (max(_line_width(draw, line, font) for line in layout) <= box_w
                and size * 1.08 * len(layout) <= box_h)
        lo, hi = (size, hi) if fits else (lo, size - 1)
    return lo


def quietest_side(image) -> str:
    """El lado (izquierda o derecha) con menos detalle, donde el texto se leerá mejor."""
    from PIL import ImageFilter, ImageStat

    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    w, h = edges.size
    left = ImageStat.Stat(edges.crop((0, 0, int(w * 0.45), h))).mean[0]
    right = ImageStat.Stat(edges.crop((int(w * 0.55), 0, w, h))).mean[0]
    return "izquierda" if left <= right else "derecha"


def _shade(image, side: str):
    """Degradado oscuro bajo el texto para que se lea sobre cualquier fondo."""
    from PIL import Image

    w, h = image.size
    ramp = Image.linear_gradient("L").rotate(90 if side == "izquierda" else -90).resize((w, h))
    ramp = ramp.point(lambda v: int(max(0, v - 70) * 0.9))  # solo el 70 % del lado del texto
    black = Image.new("RGB", (w, h), BLACK)
    return Image.composite(black, image, ramp)


def compose(base: Path, text: str, out: Path, side: str = "auto") -> Path:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

    image = ImageOps.fit(Image.open(base).convert("RGB"), SIZE, Image.LANCZOS)
    image = ImageEnhance.Color(ImageEnhance.Contrast(image).enhance(1.08)).enhance(1.15)
    words = parse_text(text)
    if words:
        if side == "auto":
            side = quietest_side(image)
        image = _shade(image, side)
        draw = ImageDraw.Draw(image)
        box_w, box_h = SIZE[0] * TEXT_WIDTH, SIZE[1] * TEXT_HEIGHT
        layout = max(_layouts(words), key=lambda lay: (_fit(draw, lay, box_w, box_h), -len(lay)))
        size = _fit(draw, layout, box_w, box_h)
        font = ImageFont.truetype(str(FONT), size)
        stroke = max(3, size // 11)
        line_h = size * 1.08
        margin = SIZE[0] * 0.04
        y = (SIZE[1] - line_h * len(layout)) / 2 - size * 0.08
        space = draw.textlength(" ", font=font)
        for line in layout:
            width = _line_width(draw, line, font)
            x = margin if side == "izquierda" else SIZE[0] - margin - width
            for word, highlight in line:
                shadow = max(2, size // 22)
                draw.text((x + shadow, y + shadow), word, font=font, fill=BLACK,
                          stroke_width=stroke, stroke_fill=BLACK)
                draw.text((x, y), word, font=font, fill=YELLOW if highlight else WHITE,
                          stroke_width=stroke, stroke_fill=BLACK)
                x += draw.textlength(word, font=font) + space
            y += line_h
    return save_jpeg(image, out)


def save_jpeg(image, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    for quality in (93, 88, 82, 75, 65):
        image.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
        if out.stat().st_size <= MAX_BYTES:
            break
    return out


def contact_sheet(paths: list[Path], out: Path) -> Path:
    """Las opciones en una sola imagen, numeradas, para elegir de un vistazo."""
    from PIL import Image, ImageDraw, ImageFont

    cols = 2 if len(paths) > 1 else 1
    rows = (len(paths) + cols - 1) // cols
    tw, th = SIZE[0] // 2, SIZE[1] // 2
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 10, rows * th + (rows + 1) * 10), (30, 30, 30))
    font = ImageFont.truetype(str(FONT), 48)
    for k, path in enumerate(paths):
        x, y = 10 + (k % cols) * (tw + 10), 10 + (k // cols) * (th + 10)
        sheet.paste(Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
        ImageDraw.Draw(sheet).text((x + 12, y + 6), str(k + 1), font=font, fill=YELLOW,
                                   stroke_width=4, stroke_fill=BLACK)
    return save_jpeg(sheet, out)


def safe_name(text: str) -> str:
    return re.sub(r"[^\w-]+", "_", text).strip("_")[:40] or "miniatura"
