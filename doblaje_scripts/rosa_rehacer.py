"""Rehace las expresiones de Rosa: «shocked» -> «moved» y «happy» -> «gentle». Nuevos grupos de planos; plan.json se actualiza
(el original queda en plan_antes_rosa.json). El vídeo se vuelve a montar en un archivo NUEVO."""
import json, shutil
from pathlib import Path
from mangavid import images
from chef_comun import STYLE, LUGAR, L, V, ficha, negative
H = Path('/mnt/c/videos/chef_divino'); P = H/'planos'
EXPR = {"moved": "moved, teary eyes, gentle surprised expression, hand on own chest, closed mouth",
        "gentle": "gentle closed-mouth smile, kind warm eyes, calm"}
NEG_EXTRA = ", open mouth, teeth, grin, wide eyes, frown, angry, scary, exaggerated wrinkles, young, smooth skin"
MAP = {"shocked": "moved", "happy": "gentle"}
pp = H/'plan.json'; plan = json.loads(pp.read_text())
if not (H/'plan_antes_rosa.json').exists(): shutil.copy2(pp, H/'plan_antes_rosa.json')
FOOD = ("food", "plate", "bowl", "pan", "knife", "cup", "glass")
ALLOW = {"kitchen": FOOD, "stall": FOOD, "restaurant": FOOD, "tvstudio": FOOD, "market": FOOD, "hospital": ("bowl", "food", "cup"),
         "street": ("buildings", "cup"), "apartment": ("phone", "cup")}
def fix(sl):
    if isinstance(sl[0], list): return [fix(x) for x in sl]
    if sl[1] == 'rosa' and sl[4] in MAP: return [sl[0], sl[1], sl[2], sl[3], MAP[sl[4]]]
    return sl
plan = {n: [fix(s) for s in seq] for n, seq in plan.items()}
pp.write_text(json.dumps(plan, ensure_ascii=False))
use = {}
for seq in plan.values():
    for sl in seq:
        for x in (sl if isinstance(sl[0], list) else [sl]):
            if x[1] == 'rosa' and x[4] in EXPR: use[tuple(x)] = use.get(tuple(x), 0) + 1
cfg = json.loads((P/'configuracion.json').read_text()); jobs = []
for i, (key, u) in enumerate(sorted(use.items())):
    kind, who, rp, loc, mood = key; name = "_".join(str(x) for x in key if x is not None)
    seeds = range(40000 + i*20, 40000 + i*20 + u*2 + 2)
    if kind == 'cow': act, size, neg = f"solo, cowboy shot, three-quarter view, {EXPR[mood]}, {LUGAR[loc]}", L, negative(who, ALLOW.get(loc, ()))
    elif kind == 'close': act, size, neg = f"solo, close-up, portrait, face focus, {EXPR[mood]}, soft blurry background, bokeh, pastel colors", L, negative(who)
    else: act, size, neg = f"solo, cowboy shot, standing, side profile, from side, facing left, looking at someone off-screen, {EXPR[mood]}, {LUGAR[loc]}", V, negative(who, ALLOW.get(loc, ()), side=True)
    prompt = ", ".join((ficha(who), act, STYLE)); neg += NEG_EXTRA
    cfg[name] = dict(clave=list(key), usos=u, primera_escena=0, semillas=list(seeds), prompt=prompt, negative=neg, tamaño=list(size))
    jobs += [images.Job(prompt, s, P/f"{name}_{s}.png", size, [], neg, images.IP_SCALE) for s in seeds]
(P/'configuracion.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
print(len(use), 'grupos,', len(jobs), 'planos', flush=True)
images.generate(jobs, negative('rosa'), images.DEFAULT_MODEL)
