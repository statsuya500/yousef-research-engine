"""Prueba de personajes de «A los 18 llamé a la puerta»: 4 planos medios y 2 primeros planos por personaje y ropa,
más paisajes de los lugares clave. Míralos antes de generar los planos de verdad."""
from pathlib import Path
from mangavid import images
from puerta_comun import *
C = Path('/mnt/c/videos/puerta/calibracion'); C.mkdir(parents=True, exist_ok=True)
jobs = []
CASOS = [("dario", "sudadera", "stairs"), ("dario", "botones", "lobby"), ("dario", "chofer", "penthouse"), ("isabel", None, "chapel"),
         ("isabel", "gala", "stairs"), ("fernando", None, "office"), ("ivan", None, "lobby"), ("valentina", None, "stairs"),
         ("ines", None, "orphanage"), ("toni", None, "shop"), ("paula", None, "lobby"), ("rafael", None, "penthouse"),
         ("guardia", None, "stairs"), ("dario_nino", None, "orphanage")]
for who, rp, loc in CASOS:
    tag = who + (f"-{rp}" if rp else "")
    for kind, act, n in (("plano", f"solo, cowboy shot, three-quarter view, calm expression, {LUGAR[loc]}", 4),
                         ("primer", "solo, close-up, portrait, face focus, calm expression, soft blurry background, bokeh, pastel colors", 2)):
        p = ", ".join((ficha(who, rp), act, STYLE))
        jobs += [images.Job(p, 500 + s, C/f"{tag}_{kind}_{s}.png", L, [], negative(who, ropa=rp), images.IP_SCALE) for s in range(n)]
for k in ("stairs", "stairs_sun", "orphanage", "lobby", "boardroom", "ballroom"):
    jobs += [images.Job(", ".join((ESCENARIO[k], STYLE)), 600 + s, C/f"escenario-{k}_{s}.png", L, [], negative("escenario"), images.IP_SCALE) for s in range(3)]
images.generate(jobs, COMMON, images.DEFAULT_MODEL)
