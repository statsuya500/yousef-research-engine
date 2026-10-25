"""Comprobación de coherencia: que cada personaje salga igual en todas las escenas.

Para cada imagen se recorta a cada persona (detector anime de imgutils), se le pasa el
etiquetador WD14 («green_eyes», «brown_hair», «grey_hoodie»…) y se compara con:
- lo que dice su ficha y la ropa que lleva en esa escena (color de ojos, pelo, prenda y su
  color, un número en la camiseta);
- lo que sale en el resto de sus apariciones: si en 9 escenas tiene los ojos verdes y en una
  rojos, esa es la que falla aunque la ficha no diga el color.
Con varios personajes en la imagen, cada recorte se asigna al personaje cuya ficha se le
parece más (CCIP, parecido de personajes anime).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .storyboard import Storyboard

TAG_SCORE = 0.35  # confianza mínima del etiquetador
PERSON_SCORE = 0.4
COLORS = {"black", "white", "grey", "brown", "blonde", "red", "orange", "yellow", "green", "blue",
          "purple", "pink", "aqua", "silver", "beige"}
# Colores de las fichas que el etiquetador llama de otra forma (o puede llamar de varias).
SYNONYMS = {
    "gray": {"grey"}, "silver": {"silver", "grey", "white"}, "blond": {"blonde"}, "golden": {"blonde", "yellow"},
    "auburn": {"brown", "red", "orange"}, "chestnut": {"brown"}, "hazel": {"brown", "green", "yellow"},
    "navy": {"blue", "black"}, "cream": {"white", "beige"}, "beige": {"beige", "white", "brown"},
    "violet": {"purple"}, "lavender": {"purple"}, "light": set(), "dark": set(),
}
# Prenda de la ficha -> etiqueta del etiquetador.
GARMENTS = {"t-shirt": "shirt", "shirt": "shirt", "blouse": "shirt", "sweater": "sweater", "jumper": "sweater",
            "hoodie": "hoodie", "jacket": "jacket", "windbreaker": "jacket", "coat": "coat", "dress": "dress",
            "suit": "suit", "skirt": "skirt", "cardigan": "cardigan", "vest": "vest", "uniform": "uniform"}
HIDDEN = re.compile(r"\b(back view|from behind|seen from behind|face not visible|no face)\b")


@dataclass
class Expected:
    eyes: set[str] = field(default_factory=set)
    hair: set[str] = field(default_factory=set)
    garments: dict[str, set[str]] = field(default_factory=dict)  # prenda -> colores admitidos
    number: str | None = None


@dataclass
class Seen:
    eyes: str | None = None
    hair: str | None = None
    garments: dict[str, str | None] = field(default_factory=dict)  # prenda -> color (o None)


@dataclass
class Finding:
    label: str  # «007b»
    character: str
    problem: str


def _colors(phrase: str) -> set[str]:
    out: set[str] = set()
    for word in re.findall(r"[a-z]+", phrase.lower()):
        if word in SYNONYMS:
            out |= SYNONYMS[word]
        elif word in COLORS:
            out.add(word)
    return out


def expected_from(text: str) -> Expected:
    """Rasgos comprobables de una ficha más su ropa: «green eyes, short auburn hair, green shirt with number 10»."""
    exp = Expected()
    for phrase in (p.strip().lower() for p in text.split(",")):
        if m := re.search(r"number (\d+)", phrase):
            exp.number = m.group(1)
        if re.search(r"\beyes?\b", phrase):
            exp.eyes |= _colors(phrase)
        elif re.search(r"\bhair\b", phrase):
            exp.hair |= _colors(phrase.split("with")[0])  # «hair with grey streaks»: el color principal
        for word, tag in GARMENTS.items():
            if re.search(rf"\b{re.escape(word)}\b", phrase):
                exp.garments.setdefault(tag, set()).update(_colors(phrase.split("with")[0]))
                break
    return exp


def seen_from(tags: dict[str, float]) -> Seen:
    """Rasgos que el etiquetador ve en un recorte: el color más probable de ojos, pelo y cada prenda."""
    seen = Seen()
    best: dict[str, float] = {}
    for tag, score in sorted(tags.items(), key=lambda kv: -kv[1]):
        if score < TAG_SCORE:
            continue
        parts = tag.split("_")
        color, item = (parts[0], parts[-1]) if len(parts) >= 2 else (None, parts[0])
        if color not in COLORS:
            color = None
        if item == "eyes" and color and "eyes" not in best:
            seen.eyes, best["eyes"] = color, score
        elif item == "hair" and color and len(parts) == 2 and "hair" not in best:
            seen.hair, best["hair"] = color, score
        elif item in GARMENTS.values() and seen.garments.get(item) is None:
            seen.garments[item] = color
    return seen


def compare(exp: Expected, seen: Seen, ocr_text: str | None = None) -> list[str]:
    problems = []
    if exp.eyes and seen.eyes and seen.eyes not in exp.eyes:
        problems.append(f"ojos {seen.eyes}, la ficha dice {'/'.join(sorted(exp.eyes))}")
    if exp.hair and seen.hair and seen.hair not in exp.hair:
        problems.append(f"pelo {seen.hair}, la ficha dice {'/'.join(sorted(exp.hair))}")
    for garment, colors in exp.garments.items():
        if garment in seen.garments:
            color = seen.garments[garment]
            if colors and color and color not in colors:
                problems.append(f"{garment} {color}, debería ser {'/'.join(sorted(colors))}")
        elif seen.garments:
            other = ", ".join(f"{c + ' ' if c else ''}{g}" for g, c in seen.garments.items())
            problems.append(f"lleva {other} en vez de {garment}")
    if exp.number and ocr_text is not None and exp.number not in ocr_text:
        problems.append(f"no se ve el número {exp.number}")
    return problems


def outliers(appearances: list[tuple[str, Seen]], min_count: int = 3, majority: float = 0.6) -> list[tuple[str, str]]:
    """Apariciones que no coinciden con lo que el personaje lleva casi siempre (aunque la ficha no lo diga)."""
    found = []
    traits = {"ojos": lambda s: s.eyes, "pelo": lambda s: s.hair}
    for name, get in traits.items():
        values = [(label, get(s)) for label, s in appearances if get(s)]
        if len(values) < min_count:
            continue
        common, n = Counter(v for _, v in values).most_common(1)[0]
        if n / len(values) >= majority:
            found += [(label, f"{name} {v}, en el resto de escenas {common}") for label, v in values if v != common]
    return found


# --- Con modelos (imgutils) ----------------------------------------------------------

def check(board: Storyboard, images: list[list[Path]], portraits: Path) -> list[Finding]:
    """images: los planos de cada escena, en el orden de board.scenes."""
    from PIL import Image
    from imgutils.detect import detect_person
    from imgutils.metrics import ccip_difference
    from imgutils.ocr import ocr
    from imgutils.tagging import get_wd14_tags

    findings: list[Finding] = []
    history: dict[str, list[tuple[str, Seen]]] = defaultdict(list)
    faces = {c: Image.open(portraits / f"{c}.png").convert("RGB")
             for c in board.characters if (portraits / f"{c}.png").exists()}
    for scene, shots in zip(board.scenes, images):
        cast = [c for c in scene.characters if c in faces]
        if not cast:
            continue
        hidden = bool(HIDDEN.search(scene.image))
        for k, path in enumerate(shots):
            label = f"{scene.number:03d}" + (chr(ord("a") + k) if len(shots) > 1 else "")
            image = Image.open(path).convert("RGB")
            crops = [image.crop(box) for box, _, score in detect_person(image) if score > PERSON_SCORE]
            crops.sort(key=lambda c: -c.width * c.height)
            for name, crop in _assign(cast, crops, faces, ccip_difference):
                _, tags, _ = get_wd14_tags(crop)
                seen = seen_from(tags)
                if hidden:
                    seen.eyes = None  # de espaldas no se le ven los ojos
                exp = expected_from(", ".join(p for p in (board.characters[name], scene.outfits.get(name, "")) if p))
                text = " ".join(t for _, t, _ in ocr(crop)) if exp.number else None
                findings += [Finding(label, name, p) for p in compare(exp, seen, text)]
                history[name].append((label, seen))
    for name, appearances in history.items():
        findings += [Finding(label, name, p) for label, p in outliers(appearances)]
    return sorted(findings, key=lambda f: (f.label, f.character))


def _assign(cast: list[str], crops: list, faces: dict, difference) -> list[tuple[str, object]]:
    """Empareja cada personaje de la escena con el recorte que más se parece a su ficha."""
    if len(cast) == 1:
        return [(cast[0], crops[0])] if crops else []
    pairs = sorted(((difference(faces[c], crop), c, i) for c in cast for i, crop in enumerate(crops)))
    used_c, used_i, out = set(), set(), []
    for _, c, i in pairs:
        if c not in used_c and i not in used_i:
            used_c.add(c)
            used_i.add(i)
            out.append((c, crops[i]))
    return out


def report(findings: list[Finding]) -> str:
    if not findings:
        return "Coherencia: todos los personajes salen como en su ficha y en el resto de escenas."
    lines = [f"Coherencia: {len(findings)} posibles fallos."]
    lines += [f"  [{f.label}] @{f.character}: {f.problem}" for f in findings]
    return "\n".join(lines)
