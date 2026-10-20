"""Flujo completo: audio → transcripción → traducción → voz → mezcla → vídeo final."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import audio_mix, media
from .masks import DEFAULT_SUB_STYLE, Mask, build_video_filter
from .segments import Segment, load_segments, save_segments, to_srt, to_transcript
from .translate import DEFAULT_MODEL
from .tts import DEFAULT_VOICE

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


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
    translation_file: Path | None = None
    stop_after_translate: bool = False


def transcribe_only(cfg: Config, audio: Path | None) -> list[Segment]:
    """Transcribe sin traducir, o reutiliza la transcripción guardada en la carpeta de trabajo."""
    path = cfg.workdir / "segments.json"
    if path.exists():
        print(f"[segmentos] reutilizando la transcripción de {path}")
        return load_segments(path)
    if audio is None:
        raise ValueError("El archivo no tiene audio que transcribir")
    from .transcribe import transcribe

    segments = transcribe(audio, cfg.src_lang, cfg.whisper_model)
    save_segments(segments, path)
    return segments


def prepare_segments(cfg: Config, audio: Path | None) -> list[Segment]:
    if cfg.segments_file:
        print(f"[segmentos] usando {cfg.segments_file}")
        segments = load_segments(cfg.segments_file)
    elif cfg.translation_file:
        segments = transcribe_only(cfg, audio)
    else:
        if audio is None:
            raise ValueError("El archivo no tiene audio que transcribir; pasa --segments")
        from .transcribe import transcribe
        from .translate import translate_segments

        segments = transcribe(audio, cfg.src_lang, cfg.whisper_model)
        segments = translate_segments(segments, cfg.src_lang, cfg.tgt_lang, cfg.translator_model)

    if cfg.translation_file:
        from .script import apply_translation

        segments = apply_translation(segments, cfg.translation_file)

    path = cfg.workdir / "segments.json"
    if not cfg.segments_file or cfg.segments_file.resolve() != path.resolve():
        save_segments(segments, path)
        print(f"[segmentos] guardados en {path}")
    return segments


def export_script_for(cfg: Config) -> Path:
    """Paso 1 del flujo con traducción externa: guion numerado sin tiempos."""
    from .script import export_script

    cfg.workdir.mkdir(parents=True, exist_ok=True)
    audio = None
    if media.has_audio(cfg.input):
        audio = media.extract_audio(cfg.input, cfg.workdir / "original.wav")
    segments = transcribe_only(cfg, audio)
    out = cfg.input.with_suffix("").parent / f"{cfg.input.stem}_guion_{cfg.src_lang}.txt"
    export_script(segments, out, cfg.input.name)
    print(f"[guion] {out} ({len(segments)} líneas). Tradúcelo y pásalo con --translation")
    return out


def output_paths(cfg: Config) -> dict[str, Path]:
    """Archivos de salida, todos junto a cfg.output con el mismo nombre base."""
    base = cfg.output.with_suffix("")
    is_audio_out = cfg.output.suffix.lower() in AUDIO_EXTS
    return {
        "video": None if is_audio_out else cfg.output,
        "audio": cfg.output if is_audio_out else base.with_suffix(".mp3"),
        "srt": base.with_suffix(".srt"),
        "srt_original": base.parent / f"{base.name}_original.srt",
        "transcript": base.with_suffix(".txt"),
    }


def write_texts(cfg: Config, segments: list[Segment]) -> None:
    paths = output_paths(cfg)
    paths["transcript"].write_text(to_transcript(segments), encoding="utf-8")
    paths["srt_original"].write_text(to_srt(segments, field="source"), encoding="utf-8")
    paths["srt"].write_text(to_srt(segments), encoding="utf-8")
    print(f"[texto] {paths['transcript']}, {paths['srt']}, {paths['srt_original']}")


def mix_audio(cfg: Config, voice: Path, background: Path | None) -> Path:
    if background is None:
        return voice
    bg_vol = 1.0 if cfg.background == "separate" else cfg.bg_volume
    out = cfg.workdir / "mix.wav"
    media.run([
        "ffmpeg", "-y", "-i", voice, "-i", background, "-filter_complex",
        "[0:a]aformat=channel_layouts=stereo[vo];"
        f"[1:a]volume={bg_vol},aformat=channel_layouts=stereo[bg];"
        "[vo][bg]amix=inputs=2:duration=first:dropout_transition=0,volume=2",
        "-ar", media.SAMPLE_RATE, out,
    ])
    return out


def render(
    cfg: Config,
    segments: list[Segment],
    original_audio: Path | None,
    total: float,
    synthesize: Callable[..., list[Path | None]] | None = None,
) -> Path:
    work = cfg.workdir
    paths = output_paths(cfg)
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
    mix = mix_audio(cfg, voice, background)

    media.run(["ffmpeg", "-y", "-i", mix, "-c:a", "libmp3lame", "-q:a", "2", paths["audio"]])
    print(f"[audio] {paths['audio']}")

    if paths["video"] is None or not media.has_video(cfg.input):
        return paths["audio"]

    srt_name = None
    if cfg.subtitles and cfg.burn_subtitles:
        srt = work / "subtitles.srt"
        srt.write_text(to_srt(segments), encoding="utf-8")
        srt_name = srt.name

    width, height = media.video_size(cfg.input)
    vfilter = build_video_filter(cfg.masks, width, height, srt_name, cfg.sub_style)

    cmd: list = ["ffmpeg", "-y", "-i", cfg.input.resolve(), "-i", mix.resolve()]
    if vfilter:
        cmd += ["-filter_complex", vfilter, "-map", "[vout]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20"]
    else:
        cmd += ["-map", "0:v", "-c:v", "copy"]
    cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", paths["video"].resolve()]
    print("[vídeo] renderizando…")
    media.run(cmd, cwd=work)
    print(f"[listo] {paths['video']}")
    return paths["video"]


def run(cfg: Config) -> Path | None:
    cfg.workdir.mkdir(parents=True, exist_ok=True)
    cfg.output.parent.mkdir(parents=True, exist_ok=True)
    if not media.has_video(cfg.input) and cfg.masks:
        print("[aviso] la entrada es solo audio: se ignoran las zonas a tapar")
    total = media.duration(cfg.input)
    audio = None
    if media.has_audio(cfg.input):
        audio = media.extract_audio(cfg.input, cfg.workdir / "original.wav")
    segments = prepare_segments(cfg, audio)
    write_texts(cfg, segments)
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
