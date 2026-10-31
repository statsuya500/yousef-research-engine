"""Convierte historias/puerta/historia.txt (formato largo de mangavid) al formato local de una línea:
    [NNN] @personaje, @personaje, lugar, tono
    narración…
Lugar y tono se deducen de la descripción de la imagen. Uso:
    python doblaje_scripts/puerta_convertir.py historias/puerta/historia.txt /mnt/c/videos/puerta/historia.txt
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mangavid import storyboard  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from puerta_comun import FICHA, STYLE  # noqa: E402

# Primera coincidencia gana: de lo más concreto a lo más general.
LUGARES = [
    ("cemetery", r"cemetery|headstone"),
    ("court", r"courtroom|court"),
    ("cell", r"holding room|barred window|calabozo"),
    ("chapel", r"chapel"),
    ("boardroom", r"boardroom"),
    ("ballroom", r"charity gala|gala table|ballroom|podium|stage"),
    ("laundry", r"laundry"),
    ("lockers", r"locker"),
    ("garage", r"parking|garage"),
    ("penthouse", r"penthouse|chessboard|chess"),
    ("rooftop", r"rooftop"),
    ("cafe", r"café|cafe"),
    ("shop", r"phone repair shop|workbench"),
    ("workshop", r"car repair workshop|workshop|engine|hardware|vintage car engine"),
    ("library", r"library|magazine photo"),
    ("study", r"wall safe|dark office|home office"),
    ("dining", r"dining"),
    ("bedroom_mansion", r"mansion hallway|staircase in the dark|sitting on stairs|sitting on a staircase"),
    ("hotel_office", r"director's office|hotel director's office|small office for a job"),
    ("office", r"luxury office|modern luxury office|glass walls"),
    ("elevator", r"elevator"),
    ("lobby", r"hotel lobby|reception desk|lobby|hotel building|hotel facade"),
    ("orphanage_office", r"orphanage office|old desk"),
    ("orphanage", r"orphanage|nun|snow|boiler|crib|bunk"),
    ("flat", r"shared apartment|mattress"),
    ("bridge", r"bridge"),
    ("stairs_sun", r"(?=.*(marble stair|mansion|gate))(?=.*(sunny|afternoon|no rain))"),
    ("stairs", r"marble staircase|marble stairs|mansion|wrought iron gate|gate"),
    ("street", r"\bstreet\b|sidewalk|taxi|\bcar\b|sunrise|\bcity\b"),
]
TONOS = [
    ("crying", r"crying|tears|sobbing|weeping"),
    ("shocked", r"shock|wide eyes|wide-eyed|pale|frozen|surprised|disbelief|panick"),
    ("angry", r"furious|angry|shouting|rage|hatred|red-faced"),
    ("smug", r"mocking|smirk|laughing loudly|smug|condescending|arrogant|disgust|contempt|grin"),
    ("sad", r"sad|humiliated|head down|ashamed|shame|defeated|regret|guilt|lonely|tired|hurt|anguish|pleading|despair"),
    ("determined", r"determined|firm|brave|commanding"),
    ("cold", r"cold|serious|stern|suspicious|threatening"),
    ("happy", r"smil|laugh|joy|happy|grateful|proud|cheerful|warm smile|warm friendly"),
]


# Secundarios sin ficha en el guion largo: se detectan por la descripción de la imagen.
EXTRAS = [
    ("guardia", r"security guard"),
    ("director", r"hotel director"),
    ("policia", r"plainclothes detective"),
    ("dario_nino", r"little boy, \d+ years old, messy dark brown hair"),
]


def lugar(image: str, prev: str) -> str:
    low = image.lower()
    for name, pat in LUGARES:
        if re.search(pat, low):
            return name
    return prev or "street"


def tono(image: str) -> str:
    low = image.lower()
    for name, pat in TONOS:
        if re.search(pat, low):
            return name
    return "neutral"


def main(src: str, dst: str) -> None:
    board = storyboard.load(Path(src))
    out = [f"# {Path(src).parent.name}: guion convertido al formato local (lugar y tono deducidos de la imagen).",
           f"@estilo: {STYLE}"]
    out += [f"@{who}: {tags}" for who, tags in FICHA.items()]
    out.append("")
    prev = ""
    for s in board.scenes:
        loc = lugar(s.image, prev)
        prev = loc
        cast = list(s.characters) + [w for w, pat in EXTRAS if re.search(pat, s.image.lower()) and w not in s.characters]
        head = ", ".join([f"@{c}" for c in cast] + [loc, tono(s.image)])
        out.append(f"[{s.number:03d}] {head}\n{s.narration}\n")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text("\n".join(out), encoding="utf-8")
    print(f"{len(board.scenes)} escenas -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
