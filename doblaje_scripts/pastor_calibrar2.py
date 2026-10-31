from pathlib import Path
from mangavid import images
from pastor_comun import *
C = Path('/mnt/c/videos/pastor_oro/calibracion'); jobs = []
for who in ("pilar", "nico", "cura", "periodista", "abogado", "dani"):
    for kind, act, n in (("plano", f"solo, cowboy shot, three-quarter view, calm expression, {LUGAR['village']}", 3),
                         ("primer", "solo, close-up, portrait, face focus, calm expression, soft blurry background, bokeh, pastel colors", 2)):
        p = ", ".join((ficha(who), act, STYLE))
        jobs += [images.Job(p, 500 + s, C/f"{who}_{kind}_{s}.png", L, [], negative(who), images.IP_SCALE) for s in range(n)]
images.generate(jobs, COMMON, images.DEFAULT_MODEL)
