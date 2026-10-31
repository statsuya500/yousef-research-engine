"""Plan de imágenes de «A los 18 llamé a la puerta»: una imagen cada ~5 s. Basado en hijos_plan.
Diferencias: escenas sin personajes (paisaje o público) solo llevan planos de escenario, y la ropa de Darío
cambia por fases de la historia (sudadera, botones, chófer, traje) y en el taller (mono)."""
import json, math, re
from collections import Counter
from pathlib import Path
from puerta_comun import NOCHE
H = Path('/mnt/c/videos/puerta')
EXPR = {"neutral": "calm expression", "happy": "gentle smile", "sad": "sad expression, looking down", "crying": "crying, tears",
        "angry": "angry, frowning", "shocked": "surprised, wide eyes", "smug": "smug smirk, arrogant", "cold": "cold expression, serious",
        "determined": "determined expression, serious"}
NOMBRES = {'dario': r'\bDarío\b', 'isabel': r'\bIsabel\b|\btu madre\b', 'fernando': r'\bFernando\b', 'ivan': r'\bIván\b',
           'valentina': r'\bValentina\b', 'ines': r'\bsor Inés\b', 'toni': r'\bToni\b', 'paula': r'\bPaula\b',
           'rafael': r'\bRafael\b|\bDon Rafael\b|\btu abuelo\b'}
FACTOR = {"cow": 1.6, "close": 1.2, "scen": 1.2, "side": 2.0}
BOTONES, CHOFER, TRAJE = 69, 178, 339   # primeras escenas de cada fase de Darío
HOTEL = {'lobby', 'laundry', 'lockers', 'garage', 'hotel_office', 'elevator', 'rooftop', 'penthouse'}
def ropa(who, n, loc):
    if who == 'dario':
        if loc == 'workshop': return 'mono'
        if n >= TRAJE: return 'traje'
        if n >= CHOFER: return 'chofer' if loc not in ('flat', 'shop', 'cafe') else 'sudadera'
        if n >= BOTONES and loc in HOTEL: return 'botones'
        return 'sudadera'
    if who == 'isabel': return {'stairs': 'gala', 'ballroom': 'gala', 'boardroom': 'blanco'}.get(loc)
    if who == 'fernando' and loc in ('stairs', 'ballroom'): return 'esmoquin'
    if who == 'ivan': return {'stairs': 'esmoquin', 'study': 'sudadera'}.get(loc)
    if who == 'valentina' and loc in ('stairs', 'stairs_sun', 'ballroom', 'boardroom'): return 'vestido'
    if who == 'paula' and loc in ('cafe', 'rooftop', 'shop', 'workshop'): return 'casual'
    if who == 'rafael' and loc in ('boardroom', 'stairs_sun', 'cemetery', 'ballroom'): return 'traje'
    return None
def scenes():
    t = (H/'historia.txt').read_text(); dur = json.loads((H/'trabajo'/'duraciones.json').read_text())
    for b in re.split(r'(?m)^(?=\[\d{3}\] )', t):
        m = re.match(r'\[(\d{3})\] (.*)\n', b)
        if not m: continue
        n = int(m.group(1)); toks = [x.strip() for x in m.group(2).split(',')]
        chars = [x[1:] for x in toks if x.startswith('@')]; rest = [x for x in toks if not x.startswith('@')]
        text = b[m.end():]
        if chars:   # personaje mencionado: puede salir en plano propio (no en viñeta)
            for who, pat in NOMBRES.items():
                if who not in chars and re.search(pat, text): chars.append(who)
        yield n, chars[:2], len([x for x in toks if x.startswith('@')]), rest[0], rest[1], dur[str(n)]
def plan():
    slots, prev = {}, None
    for n, chars, ndecl, loc, mood, d in scenes():
        k = max(1, round(d / 5))
        if not chars:   # paisaje o público: solo planos de escenario
            slots[n] = [("scen", None, None, loc, None)] * k; prev = loc; continue
        f = chars[0]; s = chars[1] if len(chars) > 1 else None
        P = lambda kind, who: (kind, who, ropa(who, n, loc), loc if kind in ("cow", "side") or (kind == "close" and loc in NOCHE) else None, "neutral" if kind == "side" else mood)
        seq = []
        if loc != prev: seq.append(("scen", None, None, loc, None))
        if s and ndecl >= 2 and k >= 3 and len(seq) < k:   # viñeta doble solo si los dos están en la línea de escena
            seq.append(("doble", P("side", f), P("side", s)))
        cyc = [P("cow", f), P("close", f)] + ([P("close", s), P("cow", s)] if s else [])
        i = 0
        while len(seq) < k:
            seq.append(cyc[i % len(cyc)]); i += 1
            if i % 4 == 0 and len(seq) < k: seq.append(("scen", None, None, loc, None))
        slots[n] = seq[:k]; prev = loc
    return slots
def pools(slots):
    use = Counter()
    for seq in slots.values():
        for sl in seq:
            if sl[0] == "doble": use[sl[1]] += 1; use[sl[2]] += 1
            else: use[sl] += 1
    return {p: math.ceil(u * FACTOR[p[0]]) + (1 if u < 3 else 0) for p, u in use.items()}, use
if __name__ == "__main__":
    sl = plan(); gen, use = pools(sl)
    print('huecos', sum(len(v) for v in sl.values()), 'grupos', len(gen), 'semillas', sum(gen.values()))
