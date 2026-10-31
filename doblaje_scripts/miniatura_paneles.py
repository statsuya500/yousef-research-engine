"""Miniatura de tres paneles con cortes en diagonal (estilo NubeManga) y titular corto abajo."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance
from imgutils.detect import detect_faces
ANTON = '/home/jamal/doblaje/mangavid/fonts/Anton-Regular.ttf'
W, H = 1280, 720
def crop_face(path, w, h):
    im = Image.open(path).convert('RGB'); f = max(detect_faces(im), key=lambda x: x[2])[0]
    cx, cy = (f[0] + f[2]) / 2, (f[1] + f[3]) / 2; s = max(h / im.height, w / im.width)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); cx, cy = cx * s, cy * s
    x0 = int(min(max(cx - w / 2, 0), im.width - w)); y0 = int(min(max(cy - h * 0.42, 0), im.height - h))
    return im.crop((x0, y0, x0 + w, y0 + h))
def headline(lines, size):
    """lines: [[(texto, color), ...], ...]"""
    f = ImageFont.truetype(ANTON, size); st = int(size * 0.09); pad = st + 10
    widths = [sum(f.getlength(t) for t, _ in ln) for ln in lines]; lh = int(size * 1.15)
    L = Image.new('RGBA', (int(max(widths)) + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k, ln in enumerate(lines):
        x = pad + (max(widths) - widths[k]) / 2; y = pad + k * lh - size * 0.1
        for t, c in ln:
            d.text((x, y), t, font=f, fill=(0, 0, 0), stroke_width=st, stroke_fill=(0, 0, 0)); d.text((x, y), t, font=f, fill=c); x += f.getlength(t)
    sl = 0.15; L = L.transform((L.width + int(sl * L.height), L.height), Image.AFFINE, (1, sl, -sl * L.height, 0, 1, 0), resample=Image.BICUBIC)
    L = L.rotate(-3, resample=Image.BICUBIC, expand=True); return L.crop(L.getbbox())
def make(paths, lines, out, size=104):
    pw = 520; cuts = [(0, 430, 0, 330), (330, 950, 430, 850), (850, W, 950, W)]  # (x_top_ini, x_top_fin, x_bot_ini, x_bot_fin)
    canvas = Image.new('RGB', (W, H), 'white')
    for p, (a, b, c, d) in zip(paths, [(0, 430, 0, 330), (430, 950, 330, 850), (950, W, 850, W)]):
        x0 = min(a, c); x1 = max(b, d); tile = crop_face(p, x1 - x0, H)
        tile = ImageEnhance.Color(ImageEnhance.Contrast(tile).enhance(1.08)).enhance(1.15)
        m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(a, 0), (b, 0), (d, H), (c, H)], fill=255)
        layer = Image.new('RGB', (W, H)); layer.paste(tile, (x0, 0)); canvas.paste(layer, (0, 0), m)
    dr = ImageDraw.Draw(canvas)
    for xt, xb in ((430, 330), (950, 850)): dr.line([(xt, 0), (xb, H)], fill='white', width=12)
    v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).rectangle((0, H - 260, W, H), fill=150)
    canvas = Image.composite(ImageEnhance.Brightness(canvas).enhance(0.55), canvas, v.filter(ImageFilter.GaussianBlur(60)))
    cv = canvas.convert('RGBA'); hl = headline(lines, size); cv.alpha_composite(hl, ((W - hl.width) // 2, H - hl.height - 22))
    cv.convert('RGB').save(out, quality=92)
