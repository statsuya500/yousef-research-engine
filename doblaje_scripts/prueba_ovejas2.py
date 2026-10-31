from pathlib import Path
from mangavid import images
from pastor_comun import STYLE, LUGAR, L, negative
O = Path('/mnt/c/videos/pastor_oro/prueba_animales')
p = ", ".join(("no humans, animal focus, several white sheep grazing together on green grass, side view, natural sheep proportions, small dark eyes, woolly sheep, " + LUGAR['meadow'], STYLE))
neg = negative("escenario", ("animal", "sheep")) + ", extra legs, deformed animal, extra heads, kawaii, chibi, cute, big eyes, sparkling eyes, eyelashes, anthropomorphic, smiling animal, human eyes, pink, cloud"
images.generate([images.Job(p, 970 + s, O/f"H_ovejas_normales_{s}.png", L, [], neg, images.IP_SCALE) for s in range(4)], neg, images.DEFAULT_MODEL)
