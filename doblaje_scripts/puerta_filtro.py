"""Filtro de «A los 18 llamé a la puerta». Incremental (solo procesa lo que no está en filtro.json)."""
import json, sys
from pathlib import Path
from PIL import Image
from imgutils.detect import detect_faces, detect_heads
from imgutils.tagging import get_wd14_tags
from chequeos import face_side
H = Path('/mnt/c/videos/puerta'); P = H/'planos'
BAD = ['mug', 'bag', 'hat', 'headwear', 'pagoda', 'hair_ornament', 'multiple_boys', 'multiple_girls', '2boys', '2girls', 'weapon', 'gun', 'cigarette']
MINOR_BAD = ['cleavage', 'nsfw', 'lingerie', 'swimsuit', 'bare_shoulders', 'midriff', 'makeup', 'lipstick']
def g(t, *ks): return max(t.get(k, 0) for k in ks)
def rules(who, rp, close, t):
    w = []
    if who in ('dario', 'dario_nino', 'isabel', 'valentina'):
        if t.get('brown_hair', 0) < 0.5: w.append('pelo')
        if g(t, 'blonde_hair', 'red_hair', 'pink_hair', 'purple_hair') >= 0.4: w.append('pelo de otro color')
    if who == 'dario' and not close:
        if rp in ('chofer', 'traje') and g(t, 'suit', 'formal', 'necktie', 'collared_shirt') < 0.3: w.append('sin traje')
        if rp == 'sudadera' and g(t, 'hoodie', 'hood') < 0.25: w.append('sin sudadera')
    elif who == 'fernando':
        if g(t, 'black_hair', 'grey_hair') < 0.5: w.append('pelo')
        if g(t, 'beard', 'facial_hair', 'glasses') >= 0.4: w.append('barba o gafas')
    elif who == 'ivan':
        if t.get('blonde_hair', 0) < 0.6: w.append('pelo')
    elif who == 'ines':
        if g(t, 'nun', 'veil', 'habit') < 0.4: w.append('sin hábito')
    elif who == 'toni':
        if g(t, 'red_hair', 'orange_hair') < 0.5: w.append('pelo')
    elif who == 'paula':
        if t.get('black_hair', 0) < 0.5: w.append('pelo')
        if g(t, 'long_hair', 'very_long_hair') >= 0.5: w.append('pelo largo')
    elif who in ('rafael', 'policia'):
        if g(t, 'white_hair', 'grey_hair') < 0.5: w.append('pelo')
    elif who == 'guardia':
        if t.get('bald', 0) < 0.3: w.append('no calvo')
    if who == 'dario_nino':
        if g(t, 'male_child', 'child') < 0.3: w.append('no parece niño')
        bad = [k for k in MINOR_BAD if t.get(k, 0) >= 0.3]
        if bad: w.append('inadecuado para menor: ' + ' '.join(bad))
    return w
def check(im, kind, who, rp, land):
    h = im.height; t = get_wd14_tags(im, general_threshold=0.2)[1]
    faces = [f for f in detect_faces(im) if f[2] > 0.4]; why = []; info = {}
    if False:
        ppl = [k for k in ('1girl', '1boy', 'text') if t.get(k, 0) >= 0.35]
        return (['sin ovejas'] if t.get('sheep', 0) < 0.4 else []) + ([f'personas {ppl}'] if ppl else []), info
    if kind == 'scen':
        ppl = [k for k in ('1girl', '1boy', 'solo', 'text', 'sign', 'english_text') if t.get(k, 0) >= 0.35]
        return ([f'{len(faces)} rostros'] if faces else []) + ([f'personas o texto {ppl}'] if ppl else []), info
    close = kind == 'close'
    if len(faces) > 1 or (len(faces) == 0 and not close): why.append(f'{len(faces)} rostros')   # primeros planos muy cerca: el detector no ve la cara
    elif land and not close and (faces[0][0][1] < 8 or faces[0][0][3] > h - 8): why.append('cara cortada')
    elif not land:
        hs = detect_heads(im)
        if not hs or min(b[0][1] for b in hs) < 0.02*h: why.append('cabeza cortada')
    bad = [f'{k}={t[k]:.2f}' for k in BAD if t.get(k, 0) >= 0.35 ]
    if bad: why.append('objetos: ' + ' '.join(bad))
    why += rules(who, rp, close, t)
    if len(faces) == 1 and not close and detect_heads(im): info['lado_cara'] = round(face_side(im), 3)
    return why, info
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'calibrar':
        for p in sorted((H/'calibracion').glob('*.png')):
            parts = p.stem.split('_')
            if len(parts) != 3: continue
            who, rp = (parts[0].split('-') + [None])[:2]
            why, _ = check(Image.open(p).convert('RGB'), 'close' if parts[1] == 'primer' else 'cow', who, rp, True)
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
