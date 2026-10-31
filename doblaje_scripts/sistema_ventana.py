"""Ventana del «sistema» dibujada por código sobre una imagen."""
import textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
TITLE = ImageFont.truetype('/home/jamal/doblaje/mangavid/fonts/Anton-Regular.ttf', 46)
BODY = ImageFont.truetype('DejaVuSans-Bold.ttf', 30)
def ventana(base_path, lines, out, title='SISTEMA', accent=(90, 200, 255)):
    im = Image.open(base_path).convert('RGB').resize((1344, 768))
    im = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(3))).enhance(0.55)
    im = Image.blend(im, Image.new('RGB', im.size, (20, 40, 90)), 0.35).convert('RGBA')
    wrapped = [w for l in lines for w in (textwrap.wrap(l, 44) or [''])]
    lh = 44; pw = 900; ph = 120 + lh * len(wrapped) + 30; x0, y0 = (1344 - pw)//2, (768 - ph)//2
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((x0-6, y0-6, x0+pw+6, y0+ph+6), 22, outline=accent + (255,), width=10)
    panel = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(panel)
    d.rounded_rectangle((x0, y0, x0+pw, y0+ph), 18, fill=(8, 18, 45, 215), outline=accent + (255,), width=3)
    d.line((x0+30, y0+92, x0+pw-30, y0+92), fill=accent + (180,), width=2)
    tw = d.textlength(title, font=TITLE); d.text((x0 + (pw - tw)/2, y0+20), title, font=TITLE, fill=accent + (255,))
    for i, l in enumerate(wrapped): d.text((x0+45, y0+115 + i*lh), l, font=BODY, fill=(235, 245, 255, 255))
    Image.alpha_composite(Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(10))), panel).convert('RGB').save(out)
