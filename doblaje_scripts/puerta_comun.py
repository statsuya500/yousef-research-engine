"""Definiciones de «A los 18 llamé a la puerta de mis padres»: cabecera, fichas, ropa, negativos y lugares.
Mismo estilo que «El pastor» y «Mis hijos me eligieron»."""
from mangavid import images

STYLE = ("masterpiece, high score, great score, absurdres, anime illustration, light novel style, clean thin lineart, "
         "soft shading, high-key lighting, bright soft daylight, white sparkles, bokeh, heavily blurred background, "
         "soft cream and white palette, glossy eyes, upper body")
# Cuerpo y cara (no cambian nunca) y ropa por separado: así un traje de gala no se mezcla con el abrigo de diario.
FISICO = {
    "dario": "1boy, young man, 18 years old, messy short dark brown hair, grey eyes, slim build, clean-shaven",
    "isabel": "1girl, mature woman, 37 years old, long straight dark brown hair, grey eyes, elegant",
    "fernando": "1boy, adult man, 45 years old, short black hair with grey temples, sharp brown eyes, thin lips, clean-shaven",
    "ivan": "1boy, young man, 20 years old, styled blond hair, light brown eyes, clean-shaven",
    "valentina": "1girl, young woman, 19 years old, long straight dark brown hair with a side part, grey eyes",
    "ines": "1girl, old woman, 70 years old, catholic nun, kind wrinkled face, small round glasses",
    "toni": "1boy, young man, 19 years old, curly red hair, freckles, green eyes",
    "paula": "1girl, young woman, 20 years old, short black bob hair, warm brown eyes",
    "rafael": "1boy, old man, 75 years old, white hair neatly combed back, tired kind grey eyes, wrinkles",
    "guardia": "1boy, adult man, 40 years old, large build, bald",
    "director": "1boy, adult man, 50 years old, balding, nervous face",
    "policia": "1boy, adult man, 45 years old, short grey hair, serious face",
    "dario_nino": "1boy, little boy, 8 years old, child, messy dark brown hair, big grey eyes",
}
# Cada prenda con color, manga y detalles fijos. "base" es la ropa de diario (la que se usa si el plan no dice otra).
ROPA = {
    "dario": {"base": "plain grey long-sleeve pullover hoodie, faded blue jeans",
              "sudadera": "plain grey long-sleeve pullover hoodie, faded blue jeans",
              "botones": "burgundy long-sleeve bellboy jacket with high collar and gold buttons, black trousers",
              "chofer": "black suit jacket, white shirt, thin black necktie, black trousers",
              "mono": "grey long-sleeve work overalls",
              "traje": "charcoal grey suit jacket, white shirt, silver necktie, grey trousers"},
    "isabel": {"base": "cream long-sleeve silk blouse, beige long trench coat",
               "gala": "silver long-sleeve evening gown, pearl earrings",
               "blanco": "white tailored long-sleeve suit jacket, white trousers, silver rose pendant"},
    "fernando": {"base": "dark navy suit jacket, white shirt, dark red necktie",
                 "esmoquin": "black tuxedo jacket, white shirt, black bow tie"},
    "ivan": {"base": "white blazer over a plain black t-shirt",
             "esmoquin": "white tuxedo jacket, white shirt, black bow tie",
             "sudadera": "dark grey long-sleeve pullover hoodie"},
    "valentina": {"base": "oversized light grey long-sleeve knit sweater",
                  "vestido": "navy blue long-sleeve evening dress"},
    "ines": {"base": "black and white nun habit, white veil, long sleeves"},
    "toni": {"base": "green long-sleeve pullover hoodie"},
    "paula": {"base": "black long-sleeve hotel receptionist blazer, white blouse",
              "casual": "beige long-sleeve knitted cardigan, white blouse"},
    "rafael": {"base": "grey long-sleeve wool cardigan, white shirt",
               "traje": "dark navy suit jacket, white shirt, grey necktie"},
    "guardia": {"base": "black suit jacket, white shirt, black necktie, earpiece"},
    "director": {"base": "dark grey suit jacket, white shirt, blue necktie"},
    "policia": {"base": "dark brown leather jacket, grey sweater"},
    "dario_nino": {"base": "worn blue long-sleeve sweater, brown trousers"},
}
FICHA = {k: f"{v}, {ROPA[k]['base']}" for k, v in FISICO.items()}   # para la cabecera del guion
SAFE_MINOR = ", nsfw, cleavage, suggestive, revealing clothes, makeup, adult, mature"
COMMON = ("lowres, bad anatomy, bad hands, text, watermark, signature, japanese text, logo, blurry face, dark, high contrast, oversaturated, "
          "neon, painterly, realistic, photorealistic, sharp background, muscular, bodybuilder, abs, chibi, nsfw, cleavage, suggestive, key, keys, "
          "multiple girls, multiple boys, 2girls, 2boys, extra person, hair ribbon, hair bow, hair ornament, saturated colors, "
          "sharp focus background, detailed background, hat, headwear, cropped head, head out of frame")
OBJ = ["paper", "document", "phone", "bag", "book", "laptop", "cup", "mug", "glass", "knife", "food", "plate", "car", "watch"]
NEG_CHAR = {
    "dario": "blonde hair, red hair, black hair, long hair, glasses, beard, stubble",
    "dario_sudadera": "jacket, coat, zipper, t-shirt, suit, uniform",
    "dario_botones": "hoodie, jeans, casual clothes, blue clothes, navy, two-tone jacket, necktie",
    "dario_chofer": "hoodie, jeans, casual clothes, uniform, grey suit, gold buttons",
    "dario_mono": "hoodie, suit, necktie, jeans",
    "dario_traje": "hoodie, jeans, uniform, black suit, black necktie",
    "isabel": "blonde hair, red hair, short hair, curly hair, glasses",
    "isabel_base": "evening gown, dress, white suit",
    "isabel_gala": "coat, blouse, trench coat, black dress, red dress",
    "isabel_blanco": "dress, gown, coat, beige, black suit",
    "fernando": "blonde hair, long hair, beard, glasses, young",
    "fernando_base": "tuxedo, bow tie, black suit",
    "fernando_esmoquin": "necktie, navy suit, white jacket",
    "ivan": "brown hair, black hair, long hair, beard, glasses",
    "ivan_base": "tuxedo, bow tie, hoodie, black jacket",
    "ivan_esmoquin": "black jacket, t-shirt, hoodie, necktie",
    "ivan_sudadera": "blazer, suit, tuxedo, white jacket",
    "valentina": "blonde hair, red hair, short hair, glasses",
    "valentina_base": "dress, gown, black sweater",
    "valentina_vestido": "sweater, black dress, red dress, coat",
    "ines": "young, hair, blonde hair, colored clothes",
    "toni": "black hair, brown hair, blonde hair",
    "toni_base": "jacket, t-shirt, suit",
    "paula": "long hair, blonde hair, red hair",
    "paula_base": "cardigan, beige, casual clothes",
    "paula_casual": "uniform, blazer, black jacket",
    "rafael": "young, black hair, brown hair, beard",
    "rafael_base": "suit, necktie, jacket",
    "rafael_traje": "cardigan, sweater, black suit",
    "guardia": "hair, long hair, glasses",
    "director": "young, long hair",
    "policia": "young, uniform, badge, hat, suit",
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
    return f"{FISICO[who]}, {ROPA[who][ropa or 'base']}"


def negative(who, allow=(), side=False, ropa=None, loc=None):
    obj = ", ".join(o for o in OBJ if o not in allow)
    common = COMMON.replace("dark, ", "") if loc in NOCHE else COMMON
    mangas = "" if who == "escenario" else "short sleeves, sleeveless, bare arms, bare shoulders"   # toda la ropa es de manga larga
    n = ", ".join(x for x in (common, obj, NEG_CHAR[who], NEG_CHAR.get(f"{who}_{ropa or 'base'}", ""), mangas, NEG_LUGAR.get(loc, "")) if x)
    return n + (", looking at viewer, facing viewer" if side else "")
