"""Prueba de ovejas con Animagine: (A) solo animal en primer plano, (B) rebaño en paisaje, (C) persona con un cordero en brazos,
(D) persona de pie con ovejas detrás desenfocadas."""
from pathlib import Path
from mangavid import images
from pastor_comun import STYLE, FICHA, ROPA, COMMON, L
O = Path('/mnt/c/videos/pastor_oro/prueba_animales'); O.mkdir(parents=True, exist_ok=True)
NEG = COMMON + ", bad anatomy, extra legs, deformed animal, fused animals, extra heads, human face on animal, text"
P = {
 "A_cordero_solo": "no humans, animal focus, close-up, a fluffy white lamb standing in green grass, cute, soft wool, black nose, mountain meadow, soft diffused daylight, pastel colors, bokeh",
 "A_oveja_solo": "no humans, animal focus, a white sheep with fluffy wool grazing on a green meadow, snowy mountains in the distance, soft diffused daylight, pastel colors",
 "B_rebano": "no humans, scenery, a flock of white sheep grazing on a green mountain valley, wide shot, snowy peaks, soft diffused daylight, pastel colors",
 "C_brazos": FICHA["daniel"] + ", " + ROPA["daniel"]["pastor"] + ", solo, cowboy shot, holding a small white lamb in his arms, gentle smile, mountain meadow, soft diffused daylight, pastel colors",
 "D_detras": FICHA["lucia"] + ", solo, cowboy shot, three-quarter view, gentle smile, standing on a meadow, white sheep grazing far in the background, blurry background, soft diffused daylight, pastel colors",
}
jobs = [images.Job(", ".join((p, STYLE)), 900 + s, O/f"{k}_{s}.png", L, [], NEG.replace("multiple boys, ", ""), images.IP_SCALE) for k, p in P.items() for s in range(4)]
images.generate(jobs, NEG, images.DEFAULT_MODEL)
