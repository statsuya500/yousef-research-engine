"""Lee el guion de escenas: personajes, estilo y, por cada escena, imagen y narración."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_SCENE = re.compile(r"^\[(\d{1,5})\]\s*(.*)$")
_DIRECTIVE = re.compile(r"^@([\w-]+)\s*:\s*(.*)$")
_MENTION = re.compile(r"@([\w-]+)")


@dataclass
class Scene:
    number: int
    image: str  # descripción de la imagen con los @personajes ya sustituidos
    narration: str
    characters: list[str] = field(default_factory=list)  # @personajes en orden de aparición


@dataclass
class Storyboard:
    style: str = ""
    negative: str = ""
    characters: dict[str, str] = field(default_factory=dict)
    scenes: list[Scene] = field(default_factory=list)

    def prompt(self, scene: Scene) -> str:
        return ", ".join(p for p in (scene.image, self.style) if p)


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
            else:
                board.characters[name] = value
        elif raw_scenes:
            raw_scenes[-1][2].append(line)
        else:
            raise ValueError(f"Línea {lineno}: no sé qué hacer con «{line[:60]}»")

    seen: set[int] = set()
    for number, image, lines in raw_scenes:
        if number in seen:
            raise ValueError(f"La escena [{number:03d}] está repetida")
        seen.add(number)
        cast = list(dict.fromkeys(m.lower() for m in _MENTION.findall(image)))
        board.scenes.append(
            Scene(number, _expand(image, board.characters, number), " ".join(lines).strip(), cast)
        )
    if not board.scenes:
        raise ValueError("El guion no tiene ninguna escena [001]")
    return board


def _expand(image: str, characters: dict[str, str], number: int) -> str:
    def sub(m: re.Match) -> str:
        name = m.group(1).lower()
        if name not in characters:
            raise ValueError(f"Escena [{number:03d}]: el personaje @{name} no está definido")
        return characters[name]

    return _MENTION.sub(sub, image)


def load(path: Path) -> Storyboard:
    return parse(Path(path).read_text(encoding="utf-8"))
