"""Lee el guion de escenas: personajes, estilo y, por cada escena, imagen y narración."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_SCENE = re.compile(r"^\[(\d{1,5})\]\s*(.*)$")
_DIRECTIVE = re.compile(r"^@([\w-]+)\s*:\s*(.*)$")
_MENTION = re.compile(r"@([\w-]+)")
_REROLL = re.compile(r"\{semilla=(\d+)\}")
_AVOID = re.compile(r"\{evitar=([^}]*)\}")


@dataclass
class Scene:
    number: int
    image: str  # descripción de la imagen con los @personajes ya sustituidos
    narration: str
    characters: list[str] = field(default_factory=list)  # @personajes en orden de aparición
    reroll: int = 0  # {semilla=N} en la escena: otra versión de la imagen con la misma descripción
    avoid: str = ""  # {evitar=...} en la escena: se añade al negativo solo en esta escena
    action: str = ""  # la descripción sin los @personajes: acción, expresión, encuadre y lugar


@dataclass
class Storyboard:
    style: str = ""
    negative: str = ""
    negative_solo: str = ""  # se añade al negativo en escenas «solo» (evita personajes clonados)
    likeness: float | None = None  # @parecido: cuánto se impone la cara del retrato (0-1)
    characters: dict[str, str] = field(default_factory=dict)  # etiquetas ya expandidas
    # Personaje derivado -> personaje base (p. ej. «@alex5: @alex, stubble» -> alex5: alex).
    # El retrato del derivado se genera con la cara del retrato elegido del base.
    bases: dict[str, str] = field(default_factory=dict)
    scenes: list[Scene] = field(default_factory=list)

    def prompt(self, scene: Scene) -> str:
        """Acción y expresión primero, después los rasgos de los personajes y al final el estilo.

        Los modelos de imagen dan más peso a lo que va al principio, y la ficha de un personaje
        puede ocupar 40 tokens: si fuera delante, la acción quedaría relegada al final.
        """
        cast = [self.characters[c] for c in scene.characters]
        return ", ".join(p for p in (scene.action or scene.image, *cast, self.style) if p)

    def negative_for(self, scene: Scene) -> str:
        solo = self.negative_solo if re.search(r"\bsolo\b", scene.image) else ""
        return ", ".join(p for p in (self.negative, solo, scene.avoid) if p)


def parse(text: str) -> Storyboard:
    board = Storyboard()
    raw_scenes: list[tuple[int, str, list[str]]] = []

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
            else:
                board.characters[name] = value
        elif raw_scenes:
            raw_scenes[-1][2].append(line)
        else:
            raise ValueError(f"Línea {lineno}: no sé qué hacer con «{line[:60]}»")

    raw_characters = dict(board.characters)
    for name, tags in raw_characters.items():
        refs = [r.lower() for r in _MENTION.findall(tags)]
        if refs:
            board.bases[name] = refs[0]
        board.characters[name] = _expand_character(name, raw_characters, [])

    seen: set[int] = set()
    for number, image, lines in raw_scenes:
        if number in seen:
            raise ValueError(f"La escena [{number:03d}] está repetida")
        seen.add(number)
        reroll = 0
        if m := _REROLL.search(image):
            reroll = int(m.group(1))
            image = _REROLL.sub("", image).strip().rstrip(",").strip()
        avoid = ""
        if m := _AVOID.search(image):
            avoid = m.group(1).strip()
            image = _AVOID.sub("", image).strip().rstrip(",").strip()
        cast = list(dict.fromkeys(m.lower() for m in _MENTION.findall(image)))
        action = re.sub(r"\s*,\s*(,\s*)+", ", ", _MENTION.sub("", image)).strip(" ,")
        board.scenes.append(Scene(number, _expand(image, board.characters, number),
                                  " ".join(lines).strip(), cast, reroll, avoid, action))
    if not board.scenes:
        raise ValueError("El guion no tiene ninguna escena [001]")
    return board


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
        return characters[name]

    return _MENTION.sub(sub, image)


def load(path: Path) -> Storyboard:
    return parse(Path(path).read_text(encoding="utf-8"))
