"""Flujo completo: audio → transcripción → traducción → voz → mezcla → vídeo final."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import audio_mix, media
from .masks import DEFAULT_SUB_STYLE, Mask, build_video_filter
from .segments import Segment, load_segments, save_segments, to_srt
from .translate import DEFAULT_MODEL
from .tts import DEFAULT_VOICE


@dataclass
class Config:
    input: Path
    output: Path
    workdir: Path
    src_lang: str = "zh"
    tgt_lang: str = "es"
    whisper_model: str = "large-v3"
    translator_model: str = DEFAULT_MODEL
    voice: str = DEFAULT_VOICE
    rate: str = "+0%"
    max_speed: float = 1.5
    background: str = "duck"  # duck | separate | none
    bg_volume: float = 0.2
    masks: list[Mask] = field(default_factory=list)
    subtitles: bool = True
    burn_subtitles: bool = True
    sub_style: str = DEFAULT_SUB_STYLE
    segments_file: Path | None = None
    stop_after_translate: bool = False


def prepare_segments(cfg: Config, audio: Path | None) -> list[Segment]:
    if cfg.segments_file:
        print(f"[segmentos] usando {cfg.segments_file}")
        return load_segments(cfg.segments_file)
    if audio is None:
        raise ValueError("El vídeo no tiene audio que transcribir; pasa --segments")
    from .transcribe import transcribe
    from .translate import translate_segments

    segments = transcribe(audio, cfg.src_lang, cfg.whisper_model)
    segments = translate_segments(segments, cfg.src_lang, cfg.tgt_lang, cfg.translator_model)
    path = cfg.workdir / "segments.json"
    save_segments(segments, path)
    print(f"[segmentos] guardados en {path} (puedes editar las traducciones y relanzar con --segments)")
    return segments


def render(
    cfg: Config,
    segments: list[Segment],
    original_audio: Path | None,
    total: float,
    synthesize: Callable[..., list[Path | None]] | None = None,
) -> Path:
    work = cfg.workdir
    if synthesize is None:
        from .tts import synthesize
    clips = synthesize(segments, work / "tts", voice=cfg.voice, rate=cfg.rate)
    voice = audio_mix.build_voice_track(segments, clips, total, work / "voice.wav", cfg.max_speed)

    background = None
    if original_audio is not None and cfg.background != "none":
        if cfg.background == "separate":
            print("[fondo] separando música y voz con Demucs…")
            background = audio_mix.separate_background(original_audio, work)
        else:
            background = original_audio

    srt_name = None
    if cfg.subtitles:
        srt = work / "subtitles.srt"
        srt.write_text(to_srt(segments), encoding="utf-8")
        shutil.copy(srt, cfg.output.with_suffix(".srt"))
        srt_name = srt.name if cfg.burn_subtitles else None

    width, height = media.video_size(cfg.input)
    vfilter = build_video_filter(cfg.masks, width, height, srt_name, cfg.sub_style)

    cmd: list = ["ffmpeg", "-y", "-i", cfg.input.resolve(), "-i", voice.resolve()]
    graph = [vfilter] if vfilter else []
    if background is not None:
        cmd += ["-i", background.resolve()]
        bg_vol = 1.0 if cfg.background == "separate" else cfg.bg_volume
        graph.append(
            "[1:a]aformat=channel_layouts=stereo[vo];"
            f"[2:a]volume={bg_vol},aformat=channel_layouts=stereo[bg];"
            "[vo][bg]amix=inputs=2:duration=first:dropout_transition=0,volume=2[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = "1:a"
    if graph:
        cmd += ["-filter_complex", ";".join(graph)]
    cmd += ["-map", "[vout]" if vfilter else "0:v", "-map", audio_map]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20"] if vfilter else ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
            cfg.output.resolve()]
    print("[vídeo] renderizando…")
    media.run(cmd, cwd=work)
    print(f"[listo] {cfg.output}")
    return cfg.output


def run(cfg: Config) -> Path | None:
    cfg.workdir.mkdir(parents=True, exist_ok=True)
    cfg.output.parent.mkdir(parents=True, exist_ok=True)
    total = media.duration(cfg.input)
    audio = None
    if media.has_audio(cfg.input):
        audio = media.extract_audio(cfg.input, cfg.workdir / "original.wav")
    segments = prepare_segments(cfg, audio)
    if cfg.stop_after_translate:
        return None
    return render(cfg, segments, audio, total)


def preview_frame(video: Path, masks: list[Mask], out: Path, at: float = 1.0) -> Path:
    """Saca un fotograma con las zonas aplicadas para comprobar las coordenadas."""
    width, height = media.video_size(video)
    vfilter = build_video_filter(masks, width, height)
    cmd: list = ["ffmpeg", "-y", "-ss", at, "-i", video]
    if vfilter:
        cmd += ["-filter_complex", vfilter, "-map", "[vout]"]
    cmd += ["-frames:v", 1, out]
    media.run(cmd)
    return out
