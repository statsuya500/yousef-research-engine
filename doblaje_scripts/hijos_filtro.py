"""Filtro de «Mis hijos me eligieron». Incremental (solo procesa lo que no está en filtro.json)."""
import json, sys
from pathlib import Path
from PIL import Image
from imgutils.detect import detect_faces, detect_heads
from imgutils.tagging import get_wd14_tags
from chequeos import face_side
H = Path('/mnt/c/videos/hijos_eligieron'); P = H/'planos'
BAD = ['mug', 'bag', 'hat', 'headwear', 'hair_ornament', 'multiple_boys', 'multiple_girls', '2boys', '2girls', 'weapon', 'gun', 'cigarette']
MINOR_BAD = ['cleavage', 'nsfw', 'lingerie', 'swimsuit', 'bare_shoulders', 'midriff', 'makeup', 'lipstick']
def g(t, *ks): return max(t.get(k, 0) for k in ks)
def rules(who, rp, close, t):
    w = []
    if who == 'irene':
        if t.get('brown_hair', 0) < 0.6: w.append('pelo')
        if g(t, 'short_hair') >= 0.6: w.append('pelo corto')
        if t.get('brown_eyes', 0) < 0.4: w.append('ojos')
    elif who == 'javier':
        if t.get('black_hair', 0) < 0.6: w.append('pelo')
        if t.get('glasses', 0) < 0.5: w.append('sin gafas')
    elif who == 'sabrina':
        if t.get('red_hair', 0) < 0.6: w.append('pelo')
        if t.get('green_eyes', 0) < 0.4: w.append('ojos')
    elif who == 'nerea':
        if t.get('black_hair', 0) < 0.6: w.append('pelo')
        if t.get('long_hair', 0) >= 0.6 and t.get('short_hair', 0) < 0.3: w.append('pelo largo')
        if t.get('grey_eyes', 0) < 0.3: w.append('ojos')
        if not close and g(t, 'school_uniform', 'blazer', 'jacket') < 0.3: w.append('sin uniforme')
    elif who == 'pablo':
        if g(t, 'brown_hair', 'light_brown_hair', 'blonde_hair') < 0.6: w.append('pelo')
        if g(t, 'male_child', 'child') < 0.3 and t.get('1boy', 0) < 0.5: w.append('no parece niño')
        if not close and g(t, 'yellow_hoodie', 'hoodie') < 0.4: w.append('sin sudadera amarilla')
    elif who == 'carmen':
        if g(t, 'grey_hair', 'white_hair') < 0.6: w.append('pelo')
        if g(t, 'old_woman', 'old', 'mature_female') < 0.4: w.append('no parece mayor')
    elif who == 'marco':
        if t.get('blonde_hair', 0) < 0.5: w.append('pelo')
    if who in ('nerea', 'pablo'):
        bad = [k for k in MINOR_BAD if t.get(k, 0) >= 0.3]
        if bad: w.append('inadecuado para menor: ' + ' '.join(bad))
    return w
def check(im, kind, who, rp, land):
    h = im.height; t = get_wd14_tags(im, general_threshold=0.2)[1]
    faces = [f for f in detect_faces(im) if f[2] > 0.4]; why = []; info = {}
    if kind == 'scen':
        ppl = [k for k in ('1girl', '1boy', 'solo', 'text', 'sign', 'english_text') if t.get(k, 0) >= 0.35]
        return ([f'{len(faces)} rostros'] if faces else []) + ([f'personas o texto {ppl}'] if ppl else []), info
    close = kind == 'close'
    if len(faces) != 1: why.append(f'{len(faces)} rostros')
    elif land and not close and (faces[0][0][1] < 8 or faces[0][0][3] > h - 8): why.append('cara cortada')
    elif not land:
        hs = detect_heads(im)
        if not hs or min(b[0][1] for b in hs) < 0.02*h: why.append('cabeza cortada')
    bad = [f'{k}={t[k]:.2f}' for k in BAD if t.get(k, 0) >= 0.35]
    if bad: why.append('objetos: ' + ' '.join(bad))
    why += rules(who, rp, close, t)
    if len(faces) == 1 and not close and detect_heads(im): info['lado_cara'] = round(face_side(im), 3)
    return why, info
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'calibrar':
        for p in sorted((H/'calibracion').glob('*.png')):
            parts = p.stem.split('_')
            if len(parts) != 3: continue
            why, _ = check(Image.open(p).convert('RGB'), 'close' if parts[1] == 'primer' else 'cow', parts[0], None, True)
            if why: print(p.stem, why)
        print('fin calibración'); sys.exit()
    cfg = json.loads((P/'configuracion.json').read_text())
    FJ = P/'filtro.json'; res = json.loads(FJ.read_text()) if FJ.exists() else {}
    n_new = 0
    for name, c in cfg.items():
        kind, who, rp, loc, mood = c['clave']; land = tuple(c['tamaño']) == (1344, 768)
        for s in c['semillas']:
            stem = f'{name}_{s}'; p = P/f'{stem}.png'
            if stem in res or not p.exists(): continue
            why, info = check(Image.open(p).convert('RGB'), kind, who, rp, land)
            res[stem] = dict(ok=not why, motivos=why, **info); n_new += 1
            if n_new % 100 == 0: FJ.write_text(json.dumps(res, ensure_ascii=False)); print(n_new, flush=True)
    FJ.write_text(json.dumps(res, ensure_ascii=False))
    print(f'{n_new} nuevos; total {len(res)}; pasan {sum(v["ok"] for v in res.values())}')
