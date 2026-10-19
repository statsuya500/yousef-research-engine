import json
import subprocess
from pathlib import Path

import pytest

from dubber import media
from dubber.masks import Mask, build_video_filter, clamp, parse_mask
from dubber.pipeline import Config, preview_frame, render
from dubber.segments import Segment, format_timestamp, load_segments, save_segments, to_srt


def test_timestamp():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(3725.4567) == "01:02:05,457"


def test_srt_skips_empty_and_wraps():
    segs = [Segment(0, 1.5, "你好", "Hola"), Segment(2, 3, "x", ""),
            Segment(3, 6, "y", "palabra " * 12)]
    srt = to_srt(segs, width=42)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\nHola\n")
    assert "\n2\n00:00:03,000 --> 00:00:06,000\n" in srt
    assert all(len(line) <= 42 for line in srt.splitlines())


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
    out = render(cfg, segs, audio if background != "none" else None,
                 media.duration(video), synthesize=_fake_tts)

    assert out.exists()
    assert media.video_size(out) == (640, 360)
    assert media.has_audio(out)
    assert abs(media.duration(out) - 4.0) < 0.3
    assert "Muy bien: gracias" in (tmp_path / "out" / "final.srt").read_text(encoding="utf-8")


def test_preview_frame(tmp_path):
    video = _make_video(tmp_path / "in.mp4", 2)
    out = preview_frame(video, [parse_mask("blur:0,0,640,100")], tmp_path / "p.png")
    assert out.exists() and out.stat().st_size > 0


def test_cli_help():
    r = subprocess.run(["python3", "-m", "dubber", "run", "--help"], capture_output=True, text=True,
                       cwd=Path(__file__).parent.parent)
    assert r.returncode == 0 and "--mask" in r.stdout
