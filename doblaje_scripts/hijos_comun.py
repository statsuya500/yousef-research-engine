"""Definiciones de «Mi marido defendió a su exmujer, pero sus hijos me eligieron a mí»."""
from mangavid import images
STYLE = ("masterpiece, high score, great score, absurdres, anime illustration, light novel style, clean thin lineart, "
         "soft shading, high-key lighting, bright soft daylight, white sparkles, bokeh, heavily blurred background, "
         "soft cream and white palette, glossy eyes, upper body")
FICHA = {
    "irene": "1girl, young woman, 31 years old, long dark brown hair in a low ponytail, warm brown eyes, gentle face, light blue blouse, navy cardigan",
    "javier": "1boy, adult man, 37 years old, short black hair, black rectangular glasses, dark eyes, grey suit, white shirt, blue tie",
    "sabrina": "1girl, adult woman, 34 years old, long curly red hair, green eyes, red lipstick, elegant red dress",
    "nerea": "1girl, teenage girl, 15 years old, short black bob cut at jaw length, straight bangs, grey eyes, navy school blazer, white shirt, modest school uniform",
    "pablo": "1boy, little boy, 5 years old, child, messy light brown hair, big round brown eyes, chubby cheeks, yellow hoodie",
    "marco": "1boy, adult man, 40 years old, short dark blond hair, stubble, light grey suit, gold watch",
    "carmen": "1girl, old woman, 65 years old, short curly grey hair, pearl necklace, stern face, purple cardigan",
}
SAFE_MINOR = ", nsfw, cleavage, suggestive, revealing clothes, makeup, adult, mature"
COMMON = ("lowres, bad anatomy, bad hands, text, watermark, signature, japanese text, logo, blurry face, dark, high contrast, oversaturated, "
          "neon, painterly, realistic, photorealistic, sharp background, muscular, bodybuilder, abs, chibi, nsfw, cleavage, suggestive, key, keys, "
          "multiple girls, multiple boys, 2girls, 2boys, extra person, hair ribbon, hair bow, hair ornament, saturated colors, "
          "sharp focus background, detailed background, hat, headwear, cropped head, head out of frame")
OBJ = ["paper", "document", "phone", "bag", "book", "laptop", "cup", "mug", "glass", "knife", "food", "plate", "toy", "backpack"]
NEG_CHAR = {
    "irene": "short hair, black hair, blonde hair, red hair, grey hair",
    "javier": "long hair, brown hair, blonde hair, beard, no glasses",
    "sabrina": "straight hair, brown hair, black hair, blonde hair, short hair",
    "nerea": "long hair, brown hair, red hair, blonde hair, adult, child" + SAFE_MINOR,
    "pablo": "teenager, adult, baby, black hair, blonde hair, red hair" + SAFE_MINOR,
    "carmen": "young, black hair, brown hair, long hair",
    "marco": "black hair, brown hair, long hair, beard, black suit",
    "escenario": "1girl, 1boy, person, people, human, character, silhouette, face",
}
LUGAR = {
    "home": "inside a cozy family living room, soft diffused daylight, pastel colors, soft blurry background",
    "kitchen": "inside a warm home kitchen, soft diffused daylight, pastel colors, soft blurry background",
    "kidsroom": "inside a child's bedroom with toys and drawings on the wall, soft diffused daylight, pastel colors, soft blurry background",
    "school": "in front of a school entrance, soft diffused daylight, pastel colors, soft blurry background",
    "park": "in a sunny city park, green trees, soft diffused daylight, pastel colors, soft blurry background",
    "restaurant": "inside an elegant restaurant, warm soft lights, pastel colors, soft blurry background",
    "office": "inside a modern corporate office, glass walls, soft diffused daylight, pastel colors, soft blurry background",
    "court": "inside a family courtroom, wooden benches, soft diffused daylight, pastel colors, soft blurry background",
    "hospital": "inside a bright hospital corridor, soft diffused daylight, pastel colors, soft blurry background",
    "street": "on a city street sidewalk, soft diffused daylight, pastel colors, soft blurry buildings in the background",
    "hotel": "inside the grand lobby of a luxury hotel, marble floor, chandelier, soft warm lights, pastel colors, soft blurry background",
}
ESCENARIO = {k: "no humans, scenery, " + v.replace("inside ", "").replace("in front of ", "").replace("on a ", "").replace(", soft blurry background", "").replace(", soft blurry buildings in the background", "")
             for k, v in LUGAR.items()}
L, V = (1344, 768), images.PORTRAIT
ROPA = {"sabrina": {"sencilla": "jeans, old denim jacket, no makeup, tired"}}
def ficha(who, ropa=None):
    f = FICHA[who]
    if ropa == "sencilla": f = f.replace("red lipstick, elegant red dress", "")
    return f.rstrip(", ") + (", " + ROPA[who][ropa] if ropa else "")
def negative(who, allow=(), side=False):
    obj = ", ".join(o for o in OBJ if o not in allow)
    n = ", ".join(x for x in (COMMON, obj, NEG_CHAR[who]) if x)
    return n + (", looking at viewer, facing viewer" if side else "")
