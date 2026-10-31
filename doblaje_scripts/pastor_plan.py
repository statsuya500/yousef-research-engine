"""Plan de imágenes de «El pastor del valle de oro»: una imagen cada ~5 s."""
import json, math, re
from collections import Counter
from pathlib import Path
H = Path('/mnt/c/videos/pastor_oro')
EXPR = {"neutral": "calm expression", "happy": "gentle smile", "sad": "sad expression, looking down", "crying": "crying, tears",
        "angry": "angry, frowning", "shocked": "surprised, wide eyes", "smug": "smug smirk, arrogant", "cold": "cold expression, serious",
        "determined": "determined expression, serious"}
NOMBRES = {'daniel': r'\bDaniel\b', 'lucia': r'\bLucía\b', 'marcos': r'\bMarcos\b', 'elena': r'\bElena\b', 'ramiro': r'\bRamiro\b',
           'pilar': r'Pilar', 'nico': r'\bNico\b|\bnieto\b|\bniño\b', 'cura': r'\bcura\b', 'periodista': r'periodista', 'abogado': r'\babogad[oa]s?\b', 'dani': r'\bDani\b'}
FACTOR = {"cow": 1.6, "close": 1.2, "scen": 1.2, "side": 2.0, "rebano": 1.4, "cordero": 1.4}
def ropa(who, n, loc):
    if who == 'daniel': return 'ciudad' if loc in ('office', 'city') else 'pastor'
    if who == 'lucia' and loc == 'clinic': return 'bata'
    return None
def scenes():
    t = (H/'historia.txt').read_text(); dur = json.loads((H/'trabajo'/'duraciones.json').read_text())
    for b in re.split(r'(?m)^(?=\[\d{3}\] )', t):
        m = re.match(r'\[(\d{3})\] (.*)\n', b)
        if not m: continue
        n = int(m.group(1)); toks = [x.strip() for x in m.group(2).split(',')]
        chars = [x[1:] for x in toks if x.startswith('@')]; rest = [x for x in toks if not x.startswith('@')]
        text = b[m.end():]
        found = sorted(((m.start(), who) for who, pat in NOMBRES.items() if who not in chars
                        for m in [re.search(pat, text)] if m), key=lambda x: x[0])
        chars += [w for _, w in found]
        yield n, chars[:3], len([x for x in toks if x.startswith('@')]), rest[0], rest[1], dur[str(n)]
def plan():
    slots, prev = {}, None
    for n, chars, ndecl, loc, mood, d in scenes():
        k = max(1, round(d / 5)); f = chars[0]; s = chars[1] if len(chars) > 1 else None
        P = lambda kind, who: (kind, who, ropa(who, n, loc), loc if kind in ("cow", "side") else None, "neutral" if kind == "side" else mood)
        seq = []
        if loc != prev: seq.append(("scen", None, None, loc, None))
        if s and k >= 3 and len(seq) < k and 'daniel' in (f, s) and s in ('lucia', 'marcos', 'ramiro', 'elena') and loc not in ('city', 'office'):
            other = s if f == 'daniel' else f
            seq.append(('doble', P('side', 'daniel'), P('side', other)))
        third = chars[2] if len(chars) > 2 else None
        cyc = [P("cow", f), P("close", f)] + ([P("close", s), P("cow", s)] if s else []) + ([P("cow", third)] if third else [])
        if loc in ('meadow', 'farm', 'barn') and k >= 3 and len(seq) < k:   # ovejas: de cerca o con Daniel (el rebaño lejano no sale)
            seq.append(("rebano", "daniel", "pastor", loc, None) if n % 2 else ("cordero", None, None, loc, None))
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
