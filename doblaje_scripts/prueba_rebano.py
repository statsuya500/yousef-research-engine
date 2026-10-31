from pathlib import Path
from mangavid import images
from pastor_comun import STYLE, FICHA, ROPA, COMMON, L
O = Path('/mnt/c/videos/pastor_oro/prueba_animales')
NEG = COMMON + ", bad anatomy, extra legs, deformed animal, extra heads, human face on animal, text, snow, snowy ground"
P = {
 "E_rebano_cerca": "no humans, animal focus, many sheep, a flock of fluffy white sheep in the foreground, sheep grazing together on a green meadow, mountains in the background, soft diffused daylight, pastel colors",
 "F_rebano_valla": "no humans, animal focus, several white sheep behind a wooden fence, green grass, old stone farmhouse in the background, soft diffused daylight, pastel colors",
 "G_persona_rebano": FICHA["daniel"] + ", " + ROPA["daniel"]["pastor"] + ", solo, cowboy shot, standing among white sheep, sheep around him, holding a wooden shepherd staff, green meadow, soft diffused daylight, pastel colors",
}
jobs = [images.Job(", ".join((p, STYLE)), 950 + s, O/f"{k}_{s}.png", L, [], NEG, images.IP_SCALE) for k, p in P.items() for s in range(4)]
images.generate(jobs, NEG, images.DEFAULT_MODEL)
