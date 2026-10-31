"""Definiciones de «A los 18 llamé a la puerta de mis padres»: cabecera, fichas, ropa, negativos y lugares.
Mismo estilo que «El pastor» y «Mis hijos me eligieron»."""
from mangavid import images

STYLE = ("masterpiece, high score, great score, absurdres, anime illustration, light novel style, clean thin lineart, "
         "soft shading, high-key lighting, bright soft daylight, white sparkles, bokeh, heavily blurred background, "
         "soft cream and white palette, glossy eyes, upper body")
FICHA = {
    "dario": "1boy, young man, 18 years old, messy short dark brown hair, grey eyes, slim build, clean-shaven",
    "isabel": "1girl, mature woman, 37 years old, long straight dark brown hair, grey eyes, elegant, cream blouse, beige long coat",
    "fernando": "1boy, adult man, 45 years old, short black hair with grey temples, sharp brown eyes, thin lips, dark navy suit, white shirt",
    "ivan": "1boy, young man, 20 years old, styled blond hair, light brown eyes, white blazer, black t-shirt",
    "valentina": "1girl, young woman, 19 years old, long straight dark brown hair with a side part, grey eyes, oversized grey sweater",
    "ines": "1girl, old woman, 70 years old, catholic nun, black and white nun habit, white veil, kind wrinkled face, small round glasses",
    "toni": "1boy, young man, 19 years old, curly red hair, freckles, green eyes, green hoodie",
    "paula": "1girl, young woman, 20 years old, short black bob hair, warm brown eyes, black hotel receptionist uniform, white blouse",
    "rafael": "1boy, old man, 75 years old, white hair neatly combed back, tired kind grey eyes, wrinkles, grey wool cardigan, white shirt",
    "guardia": "1boy, adult man, 40 years old, large build, bald, black suit, earpiece",
    "director": "1boy, adult man, 50 years old, balding, nervous face, dark suit",
    "policia": "1boy, adult man, 45 years old, short grey hair, dark jacket, serious face",
    "dario_nino": "1boy, little boy, 8 years old, child, messy dark brown hair, big grey eyes, worn blue sweater",
}
ROPA = {
    "dario": {"sudadera": "grey hoodie, old jeans", "botones": "burgundy bellboy uniform with gold buttons",
              "chofer": "black suit, white shirt, black tie", "mono": "grey work overalls",
              "traje": "elegant dark grey suit, white shirt"},
    "isabel": {"gala": "elegant silver long-sleeve evening gown, pearl earrings", "blanco": "white tailored suit, silver rose pendant"},
    "fernando": {"esmoquin": "black tuxedo, bow tie"},
    "ivan": {"esmoquin": "white tuxedo jacket, black bow tie", "sudadera": "dark grey hoodie"},
    "valentina": {"vestido": "navy blue long-sleeve evening dress"},
    "paula": {"casual": "beige knitted cardigan, white blouse"},
    "rafael": {"traje": "dark navy suit, white shirt"},
}
SAFE_MINOR = ", nsfw, cleavage, suggestive, revealing clothes, makeup, adult, mature"
COMMON = ("lowres, bad anatomy, bad hands, text, watermark, signature, japanese text, logo, blurry face, dark, high contrast, oversaturated, "
          "neon, painterly, realistic, photorealistic, sharp background, muscular, bodybuilder, abs, chibi, nsfw, cleavage, suggestive, key, keys, "
          "multiple girls, multiple boys, 2girls, 2boys, extra person, hair ribbon, hair bow, hair ornament, saturated colors, "
          "sharp focus background, detailed background, hat, headwear, cropped head, head out of frame")
OBJ = ["paper", "document", "phone", "bag", "book", "laptop", "cup", "mug", "glass", "knife", "food", "plate", "car", "watch"]
NEG_CHAR = {
    "dario": "blonde hair, red hair, black hair, long hair, glasses, beard, stubble",
    "dario_botones": "hoodie, jeans, casual clothes",
    "dario_chofer": "hoodie, jeans, casual clothes, uniform",
    "isabel": "blonde hair, red hair, short hair, curly hair, glasses",
    "fernando": "blonde hair, long hair, beard, glasses, young",
    "ivan": "brown hair, black hair, long hair, beard, glasses",
    "valentina": "blonde hair, red hair, short hair, glasses",
    "ines": "young, hair, blonde hair, colored clothes",
    "toni": "black hair, brown hair, blonde hair",
    "paula": "long hair, blonde hair, red hair",
    "rafael": "young, black hair, brown hair, beard",
    "guardia": "hair, long hair, glasses",
    "director": "young, long hair",
    "policia": "young, uniform, badge, hat",
    "dario_nino": "teenager, adult, blonde hair, red hair" + SAFE_MINOR,
    "escenario": "1girl, 1boy, person, people, human, character, silhouette, face",
}
_D = ", soft diffused daylight, pastel colors, soft blurry background"
_N = ", soft warm evening light, pastel colors, soft blurry background"
LUGAR = {
    "stairs": "outdoors, exterior, on the wide wet marble front steps of a white neoclassical mansion with columns and big lit windows, rainy night, heavy rain, wet hair, dark blue sky, warm light from the windows" + _N,
    "stairs_sun": "at the marble staircase of a white mansion with flowers, sunny afternoon" + _D,
    "orphanage": "in the courtyard of an old stone orphanage with bare trees" + _D,
    "orphanage_office": "inside a small old orphanage office with a wooden desk and a plain wall" + _D,
    "chapel": "inside a small old stone chapel with wooden benches and candles" + _N,
    "library": "inside an old public library reading room with tall windows" + _D,
    "flat": "inside a tiny shared apartment with a mattress on the floor" + _D,
    "workshop": "inside a small car repair workshop with tools on the wall" + _D,
    "shop": "inside a small cluttered phone repair shop with a workbench" + _N,
    "lobby": "in a luxury hotel lobby with a marble floor and golden chandeliers" + _D,
    "laundry": "in a hotel basement laundry room with washing machines and white towels" + _D,
    "lockers": "in a hotel staff locker room with metal lockers" + _D,
    "garage": "in an underground hotel parking garage" + _N,
    "hotel_office": "inside a hotel director's office with leather chairs" + _D,
    "elevator": "inside a hotel elevator with golden mirror walls" + _N,
    "penthouse": "inside a luxury penthouse living room with old furniture and a chessboard, city lights through the windows" + _N,
    "rooftop": "on a hotel rooftop at night with city lights below" + _N,
    "cafe": "inside a small all-night cafe with a rainy window" + _N,
    "cell": "inside a small bare holding room with a concrete bench" + _D,
    "office": "inside a modern glass office at the top of a skyscraper, city view" + _D,
    "dining": "inside an elegant mansion dining room with candles" + _N,
    "study": "inside a dark wooden home office with a painting on the wall" + _N,
    "bedroom_mansion": "on the stairs of an elegant mansion hallway" + _N,
    "boardroom": "in a large modern boardroom with a long table and panoramic windows" + _D,
    "ballroom": "in a luxury hotel ballroom decorated for a charity gala, crystal chandeliers" + _N,
    "bridge": "under a city bridge at night, rain, city lights in the distance" + _N,
    "street": "on a city street" + _D,
    "cemetery": "in a small quiet cemetery with green grass, cloudy sky" + _D,
    "court": "inside a courtroom with wooden benches and tall windows" + _D,
}
# Exteriores de noche: sin esto el «bright soft daylight» del estilo convierte la escalera bajo la lluvia en un salón de día.
# Los interiores de noche (gala, capilla…) se quedan con la luz clara de siempre.
NOCHE = {"stairs", "bridge", "rooftop"}
NEG_LUGAR = {"stairs": "indoors, interior, ceiling, chandelier, sunlight, daytime, window frame, church, cathedral, dome, castle, spire, tower, bokeh orbs",
             "bridge": "indoors, interior, sunlight, daytime", "rooftop": "indoors, interior, sunlight, daytime"}


# Fondo de los primeros planos en esos exteriores (los demás primeros planos llevan fondo claro genérico).
FONDO_CERCA = {"stairs": "rainy night, rain drops, wet hair, dark blue blurry background, warm window light glow",
               "bridge": "rainy night, rain drops, wet hair, dark blurry city lights background",
               "rooftop": "night, dark blue blurry city lights background"}


def fondo_cerca(loc=None):
    return FONDO_CERCA.get(loc, "soft blurry background, bokeh, pastel colors")


def estilo(loc=None):
    """El estilo de siempre; de noche cambia la luz de día por luz cálida de noche."""
    if loc in NOCHE:
        return STYLE.replace("high-key lighting, bright soft daylight", "soft warm night lighting, moonlight, rain glow" if "rain" in LUGAR[loc] else "soft warm night lighting")
    return STYLE


ESCENARIO = {k: "no humans, scenery, " + v.replace("at the foot of ", "").replace("in the ", "").replace("inside ", "")
             .replace("in a ", "").replace("on a ", "").replace("on the ", "").replace("under ", "")
             for k, v in LUGAR.items()}
L, V = (1344, 768), images.PORTRAIT


def ficha(who, ropa=None):
    return FICHA[who] + (", " + ROPA[who][ropa] if ropa else "")


def negative(who, allow=(), side=False, ropa=None, loc=None):
    obj = ", ".join(o for o in OBJ if o not in allow)
    common = COMMON.replace("dark, ", "") if loc in NOCHE else COMMON
    n = ", ".join(x for x in (common, obj, NEG_CHAR[who], NEG_CHAR.get(f"{who}_{ropa}", ""), NEG_LUGAR.get(loc, "")) if x)
    return n + (", looking at viewer, facing viewer" if side else "")
