"""Genera la voz de cada escena (la misma que usará el montaje) y guarda trabajo/duraciones.json.
Hay que ejecutarlo antes de puerta_plan / puerta_generar. Reanudable: la voz se guarda en caché."""
import json
from pathlib import Path
from dubber import tts, media
from dubber.segments import Segment
from mangavid import storyboard, render
H = Path('/mnt/c/videos/puerta'); W = H/'trabajo'; W.mkdir(parents=True, exist_ok=True)
board = storyboard.load(H/'historia.txt')
voices = tts.synthesize([Segment(0.0, 0.0, '', s.narration) for s in board.scenes], W/'voz', tts.DEFAULT_VOICE, '+0%')
dur = {str(s.number): round(media.duration(v) + render.PAUSE, 2) for s, v in zip(board.scenes, voices)}
(W/'duraciones.json').write_text(json.dumps(dur))
print(f"{len(dur)} escenas, {sum(dur.values())/60:.1f} min")
