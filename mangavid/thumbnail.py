"""Miniaturas de YouTube al estilo de los canales de manhwa narrado.

Imagen luminosa con los personajes de la historia (mismas caras que las escenas) y,
encima, rótulos amarillos inclinados con borde negro y blanco:
- etiquetas que señalan a un personaje con una flecha («PROTA», «HIJA», «CEO»);
- frases sueltas en un hueco libre («¡NO SALTES!», «?!?», «-80 °C»).

El texto se escribe así (en @miniatura_texto o con --texto):
    @kai=PROTA | @luna=HIJA | ¡No saltes!
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from pathlib import Path

from . import images
from .storyboard import Scene, Storyboard

SIZE = (1280, 720)  # tamaño recomendado por YouTube
MAX_BYTES = 2_000_000  # límite de YouTube para miniaturas
# Como las miniaturas de los canales de manhwa narrado: de día, nítidas y saturadas, sin neblina.
THUMB_TAGS = ("anime key visual, bright daylight, vivid saturated colors, crisp clean lineart, sharp focus, "
              "cel shading, expressive faces, dynamic pose, detailed background")
THUMB_NEGATIVE = ("text, letters, speech bubble, watermark, logo, signature, dark, monochrome, "
                  "sunset, haze, bloom, painterly, blurry, washed out")
FONT = Path(__file__).parent / "fonts" / "Anton-Regular.ttf"
YELLOW = (255, 221, 0, 255)
BLACK = (10, 10, 20, 255)
WHITE = (255, 255, 255, 255)
LABEL_SIZE = 72  # px de alto de letra de las etiquetas
LABEL_WIDTH = 0.3  # ancho máximo de una etiqueta antes de partirla en líneas
CAPTION_SIZE = 92  # px de las frases
SLANT = 0.18  # inclinación tipo cursiva
CAPTION_WIDTH = 0.5  # ancho máximo de una frase, en parte del ancho de la imagen
HEAD_CONFIDENCE = 0.4


# --- Imagen ------------------------------------------------------------------------

def thumbnail_scene(board: Storyboard) -> Scene:
    """La escena de @miniatura; si no hay, la primera con dos personajes, o con uno."""
    if board.thumbnail:
        return board.thumbnail
    for wanted in (2, 1):
        for s in board.scenes:
            if len(s.characters) == wanted:
                return s
    return board.scenes[0]


def jobs(board: Storyboard, folder: Path, portraits: Path, options: int, seed: int,
         model: str) -> list[images.Job]:
    scene = thumbnail_scene(board)
    faces = [images.chosen_portrait(portraits, c) for c in scene.characters]
    missing = [f.name for f in faces if not f.exists()]
    if missing:
        raise SystemExit(f"Miniatura: falta la ficha {', '.join(missing)} en {portraits}. "
                         "Ejecuta primero: python -m mangavid personajes <historia.txt>")
    framed = replace(scene, action=", ".join(p for p in (scene.action, THUMB_TAGS) if p))
    styled = replace(board, style=board.thumbnail_style) if board.thumbnail_style else board
    prompt = styled.prompt(framed)
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

@dataclass
class Item:
    text: str
    character: str | None = None  # None: frase suelta, sin flecha
    speech: bool = False  # @kai>¡No saltes!: lo dice el personaje, con pico de bocadillo


def parse_text(text: str) -> list[Item]:
    """«@kai=PROTA | @kai>¡No saltes! | ?!?» -> etiqueta de @kai, frase dicha por @kai y una suelta."""
    items = []
    for part in (p.strip() for p in text.split("|")):
        if not part:
            continue
        if m := re.match(r"@([\w-]+)\s*([=>])(.*)$", part):
            items.append(Item(m.group(3).strip().replace("*", "").upper(), m.group(1).lower(),
                              m.group(2) == ">"))
        else:
            items.append(Item(part.replace("*", "").upper()))
    return [i for i in items if i.text]


def _wrap(text: str, font, max_width: float, max_lines: int = 3) -> list[str]:
    """Reparte las palabras en el mínimo de líneas que caben, lo más igualadas posible."""
    words = text.split()

    def splits(ws: list[str], n: int):
        if n == 1:
            yield [" ".join(ws)]
            return
        for i in range(1, len(ws) - n + 2):
            for rest in splits(ws[i:], n - 1):
                yield [" ".join(ws[:i])] + rest

    for n in range(1, min(max_lines, len(words)) + 1):
        best = min(splits(words, n), key=lambda ls: max(font.getlength(x) for x in ls))
        if max(font.getlength(x) for x in best) <= max_width or n == min(max_lines, len(words)):
            return best
    return [text]


def sticker(lines: list[str], size: int, angle: float):
    """Rótulo amarillo con borde negro grueso, inclinado y girado."""
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(str(FONT), size)
    black = max(4, int(size * 0.13))
    pad = black + 4
    widths = [font.getlength(line) for line in lines]
    line_h = int(size * 1.05)
    w, h = int(max(widths)) + 2 * pad, line_h * len(lines) + 2 * pad
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for k, (line, lw) in enumerate(zip(lines, widths)):
        xy = (pad + (max(widths) - lw) / 2, pad + k * line_h - size * 0.08)
        draw.text(xy, line, font=font, fill=BLACK, stroke_width=black, stroke_fill=BLACK)
        draw.text(xy, line, font=font, fill=YELLOW)
    extra = int(SLANT * h)
    layer = layer.transform((w + extra, h), Image.AFFINE, (1, SLANT, -SLANT * h, 0, 1, 0),
                            resample=Image.BICUBIC)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    return layer.crop(layer.getbbox())


# --- Dónde están los personajes ---------------------------------------------------

Box = tuple[float, float, float, float]


def find_heads(image, count: int) -> list[Box]:
    """Cabezas de los personajes, de izquierda a derecha.

    Con imgutils instalado se detectan en la imagen; si no, se usa la franja donde
    IP-Adapter dibuja a cada personaje (una franja vertical por personaje, en orden).
    """
    w, h = image.size
    detected: list[Box] = []
    try:
        from imgutils.detect import detect_heads

        detected = [box for box, _, score in detect_heads(image) if score > HEAD_CONFIDENCE]
    except Exception:
        pass
    if count <= 0:
        return sorted(detected)
    slots = [((i + 0.5) / count) * w for i in range(count)]
    heads = []
    pool = sorted(detected, key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))[: max(count, len(detected))]
    for x in slots:
        if pool:
            best = min(pool, key=lambda b: abs((b[0] + b[2]) / 2 - x))
            pool.remove(best)
            heads.append(best)
        else:
            s = h * 0.22
            heads.append((x - s / 2, h * 0.18, x + s / 2, h * 0.18 + s))
    return heads


# --- Colocación --------------------------------------------------------------------

def _overlap(a: Box, b: Box) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, dx) * max(0.0, dy)


def _busy(edges, box: Box) -> float:
    from PIL import ImageStat

    return ImageStat.Stat(edges.crop(tuple(int(v) for v in box))).mean[0] / 255


def _clamp(x: float, y: float, w: int, h: int, margin: float = 12) -> tuple[float, float]:
    return (min(max(x, margin), SIZE[0] - w - margin), min(max(y, margin), SIZE[1] - h - margin))


def _place(layer, avoid: list[Box], taken: list[Box], edges, around: Box | None) -> Box:
    """Busca el sitio donde el rótulo tapa menos caras, rótulos y detalle."""
    w, h = layer.size
    if around:
        cx, cy = (around[0] + around[2]) / 2, (around[1] + around[3]) / 2
        r = max(around[2] - around[0], around[3] - around[1]) * 0.8 + max(w, h) * 0.5 + 85
        # Primero hacia fuera (el lado del borde más cercano), luego abajo y arriba.
        out = 180 if cx < SIZE[0] / 2 else 0
        sign = 1 if out == 180 else -1
        angles = [out, out - sign * 30, out + sign * 30, out - sign * 60, out + sign * 60, 90, -90,
                  out + 180]
        spots = [(cx + r * math.cos(math.radians(a)) - w / 2, cy + r * math.sin(math.radians(a)) - h / 2)
                 for a in angles]
    else:
        spots = [(fx * (SIZE[0] - w), fy * (SIZE[1] - h))
                 for fy in (0.95, 0.05, 0.5) for fx in (0.05, 0.95, 0.5)]
    best, best_score = None, float("inf")
    for rank, (wx, wy) in enumerate(spots):
        x, y = _clamp(wx, wy, w, h)
        moved = math.hypot(x - wx, y - wy) / max(w, h)
        box = (x, y, x + w, y + h)
        area = w * h
        score = (8 * sum(_overlap(box, a) for a in avoid) / area
                 + 12 * sum(_overlap(box, t) for t in taken) / area
                 + _busy(edges, box) + 0.06 * rank + 0.8 * min(1.0, moved))
        if score < best_score:
            best, best_score = box, score
    return best


ARROW_BEND = 0.12  # curvatura de las flechas: desvío del centro en parte de su largo (casi rectas)
SPEECH_BASE = 34  # ancho en px de la base del pico de bocadillo


def _speech_tail(draw, start, end, box: Box) -> Box:
    """Pico de bocadillo amarillo con borde negro, del rótulo (`start`) hacia quien habla (`end`)."""
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    # La base se mete un poco dentro del rótulo para que el pico parezca salir de él.
    inner = (start[0] - 18 * math.cos(ang), start[1] - 18 * math.sin(ang))
    for fill, grow in ((BLACK, 7), (YELLOW, 0)):
        half = SPEECH_BASE / 2 + grow
        tip = (end[0] + grow * math.cos(ang), end[1] + grow * math.sin(ang))
        draw.polygon([tip,
                      (inner[0] + half * math.cos(ang + math.pi / 2), inner[1] + half * math.sin(ang + math.pi / 2)),
                      (inner[0] + half * math.cos(ang - math.pi / 2), inner[1] + half * math.sin(ang - math.pi / 2))],
                     fill=fill)
    xs, ys = (start[0], end[0]), (start[1], end[1])
    return (min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20)


def _curve(start, end, bend: float = ARROW_BEND, steps: int = 40) -> list[tuple[float, float]]:
    """Curva suave (Bézier cuadrática) de `start` a `end`, abombada hacia arriba,
    o hacia el borde de la imagen si la flecha es casi vertical."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    if abs(dx) > abs(dy) * 0.35:
        sign = -1 if ny > 0 else 1  # el punto de control queda por encima
    else:
        sign = 1 if (nx > 0) == (mid[0] > SIZE[0] / 2) else -1  # hacia el borde más cercano
    ctrl = (mid[0] + sign * nx * bend * length, mid[1] + sign * ny * bend * length)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append(((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * ctrl[0] + t * t * end[0],
                    (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * ctrl[1] + t * t * end[1]))
    return pts


def _arrow(draw, start, end, width: int) -> Box:
    """Flecha curva amarilla con borde negro, de `start` (el rótulo) a `end` (la cara).
    Devuelve el rectángulo que ocupa."""
    pts = _curve(start, end)
    head = width * 2.6
    # El cuerpo acaba donde empieza la punta; la punta sigue la dirección final de la curva.
    shaft = [p for p in pts if math.hypot(end[0] - p[0], end[1] - p[1]) > head]
    if len(shaft) < 2:
        shaft = pts[:2]
    base = shaft[-1]
    ang = math.atan2(end[1] - base[1], end[0] - base[0])

    def tri(scale: float):
        side = head * 0.75 * scale
        tip = (end[0] + (scale - 1) * head * math.cos(ang), end[1] + (scale - 1) * head * math.sin(ang))
        back = (end[0] - head * scale * math.cos(ang) + (scale - 1) * head * math.cos(ang),
                end[1] - head * scale * math.sin(ang) + (scale - 1) * head * math.sin(ang))
        return [tip,
                (back[0] + side * math.cos(ang + math.pi / 2), back[1] + side * math.sin(ang + math.pi / 2)),
                (back[0] + side * math.cos(ang - math.pi / 2), back[1] + side * math.sin(ang - math.pi / 2))]

    for fill, w, scale in ((BLACK, width + 8, 1.35), (YELLOW, width, 1.0)):
        draw.line(shaft, fill=fill, width=w, joint="curve")
        r = w / 2
        draw.ellipse([start[0] - r, start[1] - r, start[0] + r, start[1] + r], fill=fill)
        draw.polygon(tri(scale), fill=fill)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) - 15, min(ys) - 15, max(xs) + 15, max(ys) + 15)


def _edge_point(box: Box, toward: tuple[float, float]) -> tuple[float, float]:
    """Punto del borde del rótulo en dirección a `toward`."""
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == dy == 0:
        return cx, cy
    sx = (box[2] - box[0]) / 2 / abs(dx) if dx else float("inf")
    sy = (box[3] - box[1]) / 2 / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


# --- Composición -------------------------------------------------------------------

def compose(base: Path, text: str, out: Path, characters: list[str] | None = None) -> Path:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

    image = ImageOps.fit(Image.open(base).convert("RGB"), SIZE, Image.LANCZOS)
    image = ImageEnhance.Color(ImageEnhance.Contrast(image).enhance(1.05)).enhance(1.12)
    items = parse_text(text)
    characters = characters or []
    unknown = [i.character for i in items if i.character and i.character not in characters]
    if unknown:
        raise ValueError(f"Miniatura: @{unknown[0]} no sale en la imagen de la miniatura "
                         f"(personajes: {', '.join('@' + c for c in characters) or 'ninguno'})")
    if not items:
        return save_jpeg(image, out)

    heads = find_heads(image, len(characters))
    head_of = dict(zip(characters, heads))
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    canvas = image.convert("RGBA")
    arrows = ImageDraw.Draw(canvas)
    taken: list[Box] = []
    angles = (7, -5, 5, -7)
    caption_font = ImageFont.truetype(str(FONT), CAPTION_SIZE)
    label_font = ImageFont.truetype(str(FONT), LABEL_SIZE)
    # Primero las etiquetas, que tienen que estar junto a su personaje; después las frases.
    for k, item in enumerate(sorted(items, key=lambda i: i.character is None)):
        if item.speech:
            lines = _wrap(item.text, caption_font, SIZE[0] * CAPTION_WIDTH * 0.8)
            layer = sticker(lines, int(CAPTION_SIZE * 0.85), angles[k % 4] * 0.6)
            target = head_of[item.character]
        elif item.character:
            lines = _wrap(item.text, label_font, SIZE[0] * LABEL_WIDTH)
            layer = sticker(lines, LABEL_SIZE, angles[k % 4])
            target = head_of[item.character]
        else:
            lines = _wrap(item.text, caption_font, SIZE[0] * CAPTION_WIDTH)
            layer = sticker(lines, CAPTION_SIZE, angles[k % 4] * 0.6)
            target = None
        box = _place(layer, heads, taken, edges, target)
        taken.append(box)
        if target:
            tcx, tcy = (target[0] + target[2]) / 2, (target[1] + target[3]) / 2
            start = _edge_point(box, (tcx, tcy))
            gap = max(target[2] - target[0], target[3] - target[1]) * 0.55
            dist = math.hypot(tcx - start[0], tcy - start[1])
            if item.speech:
                # El pico apunta a la barbilla: la parte baja de la cabeza.
                mouth = (tcx, target[1] + (target[3] - target[1]) * 0.8)
                d = math.hypot(mouth[0] - start[0], mouth[1] - start[1]) or 1.0
                stop = min(d - 10, max(40.0, d * 0.55))
                end = (start[0] + (mouth[0] - start[0]) * stop / d, start[1] + (mouth[1] - start[1]) * stop / d)
                taken.append(_speech_tail(arrows, start, end, box))
            elif dist > gap + 40:
                end = (tcx - (tcx - start[0]) * gap / dist, tcy - (tcy - start[1]) * gap / dist)
                taken.append(_arrow(arrows, start, end, 9))
        canvas.alpha_composite(layer, (int(box[0]), int(box[1])))
    return save_jpeg(canvas.convert("RGB"), out)


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
