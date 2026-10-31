"""Monta las imágenes de «El Sistema del Chef Divino» desde plan.json + filtro.json (+ excluir.json, aceptar_a_ojo.json).
Sin repetir; si un grupo se agota, reutiliza una imagen usada a 20 escenas o más; si no, usa un sustituto y lo anota.
Viñetas: Hugo a la izquierda mirando a la derecha; el otro a la derecha mirando a la izquierda (volteo por lado_cara)."""
import json, hashlib, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw
from fondo import correct
from chequeos import person_mask
from sistema_ventana import ventana
H = Path('/mnt/c/videos/chef_divino'); P = H/'planos'; O = Path(sys.argv[1]) if len(sys.argv) > 1 else H/'escenas'
F = json.loads((P/'filtro.json').read_text()); plan = json.loads((H/'plan.json').read_text())
EXC = set(json.loads((H/'excluir.json').read_text())) if (H/'excluir.json').exists() else set()
ACE = json.loads((H/'aceptar_a_ojo.json').read_text()) if (H/'aceptar_a_ojo.json').exists() else {}
for k in ACE: F[k]['ok'] = True
def pid(p): return "_".join(str(x) for x in p if x is not None)
ok_by = {}
for k, v in sorted(F.items()):
    if v['ok'] and k not in EXC: ok_by.setdefault(k.rsplit('_', 1)[0], []).append(k)
last_use, notes = {}, []
def take(p, n, want=None):
    cands = ok_by.get(pid(p), []); free = [k for k in cands if k not in last_use]
    if want:
        good = [k for k in free if F[k].get('lado_cara') is not None and (F[k]['lado_cara'] > 0) == (want == 'der') and abs(F[k]['lado_cara']) >= 0.06]
        free = good or [k for k in free if F[k].get('lado_cara') is not None]
    if free: k = free[0]
    else:
        old = [k for k in cands if n - last_use.get(k, -999) >= 20]
        if not old: return None
        k = old[0]; notes.append(f'escena {n}: reutilizada {k}')
    last_use[k] = n
    flip = bool(want) and F[k].get('lado_cara') is not None and (F[k]['lado_cara'] > 0) != (want == 'der')
    return k, flip
def half(k, flip):
    im = Image.open(P/f'{k}.png').convert('RGB'); im = ImageOps.mirror(im) if flip else im
    return im.resize((672, 864), Image.LANCZOS).crop((0, 0, 672, 768))
if O.exists(): shutil.rmtree(O)
O.mkdir(parents=True); reg = {}
for n_s, seq in plan.items():
    n = int(n_s)
    for i, sl in enumerate(seq, 1):
        out = O/f'escena_{n:03d}_{i}.png'
        if not isinstance(sl[0], list) and sl[0] == 'sys':
            r = take(('scen', None, None, sl[3], None), n) or take(('scen', None, None, 'stall', None), n)
            ventana(P/f'{r[0]}.png', [x.strip() + ('' if x.strip().endswith(('.', '!', '?')) else '.') for x in sl[1].split('. ') if x.strip()], out)
            reg[out.name] = dict(tipo='ventana del sistema', base=r[0], texto=sl[1]); continue
        if isinstance(sl[0], list):
            a, b = take(tuple(sl[0]), n, 'der'), take(tuple(sl[1]), n, 'izq')
            if a and b:
                L, R = half(*a), half(*b); mL, mR = person_mask(L), person_mask(R)
                tgt = (np.asarray(L).astype(float)[~mL].mean(0) + np.asarray(R).astype(float)[~mR].mean(0))/2
                v = Image.new('RGB', (1344, 768), 'white'); v.paste(correct(L, mL, tgt), (0, 0)); v.paste(correct(R, mR, tgt), (672, 0))
                ImageDraw.Draw(v).rectangle((669, 0, 675, 768), fill='white'); v.save(out)
                reg[out.name] = dict(tipo='viñeta', izquierda=a[0], izq_volteado=a[1], derecha=b[0], der_volteado=b[1]); continue
            sl = ['close', sl[1][1], sl[1][2], None, 'neutral']; notes.append(f'escena {n}: viñeta sin planos, sustituida por primer plano')
        r = take(tuple(sl), n)
        if not r:
            subs = [('close', sl[1], sl[2], None, sl[4])] if sl[0] not in ('scen', 'plato') else []
            loc = sl[3] or next((x[3] for x in seq if not isinstance(x[0], list) and x[3]), None)
            subs.append(('scen', None, None, loc, None))
            for s2 in subs:
                r = take(tuple(s2), n)
                if r: notes.append(f'escena {n}: {pid(sl)} sin planos, sustituido por {pid(s2)}'); break
        if not r: notes.append(f'escena {n} hueco {i}: SIN IMAGEN ({pid(sl)})'); continue
        shutil.copy2(P/f'{r[0]}.png', out); reg[out.name] = dict(tipo='plano', origen=r[0])
for k, v in reg.items(): v['sha256'] = hashlib.sha256((O/k).read_bytes()).hexdigest()
(O/'registro.json').write_text(json.dumps({'imagenes': reg, 'notas': notes, 'excluidas': sorted(EXC), 'aceptadas_a_ojo': ACE}, ensure_ascii=False, indent=1))
print(len(reg), 'imágenes;', len([x for x in notes if 'SIN IMAGEN' in x]), 'huecos sin imagen;', len(notes), 'notas')
