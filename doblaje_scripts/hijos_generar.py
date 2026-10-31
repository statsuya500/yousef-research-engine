"""Genera los planos de «Mis hijos me eligieron» según hijos_plan. Reanudable."""
import json
from pathlib import Path
from mangavid import images
from hijos_comun import STYLE, LUGAR, ESCENARIO, L, V, ficha, negative
from hijos_plan import plan, pools, EXPR
H = Path('/mnt/c/videos/hijos_eligieron'); P = H/'planos'; P.mkdir(exist_ok=True)
FOOD = ("food", "plate", "cup", "glass")
ALLOW = {"kitchen": FOOD + ("knife",), "restaurant": FOOD, "hotel": FOOD, "kidsroom": ("toy", "book"), "school": ("backpack", "paper", "book"),
         "office": ("laptop", "paper", "document"), "court": ("paper", "document"), "home": ("cup", "phone"), "hospital": ("cup",)}
def pid(p): return "_".join(str(x) for x in p if x is not None)
slots = plan(); gen, use = pools(slots)
first = {}
for n, seq in slots.items():
    for sl in seq:
        for p in ([sl[1], sl[2]] if sl[0] == "doble" else [sl]): first.setdefault(p, n)
jobs, cfg = [], {}
for i, p in enumerate(sorted(gen, key=lambda p: first[p])):
    kind, who, rp, loc, mood = p; name = pid(p); seeds = range(60000 + i*20, 60000 + i*20 + gen[p])
    if kind == "scen":
        prompt, neg, size = ", ".join((ESCENARIO[loc], STYLE)), negative("escenario", ALLOW.get(loc, ())), L
    elif kind == "cow":
        prompt = ", ".join((ficha(who, rp), f"solo, cowboy shot, three-quarter view, {EXPR[mood]}, {LUGAR[loc]}", STYLE)); neg = negative(who, ALLOW.get(loc, ())); size = L
    elif kind == "close":
        prompt = ", ".join((ficha(who, rp), f"solo, close-up, portrait, face focus, {EXPR[mood]}, soft blurry background, bokeh, pastel colors", STYLE)); neg = negative(who); size = L
    else:
        face = "facing right" if first[p] and True else "facing left"
        prompt = ", ".join((ficha(who, rp), f"solo, cowboy shot, standing, side profile, from side, looking at someone off-screen, calm expression, {LUGAR[loc]}", STYLE))
        neg = negative(who, ALLOW.get(loc, ()), side=True); size = V
    cfg[name] = dict(clave=list(p), usos=use[p], primera_escena=first[p], semillas=list(seeds), prompt=prompt, negative=neg, tamaño=list(size))
    jobs += [images.Job(prompt, s, P/f"{name}_{s}.png", size, [], neg, images.IP_SCALE) for s in seeds]
(P/'configuracion.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
(H/'plan.json').write_text(json.dumps({str(n): [[list(x) for x in sl[1:]] if sl[0] == "doble" else list(sl) for sl in seq] for n, seq in slots.items()}, ensure_ascii=False))
print(len(jobs), 'planos en', len(cfg), 'grupos', flush=True)
images.generate(jobs, negative("irene"), images.DEFAULT_MODEL)
