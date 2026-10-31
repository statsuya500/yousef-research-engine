"""Monta un vídeo de mangavid dando a la ventana del sistema el tiempo que la voz tarda en leer su texto («…») + 1 s.
Uso: render_sistema.py <carpeta historia> <vídeo de salida> <carpeta de tramos>
La ventana se coloca en el momento en que la voz empieza a leer el texto del sistema (estimado por la posición del texto
en la narración, proporcional a los caracteres); el resto del tiempo se reparte entre las demás imágenes."""
import json, math, re, sys
from pathlib import Path
from dubber import tts, media
from dubber.segments import Segment, to_srt
from mangavid import storyboard, render
import subprocess
# NVENC si el ffmpeg lo tiene (PC); si no (algunos Colab), libx264.
CODEC = (["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23"] if "h264_nvenc" in subprocess.run(
    ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21"])
H, OUT, WORK = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
EXTRA = 1.0  # segundos extra tras terminar de leer
reg = json.loads((H/'escenas'/'registro.json').read_text())['imagenes']
board = storyboard.load(H/'historia.txt')
pics, plan_w = [], {}
for s in board.scenes:
    files = sorted((H/'escenas').glob(f'escena_{s.number:03d}_*.png'))
    sysf = [f for f in files if reg.get(f.name, {}).get('tipo') == 'ventana del sistema']
    if not sysf: pics.append(files); continue
    txt = s.narration; i0 = txt.find('«'); i1 = txt.rfind('»') + 1
    f0, f1 = i0 / len(txt), i1 / len(txt)
    others = [f for f in files if f not in sysf]; sf = sysf[0]
    pos = min(len(others), round(f0 * len(others)))                 # dónde va la ventana entre las demás
    order = others[:pos] + [sf] + others[pos:]
    pics.append(order); plan_w[s.number] = (pos, f0, f1, len(order))
voices = tts.synthesize([Segment(0.0, 0.0, '', s.narration) for s in board.scenes], H/'trabajo'/'voz', tts.DEFAULT_VOICE, '+0%')
orig = render._render_scene
def weighted(index, shots, voice, narration, out, style):
    num = int(out.name[4:8])
    if num not in plan_w: return orig(index, shots, voice, narration, out, style)
    pos, f0, f1, n = plan_w[num]
    speech = media.duration(voice); total = speech + render.PAUSE; frames = math.ceil(total * render.FPS)
    t0, t1 = f0 * speech, min(total, f1 * speech + EXTRA)            # la ventana: desde que empieza a leerse hasta el final + 1 s
    before, after = t0, total - t1
    nb, na = pos, n - pos - 1
    if nb == 0: t1 += 0; before = 0                                   # sin imágenes antes: la ventana empieza en 0
    if na == 0: t1 = total                                            # sin imágenes después: la ventana llega al final
    durs = ([before / nb] * nb if nb else []) + [t1 - (t0 if nb else 0)] + ([(total - t1) / na] * na if na else [])
    fr = [max(1, round(d * render.FPS)) for d in durs]; fr[-1] += frames - sum(fr)
    w, h = render.SIZE
    srt = out.with_suffix('.srt'); srt.write_text(to_srt([Segment(0.0, speech, '', narration)]), encoding='utf-8')
    parts = [f"[{k}:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
             f"zoompan={render._motion(index * n + k, d)}:d={d}:s={w}x{h}:fps={render.FPS},setsar=1[s{k}]" for k, d in enumerate(fr)]
    joined = "".join(f"[s{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0"
    vfilter = ";".join(parts) + f";{joined},subtitles='{srt.name}':force_style='{style}',format=yuv420p[v]"
    inputs = [a for p in shots for a in ("-i", p.resolve())]
    tmp = out.with_suffix('.tmp.mp4')
    media.run(["ffmpeg", "-y", "-v", "error", *inputs, "-i", voice.resolve(),
               "-filter_complex", f"{vfilter};[{n}:a]aresample={media.SAMPLE_RATE},apad[a]",
               "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", *CODEC,
               "-r", str(render.FPS), "-c:a", "aac", "-b:a", "192k", "-ac", "2", tmp.name], cwd=out.parent)
    tmp.replace(out); srt.unlink()
    print(f'[sistema] escena {num}: ventana {fr[pos]/render.FPS:.1f} s de {total:.1f} s', flush=True)
render._render_scene = weighted
render.render(board, pics, voices, WORK, OUT, workers=2)
