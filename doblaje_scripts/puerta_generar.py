"""Genera los planos de «A los 18 llamé a la puerta» según puerta_plan. Reanudable."""
import json
from pathlib import Path
from mangavid import images
from puerta_comun import estilo, fondo_cerca, LUGAR, ESCENARIO, L, V, ficha, negative
from puerta_plan import plan, pools, EXPR
H = Path('/mnt/c/videos/puerta'); P = H/'planos'; P.mkdir(exist_ok=True)
FOOD = ("food", "plate", "cup", "glass")
ALLOW = {"dining": FOOD, "cafe": ("cup", "mug", "food", "plate"), "penthouse": ("cup",), "ballroom": ("glass",), "stairs": ("glass", "bag"),
         "office": ("paper", "document", "laptop", "phone"), "boardroom": ("paper", "document", "laptop"), "shop": ("phone", "laptop"),
         "study": ("paper", "document"), "hotel_office": ("paper", "document"), "orphanage_office": ("paper", "document", "book"),
         "library": ("book", "paper"), "garage": ("car",), "workshop": ("car",), "street": ("car", "phone", "bag"), "lobby": ("bag",)}
def pid(p): return "_".join(str(x) for x in p if x is not None)
slots = plan(); gen, use = pools(slots)
first = {}
for n, seq in slots.items():
    for sl in seq:
        for p in ([sl[1], sl[2]] if sl[0] == "doble" else [sl]): first.setdefault(p, n)
OLD = json.loads((P/'configuracion_v1.json').read_text()) if (P/'configuracion_v1.json').exists() else {}
used = {s for c in OLD.values() for s in c['semillas']}
next_seed = max(used, default=80000) + 100
jobs, cfg = [], {}
for i, p in enumerate(sorted(gen, key=lambda p: first[p])):
    kind, who, rp, loc, mood = p; name = pid(p)
    if name in OLD and len(OLD[name]['semillas']) >= gen[p]: seeds = OLD[name]['semillas'][:gen[p]]   # reutiliza lo ya generado
    else:
        prev = OLD[name]['semillas'] if name in OLD else []
        extra = list(range(next_seed, next_seed + gen[p] - len(prev))); next_seed += len(extra) + 5
        seeds = prev + extra
    if False: pass
    elif kind == "scen":
        prompt, neg, size = ", ".join((ESCENARIO[loc], estilo(loc))), negative("escenario", ALLOW.get(loc, ()), loc=loc), L
    elif kind == "cow":
        prompt = ", ".join((ficha(who, rp), f"solo, cowboy shot, three-quarter view, {EXPR[mood]}, {LUGAR[loc]}", estilo(loc))); neg = negative(who, ALLOW.get(loc, ()), ropa=rp, loc=loc); size = L
    elif kind == "close":
        prompt = ", ".join((ficha(who, rp), f"solo, close-up, portrait, face focus, {EXPR[mood]}, {fondo_cerca(loc)}", estilo(loc))); neg = negative(who, ropa=rp, loc=loc); size = L
    else:
        face = "facing right" if first[p] and True else "facing left"
        prompt = ", ".join((ficha(who, rp), f"solo, cowboy shot, standing, side profile, from side, looking at someone off-screen, calm expression, {LUGAR[loc]}", estilo(loc)))
        neg = negative(who, ALLOW.get(loc, ()), side=True, ropa=rp, loc=loc); size = V
    cfg[name] = dict(clave=list(p), usos=use[p], primera_escena=first[p], semillas=list(seeds), prompt=prompt, negative=neg, tamaño=list(size))
    jobs += [images.Job(prompt, s, P/f"{name}_{s}.png", size, [], neg, images.IP_SCALE) for s in seeds]
(P/'configuracion.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
(H/'plan.json').write_text(json.dumps({str(n): [[list(x) for x in sl[1:]] if sl[0] == "doble" else list(sl) for sl in seq] for n, seq in slots.items()}, ensure_ascii=False))
print(len(jobs), 'planos en', len(cfg), 'grupos', flush=True)
images.generate(jobs, negative("dario"), images.DEFAULT_MODEL)
