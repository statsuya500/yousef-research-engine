"""Línea de comandos: python -m dubber run|preview ..."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import media
from .masks import DEFAULT_SUB_STYLE, parse_mask
from .pipeline import Config, export_script_for, preview_frame, run
from .translate import DEFAULT_MODEL
from .tts import DEFAULT_VOICE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dubber", description="Transcripción, traducción y doblaje de vídeos y audios.")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="Transcribir, traducir y doblar un vídeo o audio")
    r.add_argument("input", type=Path)
    r.add_argument("-o", "--output", type=Path, help="Salida (por defecto <nombre>_es.mp4 para vídeos, <nombre>_es.mp3 para audios)")
    r.add_argument("--workdir", type=Path, help="Carpeta de trabajo (por defecto <nombre>_work)")
    r.add_argument("--src-lang", default="zh")
    r.add_argument("--tgt-lang", default="es")
    r.add_argument("--whisper-model", default="large-v3",
                   help="tiny, base, small, medium, large-v3 (más grande = mejor y más lento)")
    r.add_argument("--translator-model", default=DEFAULT_MODEL)
    r.add_argument("--voice", default=DEFAULT_VOICE,
                   help="Voz Edge-TTS: es-ES-AlvaroNeural, es-ES-ElviraNeural, es-MX-JorgeNeural…")
    r.add_argument("--rate", default="+0%", help="Velocidad base de la voz, p. ej. +10%%")
    r.add_argument("--max-speed", type=float, default=1.5,
                   help="Aceleración máxima para que una frase quepa en su hueco")
    r.add_argument("--background", choices=["duck", "separate", "none"], default="duck",
                   help="duck: audio original bajito; separate: quita la voz con Demucs; none: solo doblaje")
    r.add_argument("--bg-volume", type=float, default=0.2, help="Volumen del original en modo duck")
    r.add_argument("--mask", action="append", default=[], metavar="MODO:X,Y,ANCHO,ALTO",
                   help="Zona a tapar (blur, delogo o box). Repetible.")
    r.add_argument("--no-subs", action="store_true", help="No generar subtítulos")
    r.add_argument("--no-burn", action="store_true", help="Generar .srt aparte sin quemarlo en el vídeo")
    r.add_argument("--font-size", type=int, default=16)
    r.add_argument("--segments", type=Path, help="JSON de segmentos ya revisado (salta Whisper y traducción)")
    r.add_argument("--translation", type=Path, metavar="GUION_ES.txt",
                   help="Guion traducido por ti (paso 2); se usa en vez de la traducción automática")
    r.add_argument("--text-only", "--stop-after-translate", dest="stop_after_translate",
                   action="store_true",
                   help="Solo transcribir y traducir (genera .txt y .srt, sin doblar)")

    g = sub.add_parser("guion", help="Paso 1: transcribe y saca el guion numerado sin tiempos para traducirlo")
    g.add_argument("input", type=Path)
    g.add_argument("--workdir", type=Path, help="Carpeta de trabajo (por defecto <nombre>_work)")
    g.add_argument("--src-lang", default="zh")
    g.add_argument("--whisper-model", default="large-v3")

    v = sub.add_parser("preview", help="Fotograma con las zonas tapadas para ajustar coordenadas")
    v.add_argument("input", type=Path)
    v.add_argument("-o", "--output", type=Path, default=Path("preview.png"))
    v.add_argument("--at", type=float, default=1.0, help="Segundo del vídeo")
    v.add_argument("--mask", action="append", default=[])
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    stem = args.input.with_suffix("")
    if args.command == "guion":
        export_script_for(Config(
            input=args.input, output=Path(f"{stem}_es.mp4"),
            workdir=args.workdir or Path(f"{stem}_work"),
            src_lang=args.src_lang, whisper_model=args.whisper_model,
        ))
        return

    masks = [parse_mask(m) for m in args.mask]
    if args.command == "preview":
        out = preview_frame(args.input, masks, args.output, args.at)
        print(f"[preview] {out}")
        return

    ext = ".mp4" if media.has_video(args.input) else ".mp3"
    style = DEFAULT_SUB_STYLE.replace("FontSize=16", f"FontSize={args.font_size}")
    cfg = Config(
        input=args.input,
        output=args.output or Path(f"{stem}_{args.tgt_lang}{ext}"),
        workdir=args.workdir or Path(f"{stem}_work"),
        src_lang=args.src_lang,
        tgt_lang=args.tgt_lang,
        whisper_model=args.whisper_model,
        translator_model=args.translator_model,
        voice=args.voice,
        rate=args.rate,
        max_speed=args.max_speed,
        background=args.background,
        bg_volume=args.bg_volume,
        masks=masks,
        subtitles=not args.no_subs,
        burn_subtitles=not args.no_burn,
        sub_style=style,
        segments_file=args.segments,
        translation_file=args.translation,
        stop_after_translate=args.stop_after_translate,
    )
    run(cfg)

