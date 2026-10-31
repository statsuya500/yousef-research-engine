from pathlib import Path
from mangavid import images
from hijos_comun import *
C = Path('/mnt/c/videos/hijos_eligieron/calibracion'); C.mkdir(parents=True, exist_ok=True)
jobs = []
N = {"irene": (4, 2), "javier": (4, 2), "sabrina": (4, 2), "carmen": (4, 2), "nerea": (7, 3), "pablo": (7, 3)}
for who, (np_, nc) in N.items():
    for kind, act, n in (("plano", f"solo, cowboy shot, three-quarter view, calm expression, {LUGAR['home']}", np_),
                         ("primer", "solo, close-up, portrait, face focus, calm expression, soft blurry background, bokeh, pastel colors", nc)):
        p = ", ".join((ficha(who), act, STYLE))
        jobs += [images.Job(p, 500 + s, C/f"{who}_{kind}_{s}.png", L, [], negative(who), images.IP_SCALE) for s in range(n)]
# Pablo en brazos de Irene (plano de conjunto): prueba de la técnica para niños pequeños
p = ", ".join(("1girl, 1boy, young woman holding a little boy in her arms, " + FICHA["irene"].replace("1girl, ", "") + ", the little boy has messy light brown hair and a yellow hoodie, 5 years old, hugging", LUGAR['home'], STYLE))
jobs += [images.Job(p, 700 + s, C/f"irene_pablo_brazos_{s}.png", L, [], COMMON.replace("multiple boys, 2boys, extra person, ", "") + ", nsfw", images.IP_SCALE) for s in range(4)]
images.generate(jobs, COMMON, images.DEFAULT_MODEL)
