"""Monta el vídeo: un tramo por escena (imagen con movimiento + voz + subtítulos) y los une.

Cada tramo se guarda con un hash de su contenido, así que en vídeos de horas
solo se vuelven a montar las escenas que cambian, y si se corta se reanuda.
"""

from __future__ import annotations

import hashlib
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dubber import media
from dubber.masks import DEFAULT_SUB_STYLE
from dubber.segments import Segment, format_timestamp, to_srt

from .storyboard import Storyboard

FPS = 30
SIZE = (1920, 1080)
PAUSE = 0.5  # silencio al final de cada escena
ZOOM = 0.12  # cuánto se acerca o se desplaza la imagen durante la escena
RENDER_VERSION = "1"  # súbelo si cambia el montaje para invalidar la caché


def _motion(index: int, frames: int) -> str:
    """Efecto Ken Burns: alterna acercar, alejar y desplazar a un lado u otro."""
    center = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    progress = f"on/{max(frames - 1, 1)}"
    return [
        f"z='1+{ZOOM}*{progress}':{center}",
        f"z='{1 + ZOOM}-{ZOOM}*{progress}':{center}",
        f"z='{1 + ZOOM}':x='(iw-iw/zoom)*{progress}':y='ih/2-(ih/zoom/2)'",
        f"z='{1 + ZOOM}':x='(iw-iw/zoom)*(1-{progress})':y='ih/2-(ih/zoom/2)'",
    ][index % 4]


def _render_scene(index: int, shots: list[Path], voice: Path, narration: str, out: Path, style: str) -> None:
    """Los planos de la escena se reparten a partes iguales el tiempo de la narración."""
    speech = media.duration(voice)
    total = speech + PAUSE
    frames = math.ceil(total * FPS)
    w, h = SIZE
    srt = out.with_suffix(".srt")
    srt.write_text(to_srt([Segment(0.0, speech, "", narration)]), encoding="utf-8")
    n = len(shots)
    parts = []
    for k in range(n):
        d = frames // n + (1 if k < frames % n else 0)
        parts.append(
            f"[{k}:v]scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan={_motion(index * n + k, d)}:d={d}:s={w}x{h}:fps={FPS},setsar=1[s{k}]"
        )
    joined = "".join(f"[s{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0" if n > 1 else "[s0]null"
    vfilter = (
        ";".join(parts) + f";{joined},subtitles='{srt.name}':force_style='{style}',format=yuv420p[v]"
    )
    inputs = [arg for p in shots for arg in ("-i", p.resolve())]
    tmp = out.with_suffix(".tmp.mp4")
    media.run(
        [
            "ffmpeg", "-y", "-v", "error", *inputs, "-i", voice.resolve(),
            "-filter_complex", f"{vfilter};[{n}:a]aresample={media.SAMPLE_RATE},apad[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ac", "2",
            tmp.name,
        ],
        cwd=out.parent,
    )
    tmp.replace(out)
    srt.unlink()


def render(
    board: Storyboard,
    images: list[list[Path]],  # los planos de cada escena
    voices: list[Path],
    workdir: Path,
    output: Path,
    music: Path | None = None,
    music_volume: float = 0.12,
    font_size: int = 16,
    workers: int = 3,
) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    style = DEFAULT_SUB_STYLE.replace("FontSize=16", f"FontSize={font_size}")
    jobs = []
    for i, (scene, shots, voice) in enumerate(zip(board.scenes, images, voices)):
        names = "+".join(p.name for p in shots)  # con un solo plano, la misma clave que antes
        key = hashlib.sha1(
            f"{RENDER_VERSION}|{names}|{voice.name}|{scene.narration}|{i % 4}|{style}".encode()
        ).hexdigest()[:10]
        jobs.append((i, shots, voice, scene.narration, workdir / f"seg_{scene.number:04d}_{key}.mp4"))

    todo = [j for j in jobs if not j[4].exists()]
    print(f"[montaje] {len(todo)} tramos nuevos de {len(jobs)}")
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in pool.map(lambda j: _render_scene(*j, style), todo):
            done += 1
            if done % 10 == 0 or done == len(todo):
                print(f"[montaje] {done}/{len(todo)}", flush=True)

    segments = [j[4] for j in jobs]
    _write_full_srt(board, segments, output.with_suffix(".srt"))
    concat = workdir / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8")

    joined = workdir / "joined.mp4" if music else output
    media.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat.name,
               "-c", "copy", "-movflags", "+faststart", joined.resolve()], cwd=workdir)
    if music:
        media.run([
            "ffmpeg", "-y", "-v", "error", "-i", joined, "-stream_loop", "-1", "-i", music,
            "-filter_complex",
            f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", output,
        ])
        joined.unlink()
    print(f"[listo] {output} ({media.duration(output) / 60:.1f} min)")
    return output


def _write_full_srt(board: Storyboard, segments: list[Path], path: Path) -> None:
    """Subtítulos de todo el vídeo, para subirlos a YouTube por separado si se quiere."""
    timeline, t = [], 0.0
    for scene, seg in zip(board.scenes, segments):
        length = media.duration(seg)
        timeline.append(Segment(t, t + max(length - PAUSE, 0.1), "", scene.narration))
        t += length
    path.write_text(to_srt(timeline), encoding="utf-8")
    print(f"[subtítulos] {path} (fin {format_timestamp(t)})")
