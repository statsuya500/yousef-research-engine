"""Validador de identidad y posición de los personajes de una escena, después de generarla.

Quién es quién se decide por la ROPA (la prenda que la ficha y el guion le ponen), no por la cara:
cuando las máscaras faciales caen en el lado equivocado, la cara de un personaje acaba en el otro y
la cara deja de servir para identificarlo (prueba de la escena 004, seed 301247). La cara se usa
después, para comprobar que corresponde a la ropa: si se parece más a la del otro personaje, las
identidades están cruzadas.

Comprobaciones (PASS, FAIL o UNCERTAIN, cada una con su evidencia):
- personas y rostros: exactamente uno por personaje; un rostro de más es un fantasma (FAIL);
- identificación por ropa: margen mínimo entre la prenda propia y la del otro, asignación uno a uno;
- rostro frente a ropa: cruce (FAIL), coincide (PASS) o dudoso (UNCERTAIN);
- posición: el lado que exige el guion; en la franja central, UNCERTAIN;
- ojos: medida del iris, cuando el personaje la tiene en su registro.
Los artefactos (manchas, halos, figuras translúcidas) no tienen detector fiable: se añade siempre
un requisito de revisión visual, así que nada sale VALID de forma automática.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import coherencia as co
from .continuidad import FAIL, NOT_AUTO, PASS, UNCERTAIN, Requirement, iris_color, iris_status

GARMENT_MARGIN = 0.15  # la prenda propia tiene que superar a la del otro personaje por esto
FACE_MARGIN = 0.05  # diferencia CCIP mínima entre la referencia propia y la del otro
FACE_PASS = co.FACE_POSSIBLE  # 0.18: parecido suficiente con su propia referencia
SIDE_DEADZONE = 0.05  # centro a menos del 5 % del ancho del medio: lado indeterminado
PERSON_SCORE = co.PERSON_SCORE


@dataclass
class CharacterSpec:
    name: str
    garments: list[str]  # etiquetas WD14 de su prenda vigente («sweater», «hoodie»…)
    face_ref: Path
    iris_refs: list[dict] | None = None  # medidas del iris de referencia (registro de continuidad)
    side: str | None = None  # «izquierda» / «derecha» si el guion lo exige


@dataclass
class Tools:
    persons: Callable  # imagen -> [(caja, confianza)]
    faces: Callable  # imagen -> [(caja, confianza)]
    tag: Callable  # imagen -> {etiqueta: confianza}
    difference: Callable  # (imagen, imagen) -> diferencia CCIP


def default_tools() -> Tools:
    from imgutils.detect import detect_faces, detect_person
    from imgutils.metrics import ccip_difference
    from imgutils.tagging import get_wd14_tags

    return Tools(lambda im: [(b, s) for b, _, s in detect_person(im)],
                 lambda im: [(b, s) for b, _, s in detect_faces(im)],
                 lambda im: get_wd14_tags(im, general_threshold=0.15)[1],
                 lambda a, b: float(ccip_difference(a, b)))


@dataclass
class Person:
    box: tuple
    cx: int
    face: tuple | None
    garment_scores: dict[str, float] = field(default_factory=dict)  # personaje -> puntuación de su prenda
    character: str | None = None


@dataclass
class Report:
    requirements: list[Requirement]
    people: list[dict]
    crossed: bool  # rostro de un personaje sobre la ropa del otro
    retry_eligible: bool  # cruce con todas las condiciones de confianza: admite un reintento invertido


def garment_score(tags: dict, garments: list[str]) -> float:
    return max((tags.get(g, 0.0) for g in garments), default=0.0)


def _inside(face, box, tol=6) -> bool:
    return face[0] >= box[0] - tol and face[2] <= box[2] + tol and face[1] >= box[1] - tol and face[3] <= box[3] + tol


def assign_by_garment(people: list[Person], chars: list[CharacterSpec]) -> dict[str, tuple[Person | None, str]]:
    """Cada personaje a la persona cuya prenda propia supera a la de los demás por GARMENT_MARGIN.
    Devuelve personaje -> (persona o None, evidencia). Exige asignación uno a uno."""
    out: dict[str, tuple[Person | None, str]] = {}
    for c in chars:
        best, ev = None, []
        for p in people:
            own = p.garment_scores[c.name]
            others = max((p.garment_scores[o.name] for o in chars if o.name != c.name), default=0.0)
            ev.append(f"x={p.cx}: {c.name} {own:.2f} / otro {others:.2f}")
            if own >= co.TAG_LOW and own - others >= GARMENT_MARGIN:
                best = p if best is None else "varias"
        if best == "varias":
            out[c.name] = (None, "su prenda aparece en varias personas; " + "; ".join(ev))
        else:
            out[c.name] = (best, "; ".join(ev))
    used = [p for p, _ in out.values() if isinstance(p, Person)]
    if len(used) != len({id(p) for p in used}):
        out = {k: (None, "dos personajes asignados a la misma persona; " + e) for k, (_, e) in out.items()}
    return out


def validate(image_path: Path, chars: list[CharacterSpec], tools: Tools) -> Report:
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    width = image.width
    reqs: list[Requirement] = []
    boxes = [b for b, s in tools.persons(image) if s > PERSON_SCORE]
    faces = [b for b, s in tools.faces(image) if s > 0.4]
    n = len(chars)
    people = []
    for b in sorted(boxes, key=lambda b: b[0]):
        inside = [f for f in faces if _inside(f, b)]
        face = max(inside, key=lambda f: f[2] - f[0]) if inside else None
        tags = tools.tag(image.crop(b))
        people.append(Person(b, (b[0] + b[2]) // 2, face, {c.name: garment_score(tags, c.garments) for c in chars}))
    # Integridad.
    status = PASS if len(people) == n else FAIL if len(people) > n else UNCERTAIN
    reqs.append(Requirement("(escena)", "número de personas", str(n), status,
                            f"{len(people)} personas detectadas" + (" (pueden estar fundidas)" if status == UNCERTAIN else "")))
    status = PASS if len(faces) == n else FAIL if len(faces) > n else UNCERTAIN
    reqs.append(Requirement("(escena)", "número de rostros", str(n), status,
                            f"{len(faces)} rostros" + (": rostro fantasma" if len(faces) > n else "")))
    orphans = [f for f in faces if not any(_inside(f, p.box) for p in people)]
    if orphans:
        reqs.append(Requirement("(escena)", "rostros sin persona", "0", FAIL, f"{len(orphans)} rostros fuera de toda persona"))
    # Identificación por ropa.
    assigned = assign_by_garment(people, chars)
    refs = {c.name: Image.open(c.face_ref).convert("RGB") for c in chars}
    crossed, confident = False, True
    for c in chars:
        person, ev = assigned[c.name]
        if person is None:
            confident = False
            reqs.append(Requirement(c.name, "identificación por ropa", "/".join(c.garments), UNCERTAIN, ev))
            for attr in ("rostro frente a ropa", "posición"):
                reqs.append(Requirement(c.name, attr, "-", UNCERTAIN, "sin identificar por la ropa"))
            continue
        person.character = c.name
        reqs.append(Requirement(c.name, "identificación por ropa", "/".join(c.garments), PASS, ev))
        # Rostro frente a ropa.
        if person.face is None:
            confident = False
            reqs.append(Requirement(c.name, "rostro frente a ropa", "su rostro", UNCERTAIN, "sin rostro detectado en su persona"))
        else:
            crop = image.crop(person.face)
            d = {o.name: tools.difference(refs[o.name], crop) for o in chars}
            own = d[c.name]
            other_name, other = min(((k, v) for k, v in d.items() if k != c.name), key=lambda kv: kv[1])
            ev = f"CCIP {c.name} {own:.3f}, {other_name} {other:.3f}"
            if other <= own - FACE_MARGIN:
                crossed = True
                reqs.append(Requirement(c.name, "rostro frente a ropa", "su rostro", FAIL, f"cruzado: rostro de {other_name}; {ev}"))
            elif own <= other - FACE_MARGIN and own <= FACE_PASS:
                reqs.append(Requirement(c.name, "rostro frente a ropa", "su rostro", PASS, ev))
            else:
                confident = False if own > other - FACE_MARGIN else confident
                reqs.append(Requirement(c.name, "rostro frente a ropa", "su rostro", UNCERTAIN, ev))
            # Ojos.
            if c.iris_refs:
                st, ev_eye = iris_status(iris_color(image, person.face), c.iris_refs)
                reqs.append(Requirement(c.name, "ojos (iris)", "los de su registro", st, ev_eye))
        # Posición.
        if c.side:
            off = (person.cx - width / 2) / width
            seen = "izquierda" if off < 0 else "derecha"
            if abs(off) < SIDE_DEADZONE:
                st, ev = UNCERTAIN, f"centro x={person.cx}: en la franja central"
            else:
                st, ev = (PASS if seen == c.side else FAIL), f"centro x={person.cx} ({seen})"
            reqs.append(Requirement(c.name, "posición", c.side, st, ev))
    reqs.append(Requirement("(escena)", "artefactos", "sin manchas, halos ni figuras translúcidas", NOT_AUTO,
                            "sin detector fiable: revisar a ojo"))
    counts_ok = len(people) == n and len(faces) == n and not orphans
    retry = crossed and confident and counts_ok and all(p is not None for p, _ in assigned.values())
    info = [{"x": p.cx, "caja": list(p.box), "rostro": list(p.face) if p.face else None, "personaje": p.character,
             "prendas": {k: round(v, 3) for k, v in p.garment_scores.items()}} for p in people]
    return Report(reqs, info, crossed, retry)
