"""Definiciones de «El pastor del valle de oro»: cabecera aprobada exacta, fichas, negativos y lugares."""
from mangavid import images
STYLE = ("masterpiece, high score, great score, absurdres, anime illustration, light novel style, clean thin lineart, "
         "soft shading, high-key lighting, bright soft daylight, white sparkles, bokeh, heavily blurred background, "
         "soft cream and white palette, glossy eyes, upper body")
FICHA = {
    "daniel": "1boy, young man, 32 years old, short messy brown hair, light stubble, hazel eyes, average build, normal body",
    "lucia": "1girl, young woman, 29 years old, long auburn hair in a low ponytail, amber eyes, light freckles, green flannel shirt",
    "marcos": "1boy, adult man, 34 years old, slicked back blonde hair, blue eyes, black suit, white shirt, gold watch",
    "elena": "1girl, young woman, 30 years old, long straight black hair, purple eyes, elegant white dress, pearl earrings",
    "ramiro": "1boy, old man, 62 years old, bald, thick grey mustache, round face, brown vest over a white shirt",
    "pilar": "1girl, old woman, 70 years old, white hair in a short perm, kind wrinkled face, round glasses, white apron over a blue dress",
    "nico": "1boy, little boy, 8 years old, child, spiky black hair, big brown eyes, red raincoat",
    "cura": "1boy, old man, 68 years old, short white hair, kind face, long black cassock, black priest clothes, white clerical collar",
    "periodista": "1boy, adult man, 55 years old, grey hair, grey beard, thin glasses, brown tweed jacket",
    "abogado": "1boy, adult man, 45 years old, neat dark brown hair, dark grey suit, burgundy tie",
    "dani": "1boy, young man, 22 years old, curly orange hair, freckles, yellow t-shirt, delivery cap",
}
ROPA = {"daniel": {"ciudad": "formal navy blue business suit, white dress shirt, suit jacket", "pastor": "olive green work jacket over a beige knit sweater"},
        "lucia": {"bata": "white lab coat over the green flannel shirt"}}
COMMON = ("lowres, bad anatomy, bad hands, text, watermark, signature, japanese text, logo, blurry face, dark, high contrast, oversaturated, "
          "neon, painterly, realistic, photorealistic, sharp background, muscular, bodybuilder, abs, chibi, nsfw, cleavage, suggestive, key, keys, "
          "multiple girls, multiple boys, 2girls, 2boys, extra person, hair ribbon, hair bow, hair ornament, saturated colors, "
          "sharp focus background, detailed background, pagoda, asian architecture, japanese house, hat, headwear, cropped head, head out of frame")
OBJ = ["paper", "document", "phone", "bag", "book", "laptop", "cup", "mug", "glass", "knife", "food", "plate", "animal", "sheep", "dog"]
NEG_CHAR = {
    "daniel": "black hair, blonde hair, red hair, long hair, glasses, beard",
    "daniel_ciudad": "jeans, casual jacket, hoodie, green jacket",
    "lucia": "black hair, blonde hair, pink hair, purple hair, lavender hair, short hair",
    "marcos": "brown hair, black hair, long hair, beard, glasses",
    "elena": "brown hair, blonde hair, red hair, short hair, curly hair",
    "ramiro": "young, hair, long hair, black hair, beard",
    "pilar": "young, black hair, brown hair, long hair",
    "nico": "teenager, adult, blonde hair, brown hair, nsfw",
    "cura": "young, black hair, beard, white robe, white clothes",
    "periodista": "young, black hair, blonde hair",
    "abogado": "blonde hair, black hair, glasses, beard",
    "dani": "black hair, brown hair, blonde hair",
    "escenario": "1girl, 1boy, person, people, human, character, silhouette, face",
}
LUGAR = {
    "office": "inside a modern glass office at the top of a skyscraper, city view, soft diffused daylight, pastel colors, soft blurry background",
    "city": "on a busy city street with tall buildings, soft diffused daylight, pastel colors, soft blurry background",
    "farm": "in front of an old stone farmhouse in the mountains, green meadow, soft diffused daylight, pastel colors, soft blurry background",
    "barn": "inside a wooden barn with hay, warm soft light, pastel colors, soft blurry background",
    "cabin": "inside a rustic wooden cabin with a fireplace, warm soft light, pastel colors, soft blurry background",
    "meadow": "on a green mountain meadow, snowy peaks in the distance, soft diffused daylight, pastel colors, soft blurry background",
    "river": "beside a clear mountain river with stones, green trees, soft diffused daylight, pastel colors, soft blurry background",
    "village": "in a small european stone village square in the spanish mountains, old church bell tower, stone fountain, soft diffused daylight, pastel colors, soft blurry background",
    "bar": "inside a small rustic spanish village bar with wooden tables, warm soft light, pastel colors, soft blurry background",
    "townhall": "inside a small village town hall meeting room with wooden chairs, soft diffused daylight, pastel colors, soft blurry background",
    "clinic": "inside a small rural veterinary clinic, soft diffused daylight, pastel colors, soft blurry background",
}
ESCENARIO = {
    "office": "no humans, scenery, modern glass office at the top of a skyscraper, city view, soft diffused daylight, pastel colors",
    "city": "no humans, scenery, busy city street with tall buildings, soft diffused daylight, pastel colors",
    "farm": "no humans, scenery, old stone farmhouse in the mountains, green meadow, soft diffused daylight, pastel colors",
    "barn": "no humans, scenery, inside a wooden barn with hay, warm soft light, pastel colors",
    "cabin": "no humans, scenery, inside a rustic wooden cabin with a fireplace, warm soft light, pastel colors",
    "meadow": "no humans, scenery, green mountain valley meadow, snowy peaks, soft diffused daylight, pastel colors",
    "river": "no humans, scenery, clear mountain river with stones, green trees, soft diffused daylight, pastel colors",
    "village": "no humans, scenery, small european stone village square in the spanish mountains, old church bell tower, stone fountain, soft diffused daylight, pastel colors",
    "bar": "no humans, scenery, inside a small rustic village bar with wooden tables, warm soft light, pastel colors",
    "townhall": "no humans, scenery, small village town hall meeting room with wooden chairs, soft diffused daylight, pastel colors",
    "clinic": "no humans, scenery, small rural veterinary clinic, soft diffused daylight, pastel colors",
}
L, V = (1344, 768), images.PORTRAIT
def ficha(who, ropa=None):
    return FICHA[who] + (", " + ROPA[who][ropa] if ropa else "")
def negative(who, allow=(), side=False, ropa=None):
    obj = ", ".join(o for o in OBJ if o not in allow)
    n = ", ".join(x for x in (COMMON, obj, NEG_CHAR[who], NEG_CHAR.get(f"{who}_{ropa}", "")) if x)
    return n + (", looking at viewer, facing viewer" if side else "")
