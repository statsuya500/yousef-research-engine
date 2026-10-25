"""Lee el guion de escenas: personajes, estilo y, por cada escena, imagen y narración."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_SCENE = re.compile(r"^\[(\d{1,5})\]\s*(.*)$")
_DIRECTIVE = re.compile(r"^@([\w-]+)\s*:\s*(.*)$")
_MENTION = re.compile(r"@([\w-]+)(?:\[([^\]]*)\])?")
_REROLL = re.compile(r"\{semilla=(\d+)\}")
_AVOID = re.compile(r"\{evitar=([^}]*)\}")
_LIKENESS = re.compile(r"\{parecido=([0-9.]+)\}")


@dataclass
class Scene:
    number: int
    image: str  # descripción de la imagen con los @personajes ya sustituidos
    narration: str
    characters: list[str] = field(default_factory=list)  # @personajes en orden de aparición
    reroll: int = 0  # {semilla=N} en la escena: otra versión de la imagen con la misma descripción
    avoid: str = ""  # {evitar=...} en la escena: se añade al negativo solo en esta escena
    action: str = ""  # la descripción sin los @personajes: acción, expresión, encuadre y lugar
    likeness: float | None = None  # {parecido=0.6}: peso de la cara del retrato solo en esta escena
    # @sara[simple dress]: ropa de ese personaje. Sigue en las escenas siguientes hasta que otra la cambie.
    outfits: dict[str, str] = field(default_factory=dict)


@dataclass
class Storyboard:
    style: str = ""
    negative: str = ""
    negative_solo: str = ""  # se añade al negativo en escenas «solo» (evita personajes clonados)
    likeness: float | None = None  # @parecido: cuánto se impone la cara del retrato (0-1)
    shots: int = 1  # @planos: imágenes por escena, que se reparten el tiempo de la narración
    refine: bool = False  # @retoque: si -> las caras se redibujan a más resolución (ojos nítidos)
    characters: dict[str, str] = field(default_factory=dict)  # etiquetas ya expandidas
    # Personaje derivado -> personaje base (p. ej. «@alex5: @alex, stubble» -> alex5: alex).
    # El retrato del derivado se genera con la cara del retrato elegido del base.
    bases: dict[str, str] = field(default_factory=dict)
    scenes: list[Scene] = field(default_factory=list)
    thumbnail: Scene | None = None  # @miniatura: imagen de la miniatura, con @personajes como una escena
    thumbnail_text: str = ""  # @miniatura_texto: texto grande de la miniatura (*palabra* resaltada)
    thumbnail_style: str = ""  # @miniatura_estilo: sustituye a @estilo solo en la miniatura

    def prompt(self, scene: Scene) -> str:
        """Acción y expresión primero, después los rasgos de los personajes y al final el estilo.

        Los modelos de imagen dan más peso a lo que va al principio, y la ficha de un personaje
        puede ocupar 40 tokens: si fuera delante, la acción quedaría relegada al final.
        """
        cast = [", ".join(p for p in (self.characters[c], scene.outfits.get(c, "")) if p)
                for c in scene.characters]
        return ", ".join(p for p in (scene.action or scene.image, *cast, self.style) if p)

    def negative_for(self, scene: Scene) -> str:
        solo = self.negative_solo if re.search(r"\bsolo\b", scene.image) else ""
        return ", ".join(p for p in (self.negative, solo, scene.avoid) if p)


def parse(text: str) -> Storyboard:
    board = Storyboard()
    raw_scenes: list[tuple[int, str, list[str]]] = []
    raw_thumbnail = ""

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("#"):
            continue
        if m := _SCENE.match(line):
            raw_scenes.append((int(m.group(1)), m.group(2).strip(), []))
        elif not raw_scenes and (m := _DIRECTIVE.match(line)):
            name, value = m.group(1).lower(), m.group(2).strip()
            if name == "estilo":
                board.style = value
            elif name == "negativo":
                board.negative = value
            elif name == "negativo_solo":
                board.negative_solo = value
            elif name == "parecido":
                board.likeness = float(value)
            elif name == "planos":
                board.shots = max(1, int(value))
            elif name == "retoque":
                board.refine = value.lower() in ("si", "sí", "1", "true")
            elif name == "miniatura":
                raw_thumbnail = value
            elif name == "miniatura_texto":
                board.thumbnail_text = value
            elif name == "miniatura_estilo":
                board.thumbnail_style = value
            else:
                board.characters[name] = value
        elif raw_scenes:
            raw_scenes[-1][2].append(line)
        else:
            raise ValueError(f"Línea {lineno}: no sé qué hacer con «{line[:60]}»")

    raw_characters = dict(board.characters)
    for name, tags in raw_characters.items():
        refs = [m.group(1).lower() for m in _MENTION.finditer(tags)]
        if refs:
            board.bases[name] = refs[0]
        board.characters[name] = _expand_character(name, raw_characters, [])

    seen: set[int] = set()
    wearing: dict[str, str] = {}  # la última ropa de cada personaje: sigue puesta hasta que el guion la cambie
    for number, image, lines in raw_scenes:
        if number in seen:
            raise ValueError(f"La escena [{number:03d}] está repetida")
        seen.add(number)
        scene = _build_scene(number, image, " ".join(lines).strip(), board.characters)
        wearing.update(scene.outfits)
        scene.outfits = {c: wearing[c] for c in scene.characters if c in wearing}
        board.scenes.append(scene)
    if raw_thumbnail:
        board.thumbnail = _build_scene(0, raw_thumbnail, "", board.characters)
    if not board.scenes:
        raise ValueError("El guion no tiene ninguna escena [001]")
    return board


def _build_scene(number: int, image: str, narration: str, characters: dict[str, str]) -> Scene:
    reroll = 0
    if m := _REROLL.search(image):
        reroll = int(m.group(1))
        image = _REROLL.sub("", image).strip().rstrip(",").strip()
    avoid = ""
    if m := _AVOID.search(image):
        avoid = m.group(1).strip()
        image = _AVOID.sub("", image).strip().rstrip(",").strip()
    likeness = None
    if m := _LIKENESS.search(image):
        likeness = float(m.group(1))
        image = _LIKENESS.sub("", image).strip().rstrip(",").strip()
    cast = list(dict.fromkeys(m.group(1).lower() for m in _MENTION.finditer(image)))
    outfits = {m.group(1).lower(): m.group(2).strip() for m in _MENTION.finditer(image) if m.group(2)}
    action = re.sub(r"\s*,\s*(,\s*)+", ", ", _MENTION.sub("", image)).strip(" ,")
    return Scene(number, _expand(image, characters, number), narration, cast, reroll, avoid,
                 action, likeness, outfits)


def _expand_character(name: str, raw: dict[str, str], chain: list[str]) -> str:
    if name in chain:
        raise ValueError(f"Personajes que se definen en círculo: {' -> '.join('@' + c for c in chain + [name])}")

    def sub(m: re.Match) -> str:
        ref = m.group(1).lower()
        if ref not in raw:
            raise ValueError(f"@{name} usa @{ref}, que no está definido")
        return _expand_character(ref, raw, chain + [name])

    return _MENTION.sub(sub, raw[name])


def _expand(image: str, characters: dict[str, str], number: int) -> str:
    def sub(m: re.Match) -> str:
        name = m.group(1).lower()
        if name not in characters:
            raise ValueError(f"Escena [{number:03d}]: el personaje @{name} no está definido")
        return ", ".join(p for p in (characters[name], m.group(2)) if p)

    return _MENTION.sub(sub, image)


def load(path: Path) -> Storyboard:
    return parse(Path(path).read_text(encoding="utf-8"))
