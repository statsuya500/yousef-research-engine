"""Corrección de fondo de las viñetas dobles: sin halo; el personaje y 3 px alrededor no se tocan."""
import numpy as np
from PIL import Image
from scipy import ndimage
def blur(a, r): return np.stack([ndimage.gaussian_filter(a[..., c], r) for c in range(a.shape[-1])], -1)
def correct(im, m, target_mean, radius=4, pull=0.4):
    a = np.asarray(im).astype(float); protect = ndimage.binary_dilation(m, iterations=3)
    bg = (~protect).astype(float)[..., None]
    bl = blur(a * bg, radius) / np.maximum(blur(bg, radius), 1e-3)
    bl = bl + pull * (target_mean - a[~m].mean(0))
    w = np.clip(ndimage.distance_transform_edt(~protect) / 3.0, 0, 1)[..., None]
    return Image.fromarray(np.clip(a * (1 - w) + bl * w, 0, 255).round().astype('uint8'))
