import json
import subprocess
from pathlib import Path

import pytest

from dubber import media
from dubber.masks import Mask, build_video_filter, clamp, parse_mask
from dubber.pipeline import Config, output_paths, preview_frame, render, write_texts
from dubber.segments import (Segment, format_timestamp, load_segments, save_segments, to_srt,
                             to_transcript)


def test_timestamp():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(3725.4567) == "01:02:05,457"


def test_srt_skips_empty_and_wraps():
    segs = [Segment(0, 1.5, "你好", "Hola"), Segment(2, 3, "x", ""),
            Segment(3, 6, "y", "palabra " * 12)]
    srt = to_srt(segs, width=42)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\nHola\n")
    assert "\n2\n00:00:03,000 --> " in srt
    assert all(len(line) <= 42 for line in srt.splitlines())


def test_srt_splits_long_text_into_two_line_blocks():
    srt = to_srt([Segment(10, 20, "", "palabra " * 30)], width=42)
    blocks = [b.splitlines() for b in srt.strip().split("\n\n")]
    assert len(blocks) == 3
    assert all(len(b) - 2 <= 2 for b in blocks)  # número, tiempos y como mucho 2 líneas
    assert blocks[0][1].startswith("00:00:10,000 --> ")
    assert blocks[-1][1].endswith(" --> 00:00:20,000")
    # cada bloque empieza donde acaba el anterior
    assert blocks[0][1].split(" --> ")[1] == blocks[1][1].split(" --> ")[0]


def test_segments_roundtrip(tmp_path):
    segs = [Segment(2, 3, "二", "dos"), Segment(0, 1, "一", "uno")]
    save_segments(segs, tmp_path / "s.json")
    assert json.loads((tmp_path / "s.json").read_text(encoding="utf-8"))[0]["source"] == "二"
    assert [s.text for s in load_segments(tmp_path / "s.json")] == ["uno", "dos"]


@pytest.mark.parametrize("speed,expected", [
    (1.3, "atempo=1.3000"),
    (3.0, "atempo=2.0000,atempo=1.5000"),
    (0.25, "atempo=0.5000,atempo=0.5000"),
])
def test_atempo(speed, expected):
    assert media.atempo_filter(speed) == expected


def test_parse_mask():
    assert parse_mask("10,20,30,40") == Mask("blur", 10, 20, 30, 40)
    assert parse_mask("box:0,600,1280,120") == Mask("box", 0, 600, 1280, 120)
    for bad in ("pixel:1,2,3,4", "1,2,3", "blur:1,2,0,4"):
        with pytest.raises(ValueError):
            parse_mask(bad)


def test_clamp_keeps_inside_frame():
    m = clamp(Mask("delogo", -5, 700, 5000, 300), 1280, 720)
    assert m.x >= 1 and m.y >= 1
    assert m.x + m.w <= 1279 and m.y + m.h <= 719
    assert all(v % 2 == 0 for v in (m.x, m.y, m.w, m.h))


def test_filter_none_when_nothing_to_do():
    assert build_video_filter([], 640, 360) is None


def _make_video(path: Path, seconds: float = 4.0) -> Path:
    media.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size=640x360:rate=25:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=300:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path,
    ])
    return path


def _fake_tts(segments, workdir, voice=None, rate=None):
    workdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, seg in enumerate(segments):
        p = workdir / f"tts_{i}.wav"
        # frase de 1.8 s para forzar la aceleración en huecos de 1 s
        media.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=1.8", p])
        paths.append(p)
    return paths


@pytest.mark.parametrize("background", ["duck", "none"])
def test_render_end_to_end(tmp_path, background):
    video = _make_video(tmp_path / "in.mp4")
    segs = [Segment(0.5, 1.5, "一", "Hola, ¿qué tal?"), Segment(1.5, 3.0, "二", "Muy bien: gracias")]
    cfg = Config(
        input=video, output=tmp_path / "out" / "final.mp4", workdir=tmp_path / "work",
        background=background,
        masks=[parse_mask("blur:10,10,200,80"), parse_mask("delogo:400,250,120,60"),
               parse_mask("box:0,300,640,60")],
    )
    cfg.workdir.mkdir()
    cfg.output.parent.mkdir()
    audio = media.extract_audio(video, cfg.workdir / "original.wav")
    write_texts(cfg, segs)
    out = render(cfg, segs, audio if background != "none" else None,
                 media.duration(video), synthesize=_fake_tts)

    assert out.exists()
    assert media.video_size(out) == (640, 360)
    assert media.has_audio(out)
    assert abs(media.duration(out) - 4.0) < 0.3
    assert "Muy bien: gracias" in (tmp_path / "out" / "final.srt").read_text(encoding="utf-8")
    assert "二" in (tmp_path / "out" / "final_original.srt").read_text(encoding="utf-8")
    mp3 = tmp_path / "out" / "final.mp3"
    assert mp3.exists() and abs(media.duration(mp3) - 4.0) < 0.3


def test_preview_frame(tmp_path):
    video = _make_video(tmp_path / "in.mp4", 2)
    out = preview_frame(video, [parse_mask("blur:0,0,640,100")], tmp_path / "p.png")
    assert out.exists() and out.stat().st_size > 0


def test_cli_help():
    r = subprocess.run(["python3", "-m", "dubber", "run", "--help"], capture_output=True, text=True,
                       cwd=Path(__file__).parent.parent)
    assert r.returncode == 0 and "--mask" in r.stdout


def test_transcript_and_original_srt():
    segs = [Segment(1, 2, "你好", "Hola")]
    assert to_transcript(segs) == "[00:00:01] 你好\n           Hola\n"
    assert "你好" in to_srt(segs, field="source")


def test_output_paths(tmp_path):
    cfg = Config(input=tmp_path / "a.mp4", output=tmp_path / "a_es.mp4", workdir=tmp_path)
    p = output_paths(cfg)
    assert p["video"].name == "a_es.mp4" and p["audio"].name == "a_es.mp3"
    assert p["transcript"].name == "a_es.txt" and p["srt_original"].name == "a_es_original.srt"
    cfg.output = tmp_path / "b_es.mp3"
    assert output_paths(cfg)["video"] is None


def test_audio_only_with_cover_art(tmp_path):
    cover = tmp_path / "cover.png"
    media.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=red:size=64x64", "-frames:v", "1", cover])
    song = tmp_path / "song.mp3"
    media.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=3", "-i", cover,
               "-map", "0:a", "-map", "1:v", "-c:a", "libmp3lame", "-c:v", "png",
               "-disposition:v", "attached_pic", song])
    assert media.has_audio(song) and not media.has_video(song)

    cfg = Config(input=song, output=tmp_path / "song_es.mp3", workdir=tmp_path / "work",
                 masks=[parse_mask("blur:0,0,10,10")])
    cfg.workdir.mkdir()
    audio = media.extract_audio(song, cfg.workdir / "original.wav")
    segs = [Segment(0.5, 2.5, "一", "Hola")]
    write_texts(cfg, segs)
    out = render(cfg, segs, audio, media.duration(song), synthesize=_fake_tts)
    assert out == cfg.output and out.exists()
    assert not media.has_video(out)
    assert (tmp_path / "song_es.txt").exists()


def test_voice_track_never_overlaps(tmp_path):
    from dubber.audio_mix import build_voice_track

    segs = [Segment(0.5, 1.0, "一", "uno"), Segment(1.0, 1.5, "二", "dos")]
    clips = _fake_tts(segs, tmp_path / "tts")  # 1.8 s cada una, huecos de 0.5 s
    out = build_voice_track(segs, clips, 6.0, tmp_path / "v.wav", max_speed=1.0)
    track = media.decode_mono(out)
    # sine de ffmpeg tiene amplitud 1/8: si dos voces se sumaran, superaría ese valor
    assert abs(track).max() < 0.13
    # la segunda frase se desplaza hasta después de la primera
    sr = media.SAMPLE_RATE
    assert abs(track[int(2.45 * sr):int(2.55 * sr)]).max() > 0.05


def test_script_roundtrip_and_formats(tmp_path):
    from dubber.script import apply_translation, export_script, parse_script

    segs = [Segment(0, 1, "你好"), Segment(1, 2, "朋友们"), Segment(2, 3, "再见")]
    zh = export_script(segs, tmp_path / "g_zh.txt", "v.mp4")
    assert "[001] 你好" in zh.read_text(encoding="utf-8")
    assert parse_script(zh.read_text(encoding="utf-8")) == {1: "你好", 2: "朋友们", 3: "再见"}
    # Formatos que suelen devolver los traductores
    assert parse_script("[001] Hola\n2. Amigos\n003) Adiós") == {1: "Hola", 2: "Amigos", 3: "Adiós"}
    # Los puntos suspensivos del principio no se confunden con «2.»
    assert parse_script("[001] ...y se fue\n2. ...vale") == {1: "...y se fue", 2: "...vale"}

    es = tmp_path / "g_es.txt"
    es.write_text("# comentario\n[001] Hola\n[002] Amigos\n[003] Adiós\n", encoding="utf-8")
    assert [s.text for s in apply_translation(segs, es)] == ["Hola", "Amigos", "Adiós"]

    es.write_text("[001] Hola\n[003] Adiós\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Faltan 1 de 3"):
        apply_translation(segs, es)


def test_translation_flow_text_only(tmp_path):
    from dubber.pipeline import run

    video = _make_video(tmp_path / "v.mp4", 3)
    work = tmp_path / "v_work"
    work.mkdir()
    save_segments([Segment(0.2, 1.0, "你好"), Segment(1.2, 2.5, "再见")], work / "segments.json")
    es = tmp_path / "v_guion_es.txt"
    es.write_text("[001] Hola\n[002] Adiós\n", encoding="utf-8")

    cfg = Config(input=video, output=tmp_path / "v_es.mp4", workdir=work,
                 translation_file=es, stop_after_translate=True)
    assert run(cfg) is None
    transcript = (tmp_path / "v_es.txt").read_text(encoding="utf-8")
    assert "你好" in transcript and "Hola" in transcript and "Adiós" in transcript
    assert [s.text for s in load_segments(work / "segments.json")] == ["Hola", "Adiós"]
