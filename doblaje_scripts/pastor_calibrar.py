from pathlib import Path
from mangavid import images
from pastor_comun import *
C = Path('/mnt/c/videos/pastor_oro/calibracion'); C.mkdir(parents=True, exist_ok=True)
jobs = []
for who, rp in [("daniel", "pastor"), ("daniel", "ciudad"), ("lucia", None), ("lucia", "bata"), ("marcos", None), ("elena", None), ("ramiro", None)]:
    tag = who + (f"_{rp}" if rp else "")
    for kind, act, n in (("plano", f"solo, cowboy shot, three-quarter view, calm expression, {LUGAR['meadow']}", 4),
                         ("primer", "solo, close-up, portrait, face focus, calm expression, soft blurry background, bokeh, pastel colors", 2)):
        p = ", ".join((ficha(who, rp), act, STYLE))
        jobs += [images.Job(p, 500 + s, C/f"{tag}_{kind}_{s}.png", L, [], negative(who), images.IP_SCALE) for s in range(n)]
for k in ("meadow", "farm"):
    jobs += [images.Job(", ".join((ESCENARIO[k], STYLE)), 600 + s, C/f"escenario_{k}_{s}.png", L, [], negative("escenario", ("sheep", "animal")), images.IP_SCALE) for s in range(3)]
images.generate(jobs, COMMON, images.DEFAULT_MODEL)
