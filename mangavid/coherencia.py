"""Coherencia visual: que cada personaje conserve su identidad y su aspecto entre escenas.

Referencias, por orden:
1. La ficha del personaje y la ropa que lleva en esa escena (la ropa sigue puesta hasta que el
   guion la cambie, ver storyboard). Es la única referencia que puede dar un error CONFIRMED.
2. Su aparición válida anterior (la última sin errores confirmados): sirve para lo que la ficha no
   dice y para notar cambios de cara. Solo da POSSIBLE: una imagen no es la ficha.
Nunca se usa la mayoría de las imágenes como referencia: si muchas salen mal, seguirían mal.

Herramientas (imgutils, modelos ya descargados): detector de personas, etiquetador WD14 para
ojos, pelo, edad, barba, accesorios y ropa, y CCIP para el parecido de la cara. El OCR (número
de una camiseta) necesita un modelo que no está descargado: esa comprobación sale como
NOT CHECKABLE y se revisa a ojo.

Cada comprobación da un resultado: OK (verificado), CONFIRMED (error seguro), POSSIBLE (posible
error) o NOT CHECKABLE (no se puede verificar). Nada se da por bueno sin haberlo visto.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .storyboard import Scene, Storyboard

OK, CONFIRMED, POSSIBLE, UNCHECKABLE = "OK", "CONFIRMED", "POSSIBLE", "NOT CHECKABLE"
REPORT_VERSION = 2  # 2: el informe y las aprobaciones guardan el hash del contenido de cada imagen

TAG_LOW = 0.35  # a partir de aquí el etiquetador «ve» algo
TAG_HIGH = 0.6  # a partir de aquí lo ve con seguridad: puede confirmar un error
PERSON_SCORE = 0.4
MIN_CROP = 120  # px de alto: por debajo, el personaje es demasiado pequeño para comprobarlo
# Diferencia CCIP entre la cara de la ficha y la de la escena. Calibrado con solo 6 recortes
# (mismo personaje 0.08-0.12, distinto 0.13-0.39): provisional, ajústalo con más historias.
# El umbral por defecto de imgutils necesita un archivo que no está descargado.
FACE_POSSIBLE = 0.18
FACE_CONFIRMED = 0.28

COLORS = {"black", "white", "grey", "brown", "blonde", "red", "orange", "yellow", "green", "blue",
          "purple", "pink", "aqua", "silver", "beige"}
SYNONYMS = {
    "gray": {"grey"}, "silver": {"silver", "grey", "white"}, "blond": {"blonde"}, "golden": {"blonde", "yellow"},
    "auburn": {"brown", "red", "orange"}, "chestnut": {"brown"}, "hazel": {"brown", "green", "yellow"},
    "navy": {"blue", "black"}, "cream": {"white", "beige"}, "beige": {"beige", "white", "brown"},
    "violet": {"purple"}, "lavender": {"purple"},
}
GARMENTS = {"t-shirt": "shirt", "shirt": "shirt", "blouse": "shirt", "sweater": "sweater", "jumper": "sweater",
            "hoodie": "hoodie", "jacket": "jacket", "windbreaker": "jacket", "coat": "coat", "dress": "dress",
            "suit": "suit", "skirt": "skirt", "cardigan": "cardigan", "vest": "vest", "uniform": "uniform"}
HAIR_LENGTHS = ["short_hair", "medium_hair", "long_hair", "very_long_hair"]
HAIRSTYLES = {"ponytail": "ponytail", "twintails": "twintails", "braid": "braid", "bun": "hair_bun",
              "bob": "bob_cut", "combed back": "hair_slicked_back", "slicked back": "hair_slicked_back"}
ACCESSORIES = {"sunglasses": "sunglasses", "glasses": "glasses", "earrings": "earrings", "necklace": "necklace",
               "choker": "choker", "hat": "hat", "scarf": "scarf", "bracelet": "bracelet", "watch": "wristwatch",
               "bow tie": "bowtie", "tie": "necktie", "hairclip": "hairclip", "hair clip": "hairclip",
               "ribbon": "hair_ribbon"}
FACIAL_HAIR = ["beard", "mustache", "goatee", "facial_hair", "stubble"]
WRITING = ["clothes_writing", "jersey"]
HIDDEN = re.compile(r"\b(back view|from behind|seen from behind|face not visible|no face)\b")


# --- Qué debería verse ---------------------------------------------------------------

@dataclass
class Profile:
    eyes: set[str] = field(default_factory=set)
    hair_color: set[str] = field(default_factory=set)
    hair_length: str | None = None
    hairstyles: set[str] = field(default_factory=set)
    facial_hair: bool | None = None  # False: afeitado; True: con barba; None: la ficha no lo dice
    age: str | None = None  # child, young, adult, old
    accessories: set[str] = field(default_factory=set)
    no_accessories: set[str] = field(default_factory=set)  # «no earrings»
    garments: dict[str, set[str]] = field(default_factory=dict)  # prenda -> colores admitidos
    number: str | None = None


def _colors(phrase: str) -> set[str]:
    out: set[str] = set()
    for word in re.findall(r"[a-z]+", phrase.lower()):
        if word in SYNONYMS:
            out |= SYNONYMS[word]
        elif word in COLORS:
            out.add(word)
    return out


def _age(text: str) -> str | None:
    if m := re.search(r"(\d+)\s*years?\s*old", text):
        n = int(m.group(1))
        return "child" if n < 13 else "young" if n < 30 else "adult" if n < 55 else "old"
    for words, bucket in ((r"\b(child|little girl|little boy|kid)\b", "child"),
                          (r"\b(elderly|old man|old woman)\b", "old"),
                          (r"\b(teenager|teenage)\b", "young"),
                          (r"\b(middle-aged|mature)\b", "adult")):
        if re.search(words, text):
            return bucket
    return None


def profile_from(text: str) -> Profile:
    """Rasgos comprobables de un texto de ficha o de ropa."""
    prof = Profile()
    text = text.lower()
    prof.age = _age(text)
    for phrase in (p.strip() for p in text.split(",")):
        if m := re.search(r"number (\d+)", phrase):
            prof.number = m.group(1)
        if re.search(r"\b(clean-shaven|no beard|no mustache)\b", phrase):
            prof.facial_hair = False
        elif re.search(r"\b(beard|mustache|goatee|stubble)\b", phrase) and not phrase.startswith("no "):
            prof.facial_hair = True
        if re.search(r"\beyes?\b", phrase):
            prof.eyes |= _colors(phrase)
        if re.search(r"\b(hair|bob|ponytail|twintails|braid|bun)\b", phrase) and "eyes" not in phrase:
            prof.hair_color |= _colors(phrase.split("with")[0])
            for words, tag in (("very long", "very_long_hair"), ("long", "long_hair"), ("medium", "medium_hair"),
                               ("shoulder", "medium_hair"), ("short", "short_hair"), ("bob", "short_hair")):
                if re.search(rf"\b{words}\b", phrase):
                    prof.hair_length = tag
                    break
            prof.hairstyles |= {tag for word, tag in HAIRSTYLES.items() if re.search(rf"\b{word}\b", phrase)}
        for word, tag in ACCESSORIES.items():
            if re.search(rf"\b{word}\b", phrase):
                (prof.no_accessories if phrase.startswith("no ") else prof.accessories).add(tag)
                break
        for word, tag in GARMENTS.items():
            if re.search(rf"\b{re.escape(word)}\b", phrase):
                prof.garments.setdefault(tag, set()).update(_colors(phrase.split("with")[0]))
                break
    return prof


def expected_for(board: Storyboard, scene: Scene, name: str) -> Profile:
    """Ficha + ropa vigente. La ropa de la escena sustituye a la de la ficha; el resto se suma."""
    sheet = profile_from(board.characters[name])
    outfit = scene.outfits.get(name)
    if not outfit:
        return sheet
    wear = profile_from(outfit)
    sheet.garments = wear.garments or sheet.garments
    sheet.number = wear.number or (None if wear.garments else sheet.number)
    sheet.accessories |= wear.accessories
    sheet.hairstyles = wear.hairstyles or sheet.hairstyles
    sheet.hair_length = wear.hair_length or sheet.hair_length
    return sheet


# --- Qué se ve -------------------------------------------------------------------------

@dataclass
class Seen:
    tags: dict[str, float] = field(default_factory=dict)  # todas las etiquetas con su confianza

    def best(self, suffix: str) -> tuple[str | None, float]:
        """Mejor color de «*_eyes», «*_hair»…"""
        hits = [(t.rsplit("_", 1)[0], s) for t, s in self.tags.items()
                if t.endswith("_" + suffix) and t.count("_") == 1 and t.split("_")[0] in COLORS and s >= TAG_LOW]
        return max(hits, key=lambda h: h[1]) if hits else (None, 0.0)

    def score(self, *tags: str) -> float:
        return max((self.tags.get(t, 0.0) for t in tags), default=0.0)

    def garments(self) -> dict[str, tuple[str | None, float]]:
        out: dict[str, tuple[str | None, float]] = {}
        for tag, s in sorted(self.tags.items(), key=lambda kv: -kv[1]):
            if s < TAG_LOW:
                continue
            parts = tag.split("_")
            item = parts[-1]
            if item not in GARMENTS.values():
                continue
            color = parts[0] if len(parts) == 2 and parts[0] in COLORS else None
            if item not in out or (out[item][0] is None and color):
                out[item] = (color, max(s, out.get(item, (None, 0.0))[1]))
        return out


# --- Resultados ----------------------------------------------------------------------

@dataclass
class Result:
    character: str
    attribute: str
    expected: str
    detected: str
    level: str
    confidence: float | None
    evidence: str
    requires_review: bool = True  # False: no se puede comprobar, pero el guion lo explica (de espaldas)


def _r(name, attr, exp, det, level, conf, evidence, review=True) -> Result:
    return Result(name, attr, exp, det, level, None if conf is None else round(float(conf), 3), evidence,
                  review if level != OK else False)


def _color_check(name, attr, expected: set[str], seen: tuple[str | None, float], tag: str) -> Result:
    color, s = seen
    exp = "/".join(sorted(expected))
    if not color:
        return _r(name, attr, exp, "-", UNCHECKABLE, None, f"el etiquetador no ve ningún «*_{tag}»")
    if color in expected:
        return _r(name, attr, exp, color, OK, s, f"{color}_{tag} {s:.2f}")
    return _r(name, attr, exp, color, CONFIRMED if s >= TAG_HIGH else POSSIBLE, s, f"{color}_{tag} {s:.2f}")


def compare(name: str, exp: Profile, seen: Seen, *, hidden: bool = False, ocr: Callable | None = None,
            crop=None) -> list[Result]:
    """Cada rasgo esperado de la ficha y la ropa vigente, frente a lo que ve el etiquetador."""
    out: list[Result] = []
    behind = "de espaldas según el guion"
    if exp.eyes:
        if hidden:
            out.append(_r(name, "ojos", "/".join(sorted(exp.eyes)), "-", UNCHECKABLE, None, behind, False))
        elif seen.score("closed_eyes") >= TAG_HIGH:
            out.append(_r(name, "ojos", "/".join(sorted(exp.eyes)), "cerrados", UNCHECKABLE, None,
                          f"closed_eyes {seen.score('closed_eyes'):.2f}"))
        else:
            out.append(_color_check(name, "ojos", exp.eyes, seen.best("eyes"), "eyes"))
    if exp.hair_color:
        out.append(_color_check(name, "color de pelo", exp.hair_color, seen.best("hair"), "hair"))
    if exp.hair_length:
        lengths = [(t, seen.score(t)) for t in HAIR_LENGTHS if seen.score(t) >= TAG_LOW]
        if not lengths:
            out.append(_r(name, "largo de pelo", exp.hair_length, "-", UNCHECKABLE, None, "sin etiqueta de largo"))
        else:
            tag, s = max(lengths, key=lambda x: x[1])
            gap = abs(HAIR_LENGTHS.index(tag) - HAIR_LENGTHS.index(exp.hair_length))
            level = OK if gap == 0 else CONFIRMED if gap > 1 and s >= TAG_HIGH else POSSIBLE
            out.append(_r(name, "largo de pelo", exp.hair_length, tag, level, s, f"{tag} {s:.2f}"))
    for style in sorted(exp.hairstyles):
        s = seen.score(style)
        out.append(_r(name, "peinado", style, style if s >= TAG_LOW else "-", OK if s >= TAG_LOW else POSSIBLE,
                      s, f"{style} {s:.2f}"))
    if exp.facial_hair is not None:
        s = seen.score(*FACIAL_HAIR)
        if hidden:
            out.append(_r(name, "barba", "sí" if exp.facial_hair else "no", "-", UNCHECKABLE, None, behind, False))
        elif exp.facial_hair is False:
            level = OK if s < TAG_LOW else CONFIRMED if s >= TAG_HIGH else POSSIBLE
            out.append(_r(name, "barba", "no", "sí" if s >= TAG_LOW else "no", level, s if level != OK else 1 - s,
                          f"barba/bigote {s:.2f}"))
        else:
            out.append(_r(name, "barba", "sí", "sí" if s >= TAG_LOW else "no", OK if s >= TAG_LOW else POSSIBLE, s,
                          f"barba/bigote {s:.2f}"))
    if exp.age:
        out.append(_age_check(name, exp.age, seen, hidden))
    for acc in sorted(exp.accessories):
        s = seen.score(acc)
        out.append(_r(name, "accesorio", acc, acc if s >= TAG_LOW else "-", OK if s >= TAG_LOW else POSSIBLE, s,
                      f"{acc} {s:.2f}"))
    for acc in sorted(exp.no_accessories):
        s = seen.score(acc)
        if s >= TAG_LOW:
            out.append(_r(name, "accesorio", f"sin {acc}", acc, CONFIRMED if s >= TAG_HIGH else POSSIBLE, s,
                          f"{acc} {s:.2f}"))
    worn = seen.garments()
    for garment, colors in exp.garments.items():
        exp_text = " ".join(filter(None, ["/".join(sorted(colors)), garment]))
        if garment in worn:
            color, s = worn[garment]
            if colors and color and color not in colors:
                out.append(_r(name, "ropa", exp_text, f"{color} {garment}", CONFIRMED if s >= TAG_HIGH else POSSIBLE,
                              s, f"{color}_{garment} {s:.2f}"))
            elif colors and not color:
                out.append(_r(name, "ropa", exp_text, garment, UNCHECKABLE, None,
                              f"{garment} {s:.2f}, sin color reconocible"))
            else:
                out.append(_r(name, "ropa", exp_text, f"{color or ''} {garment}".strip(), OK, s, f"{garment} {s:.2f}"))
        elif worn:
            other, (color, s) = max(worn.items(), key=lambda kv: kv[1][1])
            out.append(_r(name, "ropa", exp_text, f"{color or ''} {other}".strip(),
                          CONFIRMED if s >= TAG_HIGH else POSSIBLE, s, f"{other} {s:.2f}, ningún {garment}"))
        else:
            out.append(_r(name, "ropa", exp_text, "-", UNCHECKABLE, None, "el etiquetador no ve ninguna prenda"))
    if exp.number:
        writing = seen.score(*WRITING)
        if ocr is None:
            out.append(_r(name, "número", exp.number, "-", UNCHECKABLE, None,
                          f"OCR no disponible (modelo no descargado); escritura en la ropa {writing:.2f}: revisar a ojo"))
        else:
            text = ocr(crop) or ""
            found = exp.number in re.sub(r"\s", "", text)
            out.append(_r(name, "número", exp.number, text or "-", OK if found else POSSIBLE, None,
                          f"OCR: «{text}»" + ("" if found else " (el OCR falla con números dibujados: revisar a ojo)")))
    return out


def _age_check(name: str, expected: str, seen: Seen, hidden: bool) -> Result:
    old, child, mature = seen.score("old_man", "old_woman"), seen.score("child", "aged_down"), \
        seen.score("mature_male", "mature_female")
    evidence = f"old {old:.2f}, child {child:.2f}, mature {mature:.2f}"
    if hidden:
        return _r(name, "edad", expected, "-", UNCHECKABLE, None, "de espaldas según el guion", False)
    if expected == "old":
        return _r(name, "edad", "old", "old" if old >= TAG_LOW else "no aparenta", OK if old >= TAG_LOW else POSSIBLE,
                  old, evidence)
    if expected == "child":
        if child >= TAG_LOW:
            return _r(name, "edad", "child", "child", OK, child, evidence)
        return _r(name, "edad", "child", "adulto?", POSSIBLE, 1 - child, evidence)
    for score, label in ((old, "old"), (child, "child")):
        if score >= TAG_LOW:
            return _r(name, "edad", expected, label, CONFIRMED if score >= TAG_HIGH else POSSIBLE, score, evidence)
    if expected == "adult" and mature >= TAG_LOW:
        return _r(name, "edad", "adult", "adult", OK, mature, evidence)
    # Joven sin señales en contra: el etiquetador no tiene una etiqueta que lo confirme.
    return _r(name, "edad", expected, "-", UNCHECKABLE, None, evidence + " (sin etiqueta que lo confirme)", False)


def face_check(name: str, difference: float | None, against: str, hidden: bool) -> Result:
    if hidden:
        return _r(name, f"cara ({against})", "misma cara", "-", UNCHECKABLE, None, "de espaldas según el guion", False)
    if difference is None:
        return _r(name, f"cara ({against})", "misma cara", "-", UNCHECKABLE, None, "sin referencia con la que comparar")
    level = OK if difference <= FACE_POSSIBLE else POSSIBLE if difference <= FACE_CONFIRMED else CONFIRMED
    if against != "ficha" and level == CONFIRMED:
        level = POSSIBLE  # la escena anterior no es la ficha: solo avisa
    return _r(name, f"cara ({against})", "misma cara", f"diferencia {difference:.2f}", level,
              difference, f"CCIP {difference:.3f} (posible > {FACE_POSSIBLE}, confirmado > {FACE_CONFIRMED})")


def previous_check(name: str, exp: Profile, seen: Seen, prev: tuple[str, Seen] | None) -> list[Result]:
    """Lo que la ficha no dice, frente a la aparición válida anterior. Solo POSSIBLE."""
    if not prev:
        return []
    label, before = prev
    out = []
    for attr, key, unset in (("ojos", "eyes", not exp.eyes), ("color de pelo", "hair", not exp.hair_color)):
        now, s = seen.best(key)
        was, _ = before.best(key)
        if unset and now and was and now != was:
            out.append(_r(name, attr, f"{was} (escena {label})", now, POSSIBLE, s, f"{now}_{key} {s:.2f}"))
    return out


# --- Con modelos -------------------------------------------------------------------------

@dataclass
class Tools:
    detect: Callable  # imagen -> [(caja, confianza)]
    tag: Callable  # imagen -> {etiqueta: confianza}
    difference: Callable  # (imagen, imagen) -> diferencia CCIP
    ocr: Callable | None = None  # imagen -> texto; None si no hay modelo de OCR


def default_tools() -> Tools:
    from imgutils.detect import detect_person
    from imgutils.metrics import ccip_difference
    from imgutils.tagging import get_wd14_tags

    def tag(image):
        # Umbral bajo para poder ver también lo que está «casi» (barba 0.2, ojos cerrados…).
        _, general, _ = get_wd14_tags(image, general_threshold=0.15)
        return general

    return Tools(lambda im: [(b, s) for b, _, s in detect_person(im)], tag,
                 lambda a, b: float(ccip_difference(a, b)), ocr=None)


@dataclass
class ImageReport:
    label: str
    scene: int
    shot: int
    image: str
    characters: list[str]
    results: list[Result]
    sha256: str = ""  # contenido revisado: si el archivo cambia después, la revisión ya no vale

    @property
    def status(self) -> str:
        levels = {r.level for r in self.results}
        if CONFIRMED in levels:
            return "ERROR"
        if POSSIBLE in levels or any(r.level == UNCHECKABLE and r.requires_review for r in self.results):
            return "REVISAR"
        return "OK"


def check(board: Storyboard, images: list[list[Path]], portraits: Path, tools: Tools | None = None) -> list[ImageReport]:
    """images: los planos de cada escena, en el orden de board.scenes."""
    from PIL import Image

    tools = tools or default_tools()
    faces = {c: Image.open(portraits / f"{c}.png").convert("RGB")
             for c in board.characters if (portraits / f"{c}.png").exists()}
    last_valid: dict[str, tuple[str, Seen, object]] = {}
    reports = []
    for scene, shots in zip(board.scenes, images):
        hidden = cast_hidden(scene)
        for k, path in enumerate(shots):
            label = f"{scene.number:03d}" + (chr(ord("a") + k) if len(shots) > 1 else "")
            image = Image.open(path).convert("RGB")
            crops = [image.crop(box) for box, score in tools.detect(image) if score > PERSON_SCORE]
            crops.sort(key=lambda c: -c.width * c.height)
            assigned = dict(_assign(scene.characters, crops, faces, tools.difference))
            results: list[Result] = []
            for name in scene.characters:
                if name not in faces:
                    results.append(_r(name, "ficha", "rostro de referencia", "-", CONFIRMED, None,
                                      f"falta {name}.png en {portraits.name}"))
                    continue
                crop = assigned.get(name)
                if crop is None:
                    results.append(_r(name, "presencia", "en la imagen", "-", POSSIBLE, None,
                                      "el detector no encuentra a este personaje", not hidden))
                    continue
                if crop.height < MIN_CROP:
                    results.append(_r(name, "tamaño", f">= {MIN_CROP}px", f"{crop.height}px", UNCHECKABLE, None,
                                      "demasiado pequeño para comprobar rasgos"))
                    continue
                seen = Seen(tools.tag(crop))
                exp = expected_for(board, scene, name)
                prev = last_valid.get(name)
                char_results = compare(name, exp, seen, hidden=hidden, ocr=tools.ocr, crop=crop)
                char_results.append(face_check(name, tools.difference(faces[name], crop), "ficha", hidden))
                if prev:
                    char_results.append(face_check(name, tools.difference(prev[2], crop), f"escena {prev[0]}", hidden))
                char_results += previous_check(name, exp, seen, prev[:2] if prev else None)
                if not any(r.level == CONFIRMED for r in char_results):
                    last_valid[name] = (label, seen, crop)
                results += char_results
            reports.append(ImageReport(label, scene.number, k, path.name, list(scene.characters), results,
                                       file_hash(path)))
    return reports


def cast_hidden(scene: Scene) -> bool:
    """¿Los @personajes de la escena salen de espaldas?

    «back view» en una escena con más personas que @personajes se refiere a la persona extra
    (descrita con palabras, sin ficha): los @personajes siguen de cara y se comprueban."""
    from .review import expected_people, scene_people_text

    if not HIDDEN.search(scene.image):
        return False
    people = expected_people(scene_people_text(scene))
    return not (people is not None and people > len(scene.characters))


def _assign(cast: list[str], crops: list, faces: dict, difference) -> list[tuple[str, object]]:
    """Empareja cada personaje con el recorte que más se parece a su ficha (de mayor a menor parecido)."""
    known = [c for c in cast if c in faces]
    if len(known) == 1:
        return [(known[0], crops[0])] if crops else []
    pairs = sorted((difference(faces[c], crop), c, i) for c in known for i, crop in enumerate(crops))
    used_c, used_i, out = set(), set(), []
    for _, c, i in pairs:
        if c not in used_c and i not in used_i:
            used_c.add(c)
            used_i.add(i)
            out.append((c, crops[i]))
    return out


PEOPLE_LEVEL = {"OK": OK, "DUPLICADO": CONFIRMED, "DUDOSO": POSSIBLE, "SIN CARA": POSSIBLE, "SIN CONTAR": UNCHECKABLE}


def add_people_checks(reports: list[ImageReport], checks: list) -> None:
    """Suma el recuento de personas de review.check (duplicados) a cada imagen del informe,
    para que el bloqueo de montaje también los tenga en cuenta."""
    by_label = {c.label: c for c in checks}
    for rep in reports:
        c = by_label.get(rep.label)
        if c is None:
            continue
        rep.results.append(_r("(escena)", "personas", "-" if c.expected is None else str(c.expected),
                              f"{c.faces} caras, {c.heads} cabezas", PEOPLE_LEVEL[c.status], None,
                              f"recuento de caras: {c.status}"))


# --- Antes de producir ---------------------------------------------------------------------

def preflight(board: Storyboard, portraits: Path, tag: Callable | None = None) -> list[Result]:
    """Ficha, rostro de referencia, vestuario y miniatura, antes de generar ninguna escena.

    tag: el etiquetador para comparar cada rostro elegido con su ficha; sin él, solo se hacen las
    comprobaciones de texto y las del rostro salen como NOT CHECKABLE."""
    from PIL import Image

    out: list[Result] = []
    used = {c for s in board.scenes for c in s.characters}
    if board.thumbnail:
        used |= set(board.thumbnail.characters)
    for name in sorted(used):
        face = portraits / f"{name}.png"
        if not face.exists():
            out.append(_r(name, "rostro de referencia", f"{face.name}", "-", CONFIRMED, None,
                          "falta: ejecuta «personajes» y «elegir»"))
            continue
        sheet = profile_from(board.characters[name])
        sheet.garments, sheet.number = {}, None  # la ropa del retrato no es la de las escenas
        if tag is None:
            out.append(_r(name, "rostro vs ficha", "-", "-", UNCHECKABLE, None, "sin etiquetador"))
            continue
        for r in compare(name, sheet, Seen(tag(Image.open(face).convert("RGB")))):
            r.attribute = f"rostro vs ficha: {r.attribute}"
            out.append(r)
    for name in sorted(used):
        in_sheet = profile_from(board.characters[name]).garments
        changed = [s.number for s in board.scenes if name in s.outfits and profile_from(s.outfits[name]).garments]
        if in_sheet and changed:
            out.append(_r(name, "vestuario", "ropa solo en [ropa] de la escena",
                          f"ficha: {', '.join(sorted(in_sheet))}", CONFIRMED, None,
                          f"la ficha incluye ropa y las escenas {changed[:5]} ponen otra: el generador recibe las dos"))
    if board.thumbnail:
        worn = {(c, o) for s in board.scenes for c, o in s.outfits.items()}
        for name, outfit in board.thumbnail.outfits.items():
            if (name, outfit) not in worn and any(c == name for c, _ in worn):
                out.append(_r(name, "miniatura", "ropa de alguna escena", outfit, POSSIBLE, None,
                              "la miniatura le pone ropa que no lleva en ninguna escena"))
    return out


# --- Informes ------------------------------------------------------------------------------

def write_report(reports: list[ImageReport], pre: list[Result], path: Path) -> None:
    data = {
        "version": REPORT_VERSION,
        "preflight": [asdict(r) for r in pre],
        "images": [{**{k: v for k, v in asdict(rep).items() if k != "results"}, "status": rep.status,
                    "results": [asdict(r) for r in rep.results]} for rep in reports],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def report_text(reports: list[ImageReport], pre: list[Result] | None = None) -> str:
    lines = []
    if pre:
        bad = [r for r in pre if r.level != OK]
        lines.append(f"Antes de producir: {len(bad)} avisos.")
        lines += [f"  {r.level:13} @{r.character} {r.attribute}: espera {r.expected}, hay {r.detected} ({r.evidence})"
                  for r in bad]
    if not reports:  # solo la comprobación previa: no se ha revisado ninguna imagen
        return "\n".join(lines)
    counts = {s: sum(1 for r in reports if r.status == s) for s in ("OK", "REVISAR", "ERROR")}
    lines.append(f"Coherencia: {counts['ERROR']} con errores, {counts['REVISAR']} por revisar, {counts['OK']} correctas.")
    for rep in reports:
        shown = [r for r in rep.results if r.level != OK and (r.level != UNCHECKABLE or r.requires_review)]
        if not shown:
            continue
        lines.append(f"  [{rep.label}] {rep.status}")
        for r in shown:
            conf = "" if r.confidence is None else f" conf {r.confidence:.2f}"
            lines.append(f"    {r.level:13} @{r.character} {r.attribute}: espera {r.expected}, "
                         f"detectado {r.detected}{conf} — {r.evidence}")
    return "\n".join(lines)


# --- Bloqueo antes de montar ----------------------------------------------------------------

def load_approvals(folder: Path) -> dict:
    path = folder / "aprobadas.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def file_hash(path: Path) -> str:
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def approve(folder: Path, report_path: Path, labels: list[str]) -> list[str]:
    """Marca como revisadas a ojo las imágenes de esas etiquetas del último informe.

    La aprobación vale solo para ese archivo con ese contenido: si la imagen se regenera o se
    retoca, hay que revisarla y aprobarla otra vez."""
    data = json.loads(report_path.read_text(encoding="utf-8"))
    by_label = {img["label"]: img for img in data["images"]}
    unknown = [l for l in labels if l not in by_label]
    if unknown:
        raise SystemExit(f"No están en el informe: {', '.join(unknown)}")
    approvals = load_approvals(folder)
    approvals.update({by_label[l]["image"]: {"label": l, "sha256": by_label[l]["sha256"]} for l in labels})
    (folder / "aprobadas.json").write_text(json.dumps(approvals, ensure_ascii=False, indent=2), encoding="utf-8")
    return [by_label[l]["image"] for l in labels]


def blockers(report_path: Path, approvals: dict, images: list[Path]) -> list[str]:
    """Imágenes que no pueden pasar al vídeo: sin revisar, o con fallos que nadie ha aprobado."""
    if not report_path.exists():
        return ["no hay informe de coherencia: ejecuta «revisar»"]
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if data.get("version") != REPORT_VERSION:
        return ["el informe es de otra versión: vuelve a ejecutar «revisar»"]
    status = {img["image"]: img for img in data["images"]}
    out = []
    for path in images:
        if path.name not in status:
            out.append(f"{path.name}: sin revisar (nueva o regenerada después del informe)")
            continue
        img = status[path.name]
        label, st, current = img["label"], img["status"], file_hash(path)
        if current != img.get("sha256"):
            out.append(f"[{label}] modificada después del informe: vuelve a ejecutar «revisar»")
            continue
        ok = approvals.get(path.name)
        if st != "OK" and not (isinstance(ok, dict) and ok.get("sha256") == current):
            out.append(f"[{label}] {st}: falta aprobarla tras mirarla («aprobar» {label})")
    return out
