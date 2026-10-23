from PIL import Image, ImageDraw

from mangavid import thumbnail
from mangavid.storyboard import parse

STORY = """
@estilo: manhwa style
@negativo: lowres
@ana: young woman, black hair
@miniatura: 1girl, solo, @ana[red dress], crying, burning house
@miniatura_texto: La traición de *Ana*

[001] 1girl, solo, @ana, smiling
Ana sonrió.

[002] city, night
La ciudad dormía.
"""


def test_thumbnail_directives():
    board = parse(STORY)
    assert set(board.characters) == {"ana"}  # @miniatura no es un personaje
    assert board.thumbnail_text == "La traición de *Ana*"
    t = board.thumbnail
    assert t.characters == ["ana"] and t.outfits == {"ana": "red dress"}
    assert thumbnail.thumbnail_scene(board) is t


def test_thumbnail_scene_fallback():
    board = parse("@ana: girl\n[001] city\nx\n[002] 1girl, @ana\ny\n")
    assert thumbnail.thumbnail_scene(board).number == 2


def test_jobs_use_portraits_and_thumbnail_tags(tmp_path):
    board = parse(STORY)
    portraits = tmp_path / "p"
    portraits.mkdir()
    Image.new("RGB", (8, 8)).save(portraits / "ana.png")
    jobs = thumbnail.jobs(board, tmp_path / "m", portraits, 3, 10, "model")
    assert len(jobs) == 3 and len({j.out for j in jobs}) == 3
    j = jobs[0]
    assert j.prompt.startswith("1girl, solo, crying, burning house, close-up")
    assert "young woman, black hair, red dress" in j.prompt
    assert "text" in j.negative and j.faces == [portraits / "ana.png"]


def test_parse_text_highlight():
    assert thumbnail.parse_text("la traición de *Ana*") == [
        ("LA", False), ("TRAICIÓN", False), ("DE", False), ("ANA", True)]
    assert thumbnail.parse_text("me engañó") == [("ME", False), ("ENGAÑÓ", True)]
    assert thumbnail.parse_text("  ") == []


def test_compose_places_text_on_quiet_side(tmp_path):
    base = Image.new("RGB", (1344, 768), (20, 30, 80))
    draw = ImageDraw.Draw(base)
    for x in range(0, 600, 12):  # mucho detalle a la izquierda
        draw.line([(x, 0), (x + 40, 768)], fill=(255, 255, 255), width=3)
    base.save(tmp_path / "b.png")
    assert thumbnail.quietest_side(base) == "derecha"

    out = thumbnail.compose(tmp_path / "b.png", "¡Volvió del *infierno*!", tmp_path / "m.jpg")
    img = Image.open(out)
    assert img.size == thumbnail.SIZE and out.stat().st_size < thumbnail.MAX_BYTES
    # el amarillo del texto resaltado está en la mitad derecha
    yellow = [x for x in range(0, 1280, 4) for y in range(0, 720, 4)
              if img.getpixel((x, y))[0] > 200 and img.getpixel((x, y))[1] > 170
              and img.getpixel((x, y))[2] < 90]
    assert yellow and min(yellow) > 640

    sheet = thumbnail.contact_sheet([out, out], tmp_path / "hoja.jpg")
    assert sheet.exists()
