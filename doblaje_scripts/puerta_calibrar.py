"""Prueba de personajes de «A los 18 llamé a la puerta»: 4 planos medios y 2 primeros planos por personaje y ropa,
más paisajes de los lugares clave. Míralos antes de generar los planos de verdad."""
from pathlib import Path
from mangavid import images
from puerta_comun import *
import sys
SOLO = sys.argv[1:]  # p. ej. «python puerta_calibrar.py dario-sudadera» repite solo esos casos
C = Path('/mnt/c/videos/puerta/calibracion'); C.mkdir(parents=True, exist_ok=True)
jobs = []
CASOS = [("dario", "sudadera", "stairs"), ("dario", "botones", "lobby"), ("dario", "chofer", "penthouse"), ("isabel", None, "chapel"),
         ("isabel", "gala", "stairs"), ("fernando", None, "office"), ("ivan", None, "lobby"), ("valentina", None, "stairs"),
         ("ines", None, "orphanage"), ("toni", None, "shop"), ("paula", None, "lobby"), ("rafael", None, "penthouse"),
         ("guardia", None, "stairs"), ("dario_nino", None, "orphanage"),
         # el resto de conjuntos, para que cada uno salga siempre igual
         ("dario", "mono", "workshop"), ("dario", "traje", "boardroom"), ("isabel", "blanco", "boardroom"),
         ("fernando", "esmoquin", "ballroom"), ("ivan", "esmoquin", "stairs"), ("ivan", "sudadera", "study"),
         ("valentina", "vestido", "ballroom"), ("paula", "casual", "cafe"), ("rafael", "traje", "boardroom"),
         ("director", None, "hotel_office"), ("policia", None, "lobby")]
for who, rp, loc in CASOS:
    tag = who + (f"-{rp}" if rp else "")
    if SOLO and tag not in SOLO: continue
    for kind, act, n, lo in (("plano", f"solo, cowboy shot, three-quarter view, calm expression, {LUGAR[loc]}", 4, loc),
                             ("primer", f"solo, close-up, portrait, face focus, calm expression, {fondo_cerca(loc if loc in NOCHE else None)}", 2, loc if loc in NOCHE else None)):
        p = ", ".join((ficha(who, rp), act, estilo(lo)))
        jobs += [images.Job(p, 500 + s, C/f"{tag}_{kind}_{s}.png", L, [], negative(who, ropa=rp, loc=lo), images.IP_SCALE) for s in range(n)]
for k in [] if SOLO else ("stairs", "stairs_sun", "orphanage", "lobby", "boardroom", "ballroom"):
    jobs += [images.Job(", ".join((ESCENARIO[k], estilo(k))), 600 + s, C/f"escenario-{k}_{s}.png", L, [], negative("escenario", loc=k), images.IP_SCALE) for s in range(3)]
images.generate(jobs, COMMON, images.DEFAULT_MODEL)
