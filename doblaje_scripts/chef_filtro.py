"""Filtro de «El Sistema del Chef Divino». Incremental: solo procesa planos que no están en filtro.json."""
import json
from pathlib import Path
from PIL import Image
from imgutils.detect import detect_faces, detect_heads
from imgutils.tagging import get_wd14_tags
from chequeos import face_side
H = Path('/mnt/c/videos/chef_divino'); P = H/'planos'; cfg = json.loads((P/'configuracion.json').read_text())
FJ = P/'filtro.json'; res = json.loads(FJ.read_text()) if FJ.exists() else {}
BAD = ['mug', 'paper', 'holding_paper', 'bag', 'hat', 'beret', 'headwear', 'white_headwear', 'chef_hat',
       'hair_ribbon', 'hair_bow', 'hair_ornament', 'multiple_boys', 'multiple_girls', '2boys', '2girls', 'weapon', 'gun', 'cigarette']
def g(t, *ks): return max(t.get(k, 0) for k in ks)
def rules(who, rp, close, t):
    w = []
    if who == 'rosa':
        if g(t, 'grey_hair', 'white_hair') < 0.6: w.append('pelo')
        if g(t, 'old_woman', 'old', 'mature_female') < 0.4: w.append('no parece anciana')
        if t.get('teeth', 0) >= 0.4 or (t.get('open_mouth', 0) >= 0.5 and t.get('smile', 0) >= 0.5): w.append('sonrisa grande')
    return w
n_new = 0
for name, c in cfg.items():
    kind, who, rp, loc, mood = c['clave']; land = tuple(c['tamaño']) == (1344, 768)
    for s in c['semillas']:
        stem = f'{name}_{s}'; p = P/f'{stem}.png'
        if stem in res or not p.exists(): continue
        im = Image.open(p).convert('RGB'); h = im.height; t = get_wd14_tags(im, general_threshold=0.2)[1]
        faces = [f for f in detect_faces(im) if f[2] > 0.4]; why = []; info = {}
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
        res[stem] = dict(ok=not why, motivos=why, **info); n_new += 1
FJ.write_text(json.dumps(res, ensure_ascii=False))
print(f'{n_new} nuevos; total {len(res)}; pasan {sum(v["ok"] for v in res.values())}')
