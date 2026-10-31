"""Definiciones de «El Sistema del Chef Divino»: cabecera aprobada exacta, fichas, negativos y lugares."""
from mangavid import images
STYLE = ("masterpiece, high score, great score, absurdres, anime illustration, light novel style, clean thin lineart, "
         "soft shading, high-key lighting, bright soft daylight, white sparkles, bokeh, heavily blurred background, "
         "soft cream and white palette, glossy eyes, upper body")
FICHA = {
    "hugo": "1boy, young man, 24 years old, messy dark brown hair, green eyes, average build, normal body",
    "marina": "1girl, young woman, 26 years old, short black bob hair with straight bangs, red eyes, black turtleneck, red coat",
    "bruno": "1boy, adult man, 35 years old, slicked back black hair, thin mustache, grey eyes, black chef jacket",
    "valentina": "1girl, young woman, 24 years old, long wavy pink hair, light blue eyes, pink dress",
    "celia": "1girl, young woman, 30 years old, short wavy blonde hair, blue eyes, modern black chef jacket with gold buttons",
    "rosa": "1girl, old woman, 72 years old, grey hair in a bun, kind eyes, wrinkles, green apron over a brown cardigan",
}
ROPA = {"hugo": {"repartidor": "orange delivery jacket over a grey t-shirt", "chef": "white chef jacket with black buttons, red neckerchief"}}
COMMON = ("lowres, bad anatomy, bad hands, text, watermark, signature, japanese text, logo, blurry face, dark, high contrast, oversaturated, "
          "neon, painterly, realistic, photorealistic, sharp background, muscular, bodybuilder, abs, chibi, nsfw, cleavage, suggestive, key, keys, "
          "multiple girls, multiple boys, 2girls, 2boys, extra person, hair ribbon, hair bow, ribbon, hair ornament, saturated colors, "
          "sharp focus background, detailed background, hat, beret, chef hat, headwear, cropped head, head out of frame")
OBJ = ["paper", "document", "phone", "bag", "book", "laptop", "cup", "mug", "glass", "knife", "food", "plate", "bowl", "pan"]
NEG_CHAR = {
    "hugo": "black hair, blonde hair, white hair, grey hair, blue eyes",
    "marina": "long hair, white hair, brown hair, blue eyes, white coat",
    "bruno": "brown hair, blonde hair, beard, white chef jacket",
    "valentina": "white hair, brown hair, blonde hair, red dress, white dress, short hair",
    "rosa": "young, black hair, brown hair",
    "celia": "long hair, brown hair, black hair, white chef jacket",
    "escenario": "1girl, 1boy, person, people, human, character, silhouette, face",
}
LUGAR = {
    "kitchen": "inside a busy restaurant kitchen, steel counters, soft diffused daylight, pastel colors, soft blurry background",
    "stall": "at a small street food stall at a night market, warm paper lanterns, pastel colors, soft blurry background",
    "restaurant": "inside an elegant restaurant dining room, warm soft lights, pastel colors, soft blurry background",
    "tvstudio": "inside a television cooking show studio, bright stage lights, pastel colors, soft blurry background",
    "apartment": "inside a small modest apartment, soft diffused daylight, pastel colors, soft blurry background",
    "street": "on a city street sidewalk, soft diffused daylight, pastel colors, soft blurry buildings in the background",
    "market": "inside a busy food market with fruit and vegetable stands, soft diffused daylight, pastel colors, soft blurry background",
    "hospital": "inside a bright hospital room, soft diffused daylight, pastel colors, soft blurry background",
}
L, V = (1344, 768), images.PORTRAIT
def ficha(who, ropa=None):
    return FICHA[who] + (", " + ROPA[who][ropa] if ropa else "")
def negative(who, allow=(), side=False):
    obj = ", ".join(o for o in OBJ if o not in allow)
    n = ", ".join(x for x in (COMMON, obj, NEG_CHAR[who]) if x)
    return n + (", looking at viewer, facing viewer" if side else "")
