"""Línea de comandos.

    python -m mangavid personajes historia.txt        # 1) opciones de retrato por personaje
    python -m mangavid elegir historia.txt elena 3    # 2) fijar la opción que te guste
    python -m mangavid run historia.txt               # 3) escenas, voz y vídeo
    python -m mangavid miniatura historia.txt         # 4) opciones de miniatura para YouTube
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

from dubber import tts
from dubber.segments import Segment

from . import images, render, storyboard


def _portraits_dir(story: Path) -> Path:
    return story.with_name(f"{story.stem}_personajes")


def cmd_personajes(args) -> None:
    board = storyboard.load(args.story)
    folder = _portraits_dir(args.story)
    folder.mkdir(parents=True, exist_ok=True)
    state_file = folder / "opciones.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}

    redo = {n.lower() for n in args.rehacer}
    unknown = redo - set(board.characters)
    if unknown:
        raise SystemExit(f"Personajes desconocidos: {', '.join(sorted(unknown))}")

    all_jobs = images.portrait_jobs(board, folder, args.opciones, args.seed)
    # Primero los personajes base y después los derivados (necesitan la cara ya elegida de su base).
    derived_depth = {n: _depth(n, board.bases) for n in board.characters}
    for depth in sorted(set(derived_depth.values())):
        jobs = []
        for name, options in all_jobs.items():
            if derived_depth[name] != depth:
                continue
            seed = state.get(name, {}).get("seed", options[0].seed)
            if name in redo:
                seed = random.randint(0, 2**31 - 1000)
            wanted = {"prompt": options[0].prompt, "seed": seed, "opciones": args.opciones,
                      "base": _base_hash(options[0].faces), "escala": options[0].ip_scale}
            if {"base": None, "escala": 0.6, **state.get(name, {})} != wanted:
                for old in folder.glob(f"{name}_*.png"):
                    old.unlink()
                state[name] = wanted
            for i, job in enumerate(options):
                job.seed = seed + i
            jobs += options

        images.generate(jobs, board.negative, args.model)
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        for name in board.characters:
            chosen = images.chosen_portrait(folder, name)
            if derived_depth[name] == depth and not chosen.exists():
                shutil.copyfile(folder / f"{name}_1.png", chosen)
                print(f"[personajes] {name}: elegida la opción 1 por defecto")
    print(f"[personajes] revisa {folder} y cambia la que no te guste con:\n"
          f"  python -m mangavid elegir {args.story} <personaje> <número>\n"
          f"  o rehaz sus opciones con: python -m mangavid personajes {args.story} --rehacer <personaje>")


def _depth(name: str, bases: dict[str, str]) -> int:
    depth = 0
    while name in bases:
        name, depth = bases[name], depth + 1
    return depth


def _base_hash(faces: list[Path]) -> str | None:
    return images._file_hash(faces[0]) if faces else None


def cmd_elegir(args) -> None:
    folder = _portraits_dir(args.story)
    name = args.personaje.lower()
    option = folder / f"{name}_{args.opcion}.png"
    if not option.exists():
        raise SystemExit(f"No existe {option}")
    shutil.copyfile(option, images.chosen_portrait(folder, name))
    print(f"[personajes] {name}: elegida la opción {args.opcion}. "
          "Las escenas donde sale se regenerarán en el próximo run.")


def cmd_run(args) -> None:
    board = storyboard.load(args.story)
    work = args.workdir or args.story.with_name(f"{args.story.stem}_work")
    output = args.output or args.story.with_suffix(".mp4")
    print(f"[guion] {len(board.scenes)} escenas, {len(board.characters)} personajes")

    _preflight_or_stop(board, args.story, args.forzar)
    shots = images.scene_shots(board, work / "images", _portraits_dir(args.story), args.seed, args.model)
    images.generate([j for js in shots for j in js], board.negative, args.model)
    pics = [[j.out for j in js] for js in shots]
    if args.only_images:
        print(f"[imágenes] en {work / 'images'}")
        return
    _review_gate_or_stop(work, [p for ps in pics for p in ps], args.forzar)
    voices = tts.synthesize(
        [Segment(0.0, 0.0, "", s.narration) for s in board.scenes], work / "voice", args.voice, args.rate
    )
    if any(v is None for v in voices):
        missing = [s.number for s, v in zip(board.scenes, voices) if v is None]
        raise SystemExit(f"Escenas sin narración: {missing}")
    render.render(board, pics, voices, work / "segments", output, args.music, args.music_volume, args.font_size)


def cmd_revisar(args) -> None:
    from . import review

    board = storyboard.load(args.story)
    work = args.workdir or args.story.with_name(f"{args.story.stem}_work")
    shots = images.scene_shots(board, work / "images", _portraits_dir(args.story), args.seed, args.model)
    missing = [j.out.name for js in shots for j in js if not j.out.exists()]
    if missing:
        raise SystemExit(f"Faltan {len(missing)} imágenes por generar. Ejecuta antes: "
                         f"python -m mangavid run {args.story} --only-images")
    pics = [[j.out for j in js] for js in shots]
    checks = review.check(board, pics)
    folder = work / "revision"
    sheets = review.contact_sheets(checks, folder)
    text = review.report(checks)
    if not args.sin_coherencia:
        from . import coherencia

        tools = coherencia.default_tools()
        pre = coherencia.preflight(board, _portraits_dir(args.story), tools.tag)
        reports = coherencia.check(board, pics, _portraits_dir(args.story), tools)
        coherencia.write_report(reports, pre, folder / "coherencia.json")
        text += "\n" + coherencia.report_text(reports, pre)
        text += f"\nInforme para el programa: {folder / 'coherencia.json'}"
    (folder / "informe.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"[revisión] {len(sheets)} hojas en {folder}")


def _preflight_or_stop(board, story: Path, force: bool) -> None:
    """Antes de generar: ficha, rostro de referencia, vestuario y miniatura (comprobación 8)."""
    from . import coherencia

    try:
        tag = coherencia.default_tools().tag
    except Exception as e:  # sin imgutils: solo las comprobaciones de texto
        print(f"[comprobar] sin etiquetador ({e}); el rostro de cada ficha no se compara")
        tag = None
    pre = coherencia.preflight(board, _portraits_dir(story), tag)
    bad = [r for r in pre if r.level == coherencia.CONFIRMED]
    if pre:
        print(coherencia.report_text([], pre))
    if bad and not force:
        raise SystemExit(f"[comprobar] {len(bad)} errores confirmados antes de producir. "
                         "Corrige las fichas o relanza con --forzar si lo has revisado.")


def _review_gate_or_stop(work: Path, pics: list[Path], force: bool) -> None:
    """Antes de montar: ninguna imagen sin revisar ni con fallos sin aprobar (comprobación 7)."""
    from . import coherencia

    folder = work / "revision"
    pending = coherencia.blockers(folder / "coherencia.json", coherencia.load_approvals(folder), pics)
    if not pending:
        return
    print("[montaje] imágenes que no pueden pasar al vídeo:")
    for line in pending[:40]:
        print("  " + line)
    if len(pending) > 40:
        print(f"  … y {len(pending) - 40} más")
    if not force:
        raise SystemExit("[montaje] parado. Revisa y aprueba esas imágenes, o relanza con --forzar.")
    print("[montaje] --forzar: se monta igualmente.")


def cmd_comprobar(args) -> None:
    from . import coherencia

    board = storyboard.load(args.story)
    pre = coherencia.preflight(board, _portraits_dir(args.story), coherencia.default_tools().tag)
    print(coherencia.report_text([], pre) if pre else "[comprobar] fichas, rostros, vestuario y miniatura: sin avisos")


def cmd_aprobar(args) -> None:
    from . import coherencia

    work = args.workdir or args.story.with_name(f"{args.story.stem}_work")
    folder = work / "revision"
    done = coherencia.approve(folder, folder / "coherencia.json", args.etiquetas)
    print(f"[aprobar] {len(done)} imágenes marcadas como revisadas a ojo")


def cmd_miniatura(args) -> None:
    from . import thumbnail

    board = storyboard.load(args.story)
    folder = args.story.with_name(f"{args.story.stem}_miniaturas")
    text = args.texto if args.texto is not None else board.thumbnail_text
    if args.imagen:
        # Imágenes hechas por el usuario (Fooocus, ChatGPT…): solo se les ponen los rótulos.
        # Las flechas van a los personajes en el orden en que salen en el texto, de izquierda a derecha.
        missing = [str(p) for p in args.imagen if not p.exists()]
        if missing:
            raise SystemExit(f"No encuentro: {', '.join(missing)}")
        cast = list(dict.fromkeys(i.character for i in thumbnail.parse_text(text) if i.character))
        picked = [(p, cast) for p in args.imagen]
    elif args.escena:
        # Reutiliza la imagen ya generada de una escena del vídeo: no hace falta GPU.
        work = args.workdir or args.story.with_name(f"{args.story.stem}_work")
        scene_jobs = images.scene_jobs(board, work / "images", _portraits_dir(args.story), 1234, args.model)
        picked = [(j.out, s.characters) for j, s in zip(scene_jobs, board.scenes) if s.number in args.escena]
        missing = [b.name for b, _ in picked if not b.exists()]
        if not picked or missing:
            raise SystemExit(f"Esas escenas no tienen imagen generada todavía: {args.escena}")
    else:
        jobs = thumbnail.jobs(board, folder, _portraits_dir(args.story), args.opciones, args.seed, args.model)
        images.generate(jobs, board.negative, args.model)
        cast = thumbnail.thumbnail_scene(board).characters
        picked = [(j.out, cast) for j in jobs]
    for old in folder.glob("miniatura_*.jpg"):
        old.unlink()
    outs = [thumbnail.compose(b, text, folder / f"miniatura_{i}.jpg", chars)
            for i, (b, chars) in enumerate(picked, start=1)]
    sheet = thumbnail.contact_sheet(outs, folder / "opciones.jpg")
    print(f"[miniatura] texto: «{text or '(sin texto)'}»")
    print(f"[miniatura] {len(outs)} opciones en {folder} (todas juntas en {sheet.name})")
    print("[miniatura] para cambiar solo el texto, relanza con --texto: las imágenes no se regeneran")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="mangavid", description="Historia en texto → vídeo estilo manhwa narrado")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("personajes", help="Paso 1: generar opciones de retrato de cada personaje")
    c.add_argument("story", type=Path)
    c.add_argument("--opciones", type=int, default=4, help="Retratos a elegir por personaje")
    c.add_argument("--rehacer", nargs="*", default=[], help="Personajes a los que rehacer las opciones")
    c.add_argument("--seed", type=int, default=777)
    c.add_argument("--model", default=images.DEFAULT_MODEL)
    c.set_defaults(func=cmd_personajes)

    e = sub.add_parser("elegir", help="Paso 2: fijar el retrato elegido de un personaje")
    e.add_argument("story", type=Path)
    e.add_argument("personaje")
    e.add_argument("opcion", type=int)
    e.set_defaults(func=cmd_elegir)

    r = sub.add_parser("run", help="Paso 3: generar escenas, voz y vídeo")
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
    r.add_argument("--forzar", action="store_true",
                   help="Producir aunque haya errores de coherencia confirmados o imágenes sin aprobar")
    r.set_defaults(func=cmd_run)

    m = sub.add_parser("miniatura", help="Opciones de miniatura de YouTube con texto grande")
    m.add_argument("story", type=Path)
    m.add_argument("--texto", help='Rótulos separados por |: "@kai=PROTA | @luna=HIJA | ¡No saltes!". '
                                   "Por defecto, el de @miniatura_texto")
    m.add_argument("--opciones", type=int, default=4, help="Imágenes distintas a generar")
    m.add_argument("--escena", type=int, nargs="*", help="Usar la imagen ya generada de estas escenas")
    m.add_argument("--imagen", type=Path, nargs="*",
                   help="Usar tus propias imágenes (Fooocus, ChatGPT…) y solo ponerles los rótulos. "
                        "Escribe las etiquetas @personaje en orden de izquierda a derecha")
    m.add_argument("--workdir", type=Path)
    m.add_argument("--seed", type=int, default=4242)
    m.add_argument("--model", default=images.DEFAULT_MODEL)
    m.set_defaults(func=cmd_miniatura)

    v = sub.add_parser("revisar", help="Detectar personajes duplicados y preparar hojas de revisión")
    v.add_argument("story", type=Path)
    v.add_argument("--workdir", type=Path)
    v.add_argument("--seed", type=int, default=1234)
    v.add_argument("--model", default=images.DEFAULT_MODEL, help="El mismo modelo con el que se generaron las escenas")
    v.add_argument("--sin-coherencia", action="store_true",
                   help="No comprobar que cada personaje salga igual (ojos, pelo, ropa) en todas las escenas")
    v.set_defaults(func=cmd_revisar)

    c2 = sub.add_parser("comprobar", help="Antes de producir: fichas, rostros elegidos, vestuario y miniatura")
    c2.add_argument("story", type=Path)
    c2.set_defaults(func=cmd_comprobar)

    a = sub.add_parser("aprobar", help="Marcar imágenes como revisadas a ojo tras el informe de coherencia")
    a.add_argument("story", type=Path)
    a.add_argument("etiquetas", nargs="+", help="Etiquetas del informe, p. ej. 003b 004")
    a.add_argument("--workdir", type=Path)
    a.set_defaults(func=cmd_aprobar)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
