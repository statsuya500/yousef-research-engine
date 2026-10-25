"""Continuidad visual automática: generar candidatas de una escena hasta que cumplan las fichas.

Piezas (todas reutilizan storyboard, images, coherencia y review):

1. Registro de continuidad (`<historia>_continuidad.json`): por personaje, atributos permanentes
   (ojos, pelo, edad…) sacados de su ficha y medidos en su rostro de referencia, y atributos
   variables (ropa) con la escena de la que salen y su color medido en esa imagen. Un archivo de
   especificación opcional añade lo que la ficha no dice (p. ej. «pelo que cubre las orejas») y la
   composición que exige el guion de cada escena.
2. Evaluación: cada requisito sale PASS, FAIL, UNCERTAIN o N/A (no visible según el guion).
   Ninguna herramienta decide sola: el etiquetador WD14 y la medida de color por regiones tienen que
   coincidir para un PASS; si se contradicen, UNCERTAIN. CCIP no es prueba de identidad: un parecido
   bajo es FAIL, uno dudoso UNCERTAIN.
3. Bucle: lotes de candidatas con semillas reproducibles; si ninguna es válida, se corrige solo lo
   que falló (sin contradecir los atributos de otro personaje presente) y, si el mismo fallo se
   repite, se cambia de estrategia (p. ej. el segundo personaje de espaldas sin referencia facial).
   Termina en VALID_CANDIDATE o NO_VALID_CANDIDATE. Nunca sustituye imágenes definitivas ni aprueba.
"""

from __future__ import annotations

import colorsys
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from . import coherencia as co
from .storyboard import Scene, Storyboard, parse

PASS, FAIL, UNCERTAIN, NA = "PASS", "FAIL", "UNCERTAIN", "N/A"
REGISTRY_VERSION = 1

# Umbrales calibrados con imágenes de la historia de prueba (ver docs del módulo y tests):
# pelo de Daniel 4.8-5.5 bien / 22 mal; sudadera 7-14 bien / 28 mal; pelo de Clara 7-16 / 23-34.
COLOR_PASS = 15.0  # ΔE (CIELAB) hasta aquí: mismo color que la referencia
COLOR_FAIL = 25.0  # ΔE desde aquí: otro color
# Ojos: tono y saturación medianos del iris frente a los del rostro de referencia.
# Gris de Clara: tono ~335°, sat 0.22; cálidos (que el etiquetador llama marrón) ~11-15°.
IRIS_HUE_PASS, IRIS_HUE_FAIL = 25.0, 40.0
IRIS_SAT_PASS = 0.12
# Peinados que el etiquetador no reconoce de forma fiable: se comprueban solo por el largo.
UNRELIABLE_STYLES = {"bob_cut"}
# Estilo: brillo, saturación y contraste (0-100) frente a la media de las escenas de referencia.
STYLE_TOLERANCE = (12.0, 10.0, 10.0)
LIKENESS_STEP, LIKENESS_MAX = 0.1, 0.8


# --- Medidas de color ----------------------------------------------------------------------

def lab(rgb) -> np.ndarray:
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = m @ c / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def delta_e(a, b) -> float:
    return float(np.linalg.norm(lab(a) - lab(b)))


def region_color(image, box, rows: tuple[float, float], dark: bool = False) -> list[int]:
    """Color mediano de una franja horizontal (centro del recorte de la persona).

    rows (0.60, 0.95): ropa del torso; (0.0, 0.25) con dark=True: pelo (la mitad más oscura)."""
    a = np.asarray(image.crop(box)).astype(float)
    h, w = a.shape[:2]
    px = a[int(h * rows[0]):max(int(h * rows[1]), int(h * rows[0]) + 1), int(w * .25):max(int(w * .75), 1)]
    px = px.reshape(-1, 3)
    if dark and len(px):
        px = px[px.mean(1) <= np.percentile(px.mean(1), 40)]
    return [int(v) for v in np.median(px, 0)] if len(px) else [0, 0, 0]


def iris_color(image, face_box) -> tuple[float, float]:
    """(saturación, tono en grados) medianos de la banda de los ojos de una cara."""
    x0, y0, x1, y1 = face_box
    w, h = x1 - x0, y1 - y0
    a = np.asarray(image.crop((x0 + int(w * .1), y0 + int(h * .35), x1 - int(w * .1), y0 + int(h * .65))))
    px = a.reshape(-1, 3).astype(float) / 255
    lum = px.mean(1)
    px = px[(lum > 0.15) & (lum < 0.62)]  # ni el blanco del ojo ni la pupila negra
    if not len(px):
        return 0.0, 0.0
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px[:: max(1, len(px) // 4000)]])
    return float(np.median(hsv[:, 1])), float(np.median(hsv[:, 0]) * 360)


def hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def style_stats(image) -> tuple[float, float, float]:
    from PIL import ImageStat

    s = ImageStat.Stat(image.convert("RGB").resize((256, 144)).convert("HSV"))
    return s.mean[2] / 2.55, s.mean[1] / 2.55, s.stddev[2] / 2.55


# --- Registro de continuidad ------------------------------------------------------------------

def _file_sha(path: Path) -> str:
    return co.file_hash(path) if Path(path).exists() else ""


def build_registry(board: Storyboard, portraits: Path, scene_images: dict[int, Path], reference_scenes: set[int],
                   spec: dict, tools: co.Tools) -> dict:
    """Atributos de cada personaje con su valor esperado, de dónde sale y si es permanente.

    scene_images: la imagen vigente de cada escena; reference_scenes: las que son fuente de verdad
    (aprobadas o correctas), de las que se mide el color de la ropa."""
    from PIL import Image

    chars = {}
    for name, text in board.characters.items():
        prof = co.profile_from(text)
        extra = spec.get("personajes", {}).get(name, {})
        face_path = portraits / f"{name}.png"
        entry = {"ficha": text, "rostro": str(face_path), "rostro_sha256": _file_sha(face_path),
                 "permanentes": {}, "ropa": [], "extra_prompt": extra.get("prompt", ""),
                 "detras_prompt": extra.get("detras_prompt", "")}
        perm = entry["permanentes"]
        if prof.eyes:
            perm["ojos"] = {"esperado": sorted(prof.eyes), "origen": f"ficha {name}"}
        if prof.hair_color:
            perm["color de pelo"] = {"esperado": sorted(prof.hair_color), "origen": f"ficha {name}"}
        length = extra.get("hair_length") or prof.hair_length
        if length:
            perm["largo de pelo"] = {"esperado": length, "origen": "especificación" if extra.get("hair_length")
                                     else f"ficha {name}"}
        if prof.age:
            perm["edad"] = {"esperado": prof.age, "origen": f"ficha {name}"}
        if prof.facial_hair is not None:
            perm["barba"] = {"esperado": prof.facial_hair, "origen": f"ficha {name}"}
        if face_path.exists():
            face = Image.open(face_path).convert("RGB")
            boxes = [b for b, s in (tools.faces(face) if tools.faces else []) if s > 0.4]
            if boxes and "ojos" in perm:
                sat, hue = iris_color(face, max(boxes, key=lambda b: b[2] - b[0]))
                perm["ojos"]["medida"] = {"sat": round(sat, 3), "hue": round(hue, 1), "fuente": face_path.name}
            if "color de pelo" in perm:
                perm["color de pelo"]["medida"] = {"rgb": region_color(face, (0, 0, *face.size), (0.0, 0.25), True),
                                                   "fuente": face_path.name}
        chars[name] = entry
    # Ropa: cada cambio de ropa del guion, medido en la primera escena de referencia que la lleva.
    for scene in board.scenes:
        for name, outfit in scene.outfits.items():
            outfits = chars[name]["ropa"]
            if outfits and outfits[-1]["texto"] == outfit:
                continue
            item = {"texto": outfit, "desde_escena": scene.number, "origen": "guion"}
            path = scene_images.get(scene.number)
            if scene.number in reference_scenes and path and Path(path).exists() and name in scene.characters:
                image = Image.open(path).convert("RGB")
                box = _person_of(name, image, scene.characters, portraits, tools)
                if box:
                    item["medida"] = {"rgb": region_color(image, box, (0.60, 0.95)),
                                      "pelo_rgb": region_color(image, box, (0.0, 0.25), True),
                                      "fuente": Path(path).name, "sha256": _file_sha(path)}
            outfits.append(item)
    style = []
    for number in sorted(reference_scenes):
        path = scene_images.get(number)
        if path and Path(path).exists():
            style.append(style_stats(Image.open(path)))
    return {"version": REGISTRY_VERSION, "personajes": chars,
            "estilo": [round(float(v), 1) for v in np.mean(style, 0)] if style else None}


def _person_of(name: str, image, cast: list[str], portraits: Path, tools: co.Tools):
    from PIL import Image

    boxes = [b for b, s in tools.detect(image) if s > co.PERSON_SCORE]
    if not boxes:
        return None
    if len(cast) == 1:
        return max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    face = Image.open(portraits / f"{name}.png").convert("RGB")
    return min(boxes, key=lambda b: tools.difference(face, image.crop(b)))


def outfit_at(registry: dict, name: str, scene_number: int) -> dict | None:
    """La ropa vigente de un personaje en una escena: la última que el guion le puso antes o en ella."""
    current = None
    for item in registry["personajes"][name]["ropa"]:
        if item["desde_escena"] <= scene_number:
            current = item
    return current


def save_registry(registry: dict, path: Path) -> None:
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Requisitos ---------------------------------------------------------------------------------

@dataclass
class Requirement:
    character: str  # «(escena)» para los de la escena completa
    attribute: str
    expected: str
    status: str  # PASS, FAIL, UNCERTAIN o N/A
    evidence: str
    mandatory: bool = True


LEVEL_TO_STATUS = {co.OK: PASS, co.CONFIRMED: FAIL, co.POSSIBLE: UNCERTAIN}


def _from_level(r: co.Result) -> str:
    if r.level == co.UNCHECKABLE:
        return NA if not r.requires_review else UNCERTAIN
    return LEVEL_TO_STATUS[r.level]


def combine(*statuses: str) -> str:
    """Dos fuentes: PASS solo si todas dicen PASS; FAIL si alguna dice FAIL y ninguna PASS."""
    s = [x for x in statuses if x != NA]
    if not s:
        return NA
    if all(x == PASS for x in s):
        return PASS
    if FAIL in s and PASS not in s:
        return FAIL
    return UNCERTAIN


def worst(statuses: list[str]) -> str:
    s = [x for x in statuses if x != NA] or [NA]
    for level in (FAIL, UNCERTAIN, PASS, NA):
        if level in s:
            return level
    return NA


def color_status(measured, reference) -> tuple[str, str]:
    if reference is None:
        return UNCERTAIN, "sin color de referencia medido"
    d = delta_e(measured, reference)
    status = PASS if d <= COLOR_PASS else FAIL if d >= COLOR_FAIL else UNCERTAIN
    return status, f"ΔE {d:.1f} (rgb {list(measured)} frente a {list(reference)})"


def iris_status(measured: tuple[float, float], reference: dict | None) -> tuple[str, str]:
    if not reference:
        return UNCERTAIN, "sin medida de iris de referencia"
    sat, hue = measured
    dh, ds = hue_distance(hue, reference["hue"]), abs(sat - reference["sat"])
    if dh <= IRIS_HUE_PASS and ds <= IRIS_SAT_PASS:
        status = PASS
    elif dh >= IRIS_HUE_FAIL:
        status = FAIL
    else:
        status = UNCERTAIN
    return status, f"iris tono {hue:.0f}° sat {sat:.2f} (ref {reference['hue']:.0f}° {reference['sat']:.2f}): Δtono {dh:.0f}°"


# --- Especificación de escena -----------------------------------------------------------------------

@dataclass
class SceneSpec:
    number: int
    action: str  # composición y acción, sin @personajes
    cast: list[str]  # @personajes con referencia visual, de izquierda a derecha
    composition: list[str] = field(default_factory=list)  # etiquetas que deben verse (sitting, bench…)
    forbidden: list[str] = field(default_factory=list)  # etiquetas que no pueden verse (standing…)
    behind: list[str] = field(default_factory=list)  # personajes de espaldas, sin referencia facial


def scene_spec(board: Storyboard, number: int, spec: dict) -> SceneSpec:
    scene = next(s for s in board.scenes if s.number == number)
    over = spec.get("escenas", {}).get(str(number), {})
    return SceneSpec(number, over.get("accion", scene.action), over.get("personajes", list(scene.characters)),
                     over.get("composicion", []), over.get("prohibido", []), over.get("detras", []))


# --- Evaluación de una candidata ------------------------------------------------------------------

def evaluate(board: Storyboard, scene: Scene, sspec: SceneSpec, image_path: Path, registry: dict,
             portraits: Path, tools: co.Tools, people_check: Callable) -> list[Requirement]:
    """Todos los requisitos de una candidata. people_check(scene, path) -> review.Check."""
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    report = co.check(Storyboard(characters=board.characters, scenes=[scene]), [[image_path]], portraits, tools)[0]
    by_attr: dict[tuple[str, str], list[co.Result]] = {}
    for r in report.results:
        by_attr.setdefault((r.character, r.attribute), []).append(r)
    reqs: list[Requirement] = []
    crops_by_char = _crops(scene, image, portraits, tools)
    faces = [b for b, s in (tools.faces(image) if tools.faces else []) if s > 0.4]
    for name in scene.characters:
        entry = registry["personajes"][name]
        perm = entry["permanentes"]
        box = crops_by_char.get(name)
        if box is None:
            reqs.append(Requirement(name, "presencia", "en la imagen", FAIL, "el detector no lo encuentra"))
            continue
        crop = image.crop(box)
        # Identidad (CCIP): parecido, no prueba. Bajo = FAIL, dudoso = UNCERTAIN.
        for r in by_attr.get((name, "cara (ficha)"), []):
            reqs.append(Requirement(name, "identidad", "rostro de su ficha", _from_level(r), r.evidence))
        for r in by_attr.get((name, "clon"), []):
            reqs.append(Requirement(name, "clon", "aparece una sola vez", _from_level(r), r.evidence))
        if "ojos" in perm:
            tag = [_from_level(r) for r in by_attr.get((name, "ojos"), [])] or [UNCERTAIN]
            face = _face_in(box, faces)
            if face is None:
                region, ev = UNCERTAIN, "sin cara detectada para medir el iris"
            else:
                region, ev = iris_status(iris_color(image, face), perm["ojos"].get("medida"))
            tag_ev = "; ".join(r.evidence for r in by_attr.get((name, "ojos"), [])) or "etiquetador: nada"
            reqs.append(Requirement(name, "ojos", "/".join(perm["ojos"]["esperado"]), combine(tag[0], region),
                                    f"etiquetador: {tag_ev} | región: {ev}"))
        if "color de pelo" in perm:
            tag = [_from_level(r) for r in by_attr.get((name, "color de pelo"), [])] or [UNCERTAIN]
            region, ev = color_status(region_color(image, box, (0.0, 0.25), True),
                                      (perm["color de pelo"].get("medida") or {}).get("rgb"))
            reqs.append(Requirement(name, "color de pelo", "/".join(perm["color de pelo"]["esperado"]),
                                    combine(tag[0], region), f"región: {ev}"))
        if "largo de pelo" in perm:
            seen = co.Seen(tools.tag(crop))
            res = co.compare(name, co.Profile(hair_length=perm["largo de pelo"]["esperado"]), seen)
            reqs.append(Requirement(name, "largo de pelo", perm["largo de pelo"]["esperado"], _from_level(res[0]),
                                    res[0].evidence))
        for attr in ("barba", "edad"):
            for r in by_attr.get((name, attr), []):
                reqs.append(Requirement(name, attr, str(r.expected), _from_level(r), r.evidence))
        for r in by_attr.get((name, "peinado"), []):
            if r.expected in UNRELIABLE_STYLES:
                continue  # se comprueba por el largo; el etiquetador casi nunca lo reconoce
            reqs.append(Requirement(name, "peinado", r.expected, _from_level(r), r.evidence))
        outfit = outfit_at(registry, name, scene.number)
        if outfit:
            # Tipo de prenda y color son requisitos distintos: un color parecido (blanco ≈ crema) no
            # dice nada de si es un jersey o una sudadera.
            rs = by_attr.get((name, "ropa"), [])
            kinds, tag_colors = [], []
            for r in rs:
                if "ningún" in r.evidence:  # el etiquetador ve otra prenda
                    kinds.append(_from_level(r))
                elif r.level == co.UNCHECKABLE:
                    kinds.append(PASS if "sin color" in r.evidence else UNCERTAIN)
                    tag_colors.append(UNCERTAIN)
                else:
                    kinds.append(PASS)
                    tag_colors.append(_from_level(r))
            evidence = "; ".join(r.evidence for r in rs) or "el etiquetador no ve prendas"
            reqs.append(Requirement(name, "prenda", outfit["texto"], worst(kinds or [UNCERTAIN]),
                                    f"etiquetador: {evidence}"))
            region, ev = color_status(region_color(image, box, (0.60, 0.95)),
                                      (outfit.get("medida") or {}).get("rgb"))
            reqs.append(Requirement(name, "color de ropa", outfit["texto"],
                                    combine(worst(tag_colors or [UNCERTAIN]), region),
                                    f"etiquetador: {evidence} | región: {ev}"))
    # Personajes de espaldas (sin referencia facial): pelo y ropa por color, la cara no se ve.
    if sspec.behind:
        others = [b for b in (bx for bx, s in tools.detect(image) if s > co.PERSON_SCORE)
                  if b not in crops_by_char.values()]
        for name in sspec.behind:
            entry = registry["personajes"][name]
            if not others:
                reqs.append(Requirement(name, "presencia", "de espaldas en la imagen", FAIL, "no hay segunda persona"))
                continue
            box = max(others, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            outfit = outfit_at(registry, name, scene.number)
            hair_ref = (outfit or {}).get("medida", {}).get("pelo_rgb") or \
                (entry["permanentes"].get("color de pelo", {}).get("medida") or {}).get("rgb")
            st, ev = color_status(region_color(image, box, (0.0, 0.25), True), hair_ref)
            reqs.append(Requirement(name, "color de pelo", "el de su referencia", st, f"de espaldas, región: {ev}"))
            if outfit:
                st, ev = color_status(region_color(image, box, (0.60, 0.95)), (outfit.get("medida") or {}).get("rgb"))
                reqs.append(Requirement(name, "ropa", outfit["texto"], st, f"de espaldas, región: {ev}"))
            reqs.append(Requirement(name, "ojos", "no visibles", NA, "de espaldas según la estrategia", False))
    # Escena completa.
    check = people_check(scene, image_path)
    reqs.append(Requirement("(escena)", "personas", str(check.expected),
                            PASS if check.status == "OK" else FAIL if check.status == "DUPLICADO" else UNCERTAIN,
                            f"{check.faces} caras, {check.heads} cabezas: {check.status}"))
    tags = tools.tag(image)
    for t in sspec.composition:
        s = tags.get(t, 0.0)
        reqs.append(Requirement("(escena)", "composición", t, PASS if s >= co.TAG_LOW else UNCERTAIN, f"{t} {s:.2f}"))
    for t in sspec.forbidden:
        s = tags.get(t, 0.0)
        reqs.append(Requirement("(escena)", "composición", f"sin {t}",
                                FAIL if s >= co.TAG_HIGH else UNCERTAIN if s >= co.TAG_LOW else PASS, f"{t} {s:.2f}"))
    if registry.get("estilo"):
        got = style_stats(image)
        off = [abs(g - r) for g, r in zip(got, registry["estilo"])]
        ok = all(o <= tol for o, tol in zip(off, STYLE_TOLERANCE))
        reqs.append(Requirement("(escena)", "estilo", "brillo/saturación/contraste de las escenas de referencia",
                                PASS if ok else UNCERTAIN,
                                f"{[round(g) for g in got]} frente a {registry['estilo']}"))
    return reqs


def _crops(scene: Scene, image, portraits: Path, tools: co.Tools) -> dict[str, tuple]:
    from PIL import Image

    boxes = [b for b, s in tools.detect(image) if s > co.PERSON_SCORE]
    faces = {c: Image.open(portraits / f"{c}.png").convert("RGB")
             for c in scene.characters if (portraits / f"{c}.png").exists()}
    if not boxes or not faces:
        return {}
    if len(faces) == 1:
        c = next(iter(faces))
        return {c: min(boxes, key=lambda b: tools.difference(faces[c], image.crop(b)))}
    pairs = sorted((tools.difference(faces[c], image.crop(b)), c, i) for c in faces for i, b in enumerate(boxes))
    out, used = {}, set()
    for _, c, i in pairs:
        if c not in out and i not in used:
            out[c] = boxes[i]
            used.add(i)
    return out


def _face_in(person_box, faces: list) -> tuple | None:
    x0, y0, x1, y1 = person_box
    inside = [f for f in faces if f[0] >= x0 - 5 and f[2] <= x1 + 5 and f[1] >= y0 - 5 and f[3] <= y1 + 5]
    return max(inside, key=lambda f: f[2] - f[0]) if inside else None


def verdict(reqs: list[Requirement]) -> str:
    """VALID solo si todos los obligatorios son PASS (o N/A justificado por el guion)."""
    mandatory = [r for r in reqs if r.mandatory]
    if any(r.status == FAIL for r in mandatory):
        return "REJECTED"
    if any(r.status == UNCERTAIN for r in mandatory):
        return "UNCERTAIN"
    return "VALID"


# --- Prompts, correcciones y estrategias -------------------------------------------------------------

STRATEGIES = ["referencias por región", "secundarios de espaldas"]


@dataclass
class Plan:
    strategy: int = 0
    likeness: float | None = None  # {parecido} de la escena
    emphasis: dict[str, list[str]] = field(default_factory=dict)  # personaje -> refuerzos de su atributo
    avoid: list[str] = field(default_factory=list)  # negativo de la escena
    composition: list[str] = field(default_factory=list)  # refuerzos de composición
    notes: list[str] = field(default_factory=list)  # registro de correcciones

    def copy(self) -> "Plan":
        return Plan(self.strategy, self.likeness, {k: list(v) for k, v in self.emphasis.items()},
                    list(self.avoid), list(self.composition), list(self.notes))


def scene_line(sspec: SceneSpec, registry: dict, plan: Plan, reroll: int, board: Storyboard) -> str:
    """La línea de escena de una candidata, en la sintaxis del guion."""
    cast = list(sspec.cast)
    behind = list(sspec.behind)
    if STRATEGIES[plan.strategy] == "secundarios de espaldas" and len(cast) > 1:
        behind += cast[1:]
        cast = cast[:1]
    gender = {c: ("boy" if "1boy" in board.characters[c] else "girl") for c in sspec.cast}
    parts = [_count_tags(sspec.cast, board)]
    for c in cast:
        outfit = outfit_at(registry, c, sspec.number)
        bits = [outfit["texto"]] if outfit else []
        bits += [registry["personajes"][c].get("extra_prompt", "")] + plan.emphasis.get(c, [])
        parts.append(f"@{c}[{', '.join(b for b in bits if b)}]")
    if len(cast) > 1:
        sides = ["on the left", "on the right"] if len(cast) == 2 else [f"position {i + 1}" for i in range(len(cast))]
        parts.append(", ".join(f"the {gender[c]} {side}" for c, side in zip(cast, sides)))
    for c in behind:
        outfit = outfit_at(registry, c, sspec.number)
        desc = registry["personajes"][c].get("detras_prompt") or ", ".join(
            x for x in (registry["personajes"][c].get("extra_prompt", ""), (outfit or {}).get("texto", "")) if x)
        parts.append(f"a {('young man' if gender[c] == 'boy' else 'young woman')} seen from behind, back view, {desc}")
    parts += [sspec.action] + plan.composition
    line = ", ".join(p for p in parts if p)
    tail = [f"{{semilla={reroll}}}"]
    if plan.avoid:
        tail.append("{evitar=" + ", ".join(dict.fromkeys(plan.avoid)) + "}")
    if plan.likeness is not None:
        tail.append(f"{{parecido={plan.likeness:.2f}}}")
    return f"[{sspec.number:03d}] {line} " + " ".join(tail)


def _count_tags(cast: list[str], board: Storyboard) -> str:
    boys = sum(1 for c in cast if "1boy" in board.characters[c])
    girls = sum(1 for c in cast if "1girl" in board.characters[c])
    tags = [f"{boys}boy{'s' if boys > 1 else ''}"] * bool(boys) + [f"{girls}girl{'s' if girls > 1 else ''}"] * bool(girls)
    return ", ".join(tags) if len(cast) > 1 else "solo"


def expected_of_others(registry: dict, cast: list[str], name: str) -> set[str]:
    """Palabras que otro personaje presente sí necesita: no se pueden poner en el negativo."""
    words: set[str] = set()
    for other in cast:
        if other == name:
            continue
        entry = registry["personajes"][other]
        for attr in entry["permanentes"].values():
            exp = attr["esperado"]
            words |= set(exp) if isinstance(exp, list) else {str(exp)}
        for item in entry["ropa"]:
            words |= set(re.findall(r"[a-z]+", item["texto"].lower()))
        words |= set(re.findall(r"[a-z]+", entry.get("extra_prompt", "").lower()))
    return words


def correct(plan: Plan, failed: list[Requirement], registry: dict, sspec: SceneSpec) -> Plan:
    """Cambia solo lo relacionado con los fallos. Nunca pone en el negativo algo que otro
    personaje presente necesita (p. ej. «brown eyes» con Daniel en la escena)."""
    new = plan.copy()
    present = sspec.cast + sspec.behind
    for r in failed:
        name = r.character
        if r.attribute == "ojos" and name in registry["personajes"]:
            exp = registry["personajes"][name]["permanentes"]["ojos"]["esperado"]
            _add(new.emphasis.setdefault(name, []), f"{'/'.join(exp)} eyes, {'/'.join(exp)} irises")
            for wrong in ("brown", "black", "red", "blue", "green", "amber"):
                if wrong not in exp and wrong not in expected_of_others(registry, present, name):
                    _add(new.avoid, f"{wrong} eyes")
            new.notes.append(f"{name}: ojos -> refuerzo {exp} y negativo sin contradecir a otros")
        elif r.attribute in ("color de pelo", "largo de pelo") and name in registry["personajes"]:
            extra = registry["personajes"][name].get("extra_prompt") or ""
            hair = [p.strip() for p in extra.split(",") if "hair" in p] or \
                   [registry["personajes"][name]["ficha"]]
            _add(new.emphasis.setdefault(name, []), hair[0])
            new.notes.append(f"{name}: pelo -> refuerzo «{hair[0]}»")
        elif r.attribute in ("ropa", "prenda", "color de ropa") and name in registry["personajes"]:
            outfit = outfit_at(registry, name, sspec.number)
            if outfit:
                _add(new.emphasis.setdefault(name, []), f"wearing {outfit['texto']}")
            new.notes.append(f"{name}: ropa -> refuerzo «{(outfit or {}).get('texto')}»")
        elif r.attribute in ("identidad", "clon"):
            base = new.likeness if new.likeness is not None else co_default_likeness()
            new.likeness = min(LIKENESS_MAX, base + LIKENESS_STEP)
            for t in ("clone", "twins", "duplicate", "extra person"):
                _add(new.avoid, t)
            new.notes.append(f"{name}: {r.attribute} -> parecido {new.likeness:.2f}, negativo anti-clon")
        elif r.attribute == "personas":
            for t in ("extra person", "multiple girls", "multiple boys", "crowd"):
                if t.split()[-1].rstrip("s") not in {"girl", "boy"} or not _needs_many(registry, present, t):
                    _add(new.avoid, t)
            new.notes.append("escena: personas -> negativo de personas extra")
        elif r.attribute == "composición":
            _add(new.composition, r.expected.replace("_", " "))
            new.notes.append(f"escena: composición -> refuerzo «{r.expected}»")
    return new


def co_default_likeness() -> float:
    from .images import IP_SCALE

    return IP_SCALE


def _needs_many(registry, present, tag: str) -> bool:
    boys = sum(1 for c in present if "1boy" in registry["personajes"][c]["ficha"])
    girls = sum(1 for c in present if "1girl" in registry["personajes"][c]["ficha"])
    return ("girls" in tag and girls > 1) or ("boys" in tag and boys > 1)


def _add(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def failure_key(reqs: list[Requirement]) -> frozenset:
    return frozenset((r.character, r.attribute) for r in reqs if r.mandatory and r.status in (FAIL, UNCERTAIN))


# --- Bucle -----------------------------------------------------------------------------------------

@dataclass
class Candidate:
    scene: int
    batch: int
    strategy: str
    reroll: int
    line: str
    prompt: str
    negative: str
    seed: int
    likeness: float
    model: str
    image: str
    sha256: str
    verdict: str
    requirements: list[Requirement]


@dataclass
class SceneResult:
    scene: int
    state: str  # VALID_CANDIDATE, NO_VALID_CANDIDATE, GPU_ERROR
    candidate: str | None
    batches: int
    unmet: dict[str, int]  # requisito -> nº de candidatas en que falló o quedó incierto
    corrections: list[str]


def run_scene(story_header: str, board: Storyboard, sspec: SceneSpec, registry: dict, workdir: Path,
              portraits: Path, *, batch_size: int = 4, max_batches: int = 10, seed: int = 1234,
              model: str, generate: Callable, evaluate_fn: Callable, log: Callable = print,
              repeat_to_switch: int = 2) -> tuple[SceneResult, list[Candidate]]:
    """Lotes de candidatas hasta una válida o hasta el límite. generate(jobs) genera las imágenes;
    evaluate_fn(board1, scene, sspec, path) devuelve los requisitos."""
    from . import images as img

    plan = Plan()
    candidates: list[Candidate] = []
    unmet: dict[str, int] = {}
    last_keys: list[frozenset] = []
    folder = workdir / f"{sspec.number:03d}"
    for batch in range(max_batches):
        lines = [scene_line(sspec, registry, plan, batch * batch_size + i + 1, board) for i in range(batch_size)]
        boards = [parse(story_header + "\n\n" + line + "\nx\n") for line in lines]
        jobs = [img.scene_jobs(b, folder, portraits, seed, model)[0] for b in boards]
        try:
            generate(jobs)
        except Exception as e:  # falta de memoria de la GPU u otro error del generador
            oom = "out of memory" in str(e).lower() or type(e).__name__ == "OutOfMemoryError"
            log(f"[{sspec.number:03d}] lote {batch + 1}: error de generación ({'memoria GPU' if oom else e})")
            return SceneResult(sspec.number, "GPU_ERROR" if oom else "GENERATION_ERROR", None, batch,
                               unmet, plan.notes), candidates
        batch_cands = []
        for b, job, line in zip(boards, jobs, lines):
            scene = b.scenes[0]
            reqs = evaluate_fn(b, scene, sspec, job.out)
            v = verdict(reqs)
            cand = Candidate(sspec.number, batch + 1, STRATEGIES[plan.strategy], scene.reroll, line, job.prompt,
                             job.negative or b.negative, job.seed, job.ip_scale, model, str(job.out),
                             co.file_hash(job.out), v, reqs)
            batch_cands.append(cand)
            for r in reqs:
                if r.mandatory and r.status in (FAIL, UNCERTAIN):
                    key = f"{r.character} {r.attribute}"
                    unmet[key] = unmet.get(key, 0) + 1
            log(f"[{sspec.number:03d}] lote {batch + 1} semilla {scene.reroll}: {v} "
                f"({', '.join(f'{r.character} {r.attribute} {r.status}' for r in reqs if r.status in (FAIL, UNCERTAIN))})")
        candidates += batch_cands
        valid = [c for c in batch_cands if c.verdict == "VALID"]
        if valid:
            return SceneResult(sspec.number, "VALID_CANDIDATE", valid[0].image, batch + 1, unmet,
                               plan.notes), candidates
        # La candidata con menos fallos guía la corrección dirigida.
        best = min(batch_cands, key=lambda c: (sum(r.status == FAIL for r in c.requirements),
                                               sum(r.status == UNCERTAIN for r in c.requirements)))
        failed = [r for r in best.requirements if r.mandatory and r.status in (FAIL, UNCERTAIN)]
        key = failure_key(best.requirements)
        last_keys.append(key)
        same = len(last_keys) >= repeat_to_switch and len(set(last_keys[-repeat_to_switch:])) == 1
        if same and plan.strategy + 1 < len(STRATEGIES) and len(sspec.cast) > 1:
            plan = Plan(strategy=plan.strategy + 1, notes=plan.notes + [
                f"lote {batch + 1}: el mismo fallo {sorted(key)} se repite -> estrategia «{STRATEGIES[plan.strategy + 1]}»"])
            last_keys.clear()
        else:
            plan = correct(plan, failed, registry, sspec)
    return SceneResult(sspec.number, "NO_VALID_CANDIDATE", None, max_batches, unmet, plan.notes), candidates


def write_results(results: list[SceneResult], candidates: list[Candidate], path: Path) -> None:
    data = {"escenas": [asdict(r) for r in results],
            "candidatas": [{**{k: v for k, v in asdict(c).items() if k != "requirements"},
                            "requisitos": [asdict(r) for r in c.requirements]} for c in candidates]}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot(paths: list[Path]) -> dict[str, str]:
    return {str(p): co.file_hash(p) for p in paths if Path(p).exists()}


def protected_changed(before: dict[str, str]) -> list[str]:
    """Archivos protegidos (imágenes definitivas) que han cambiado o desaparecido."""
    return [p for p, h in before.items() if not Path(p).exists() or co.file_hash(Path(p)) != h]
