"""Comprobaciones de imagen: máscara de persona, vaso (zonas), lado de la cara."""
import numpy as np
from imgutils.detect import detect_faces, detect_heads
from imgutils.segment import segment_rgba_with_isnetis
from imgutils.tagging import get_wd14_tags
def person_mask(im):
    m = np.asarray(segment_rgba_with_isnetis(im)[0]); return (m > 0.5) if m.dtype != np.uint8 else (m > 128)
def cups(im):
    W, H = im.size; cw, ch = W // 2, int(H * 0.30); out = []
    for gy in range(3):
        for gx in range(4):
            x0 = int(gx * (W - cw) / 3); y0 = int(H * 0.35 + gy * (H * 0.65 - ch) / 2)
            t = get_wd14_tags(im.crop((x0, y0, x0 + cw, y0 + ch)), general_threshold=0.2)[1]
            out.append(dict(vaso=max(t.get('cup', 0), t.get('holding_cup', 0)), cafe=t.get('coffee', 0)))
    return out
def face_side(im):
    hb = max(detect_heads(im), key=lambda x: x[1])[0]; fb = max(detect_faces(im), key=lambda x: x[2])[0]
    return round(((fb[0] + fb[2]) / 2 - (hb[0] + hb[2]) / 2) / (hb[2] - hb[0]), 3)
