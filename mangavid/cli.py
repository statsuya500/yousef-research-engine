"""Línea de comandos: python -m mangavid run historia.txt"""

from __future__ import annotations

import argparse
from pathlib import Path

from dubber import tts
from dubber.segments import Segment

from . import images, render, storyboard


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="mangavid", description="Historia en texto → vídeo estilo manhwa narrado")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="Generar imágenes, voz y vídeo")
    r.add_argument("story", type=Path, help="Guion de escenas (.txt)")
    r.add_argument("-o", "--output", type=Path, help="Vídeo de salida (por defecto <guion>.mp4)")
    r.add_argument("--workdir", type=Path, help="Carpeta de trabajo (por defecto <guion>_work)")
    r.add_argument("--voice", default=tts.DEFAULT_VOICE, help="Voz Edge-TTS, p. ej. es-MX-JorgeNeural")
    r.add_argument("--rate", default="+0%", help="Velocidad de la voz, p. ej. +10%%")
    r.add_argument("--seed", type=int, default=1234, help="Cambia todas las imágenes manteniendo el guion")
    r.add_argument("--model", default=images.DEFAULT_MODEL)
    r.add_argument("--music", type=Path, help="Música de fondo (se repite en bucle)")
    r.add_argument("--music-volume", type=float, default=0.12)
    r.add_argument("--font-size", type=int, default=16)
    r.add_argument("--only-images", action="store_true", help="Generar solo las imágenes para revisarlas")
    args = p.parse_args(argv)

    board = storyboard.load(args.story)
    work = args.workdir or args.story.with_name(f"{args.story.stem}_work")
    output = args.output or args.story.with_suffix(".mp4")
    print(f"[guion] {len(board.scenes)} escenas, {len(board.characters)} personajes")

    pics = images.generate(board, work / "images", seed=args.seed, model=args.model)
    if args.only_images:
        print(f"[imágenes] en {work / 'images'}")
        return
    voices = tts.synthesize(
        [Segment(0.0, 0.0, "", s.narration) for s in board.scenes], work / "voice", args.voice, args.rate
    )
    if any(v is None for v in voices):
        missing = [s.number for s, v in zip(board.scenes, voices) if v is None]
        raise SystemExit(f"Escenas sin narración: {missing}")
    render.render(board, pics, voices, work / "segments", output, args.music, args.music_volume, args.font_size)


if __name__ == "__main__":
    main()
