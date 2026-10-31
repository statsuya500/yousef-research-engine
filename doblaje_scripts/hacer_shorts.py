"""Shorts verticales 1080x1920 desde un vídeo largo de mangavid: gancho nuevo (voz + texto) + tramo de escenas a..b.
Uso: hacer_shorts.py <carpeta historia> <vídeo largo> <shorts.json>"""
import json, subprocess, sys
from pathlib import Path
from dubber import tts, media
from dubber.segments import Segment, to_srt
from mangavid import render
H, LONG, SPEC = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text())
O = H/'shorts'; W = O/'trabajo'; W.mkdir(parents=True, exist_ok=True)
FONT = '/home/jamal/doblaje/mangavid/fonts/Anton-Regular.ttf'
d = json.loads((H/'trabajo'/'duraciones.json').read_text()); st, t = {}, 0.0
for n in sorted(d, key=int): st[int(n)] = t; t += d[n] + render.PAUSE
def ts(s):
    h, m, r = s.split(':'); sec, ms = r.split(','); return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000
srt = []
for b in LONG.with_suffix('.srt').read_text(encoding='utf-8').strip().split('\n\n'):
    l = b.split('\n'); a, z = l[1].split(' --> '); srt.append((ts(a), ts(z), ' '.join(l[2:])))
run = lambda *c: subprocess.run(['ffmpeg', '-y', '-v', 'error', *map(str, c)], check=True)
info = []
for s in SPEC:
    n = s['n']; a = st[s['a']]; z = st[s['b']] + d[str(s['b'])] + 0.4
    voice = tts.synthesize([Segment(0.0, 0.0, '', s['gancho'])], W/f'gancho_{n}', tts.DEFAULT_VOICE, '+0%')[0]
    hd = media.duration(voice) + 0.3
    clip, still, hook, joined = W/f'tramo_{n}.mp4', W/f'quieto_{n}.png', W/f'gancho_{n}.mp4', W/f'unido_{n}.mp4'
    run('-ss', f'{a:.3f}', '-to', f'{z:.3f}', '-i', LONG, '-c:v', 'h264_nvenc', '-cq', '20', '-c:a', 'aac', '-ar', '48000', '-ac', '2', clip)
    run('-ss', '1.5', '-i', clip, '-frames:v', '1', still)
    run('-loop', '1', '-i', still, '-i', voice, '-t', f'{hd:.3f}', '-vf', 'fps=30,format=yuv420p', '-af', 'apad', '-c:v', 'h264_nvenc', '-cq', '20',
        '-c:a', 'aac', '-ar', '48000', '-ac', '2', hook)
    (W/f'lista_{n}.txt').write_text(f"file '{hook.name}'\nfile '{clip.name}'\n")
    run('-f', 'concat', '-safe', '0', '-i', W/f'lista_{n}.txt', '-c', 'copy', joined)
    segs = [Segment(0.0, hd - 0.2, '', s['gancho'])] + [Segment(max(0, x - a) + hd, min(y, z) - a + hd, '', tx) for x, y, tx in srt if y > a and x < z]
    sub = W/f'subs_{n}.srt'; sub.write_text(to_srt(segs), encoding='utf-8')
    style = 'FontName=DejaVu Sans,Bold=1,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=70,MarginL=20,MarginR=20'
    draws = ''
    for i, ln in enumerate(s['texto'].split('\n')):
        tf = W/f'texto_{n}_{i}.txt'; tf.write_text(ln)
        draws += (f"drawtext=fontfile={FONT}:textfile={tf}:fontsize=104:fontcolor=white:borderw=8:bordercolor=black:"
                  f"x=(w-text_w)/2:y={200 + i*125}:enable='lt(t,{hd:.2f})',")
    vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.12[bg];"
          "[b]crop=iw:ih*0.74:0:0,scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2-140[v1];"
          f"[v1]{draws.rstrip(',')}[v2];[v2]subtitles={sub}:force_style='{style}'[v]")
    out = O/f'short_{n}.mp4'
    run('-i', joined, '-filter_complex', vf, '-map', '[v]', '-map', '0:a', '-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '21', '-r', '30',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out)
    info.append(dict(n=n, escenas=f"{s['a']}-{s['b']}", inicio=round(a, 1), duracion=round(media.duration(out), 1))); print(info[-1], flush=True)
(O/'shorts.json').write_text(json.dumps(info, ensure_ascii=False, indent=1))
