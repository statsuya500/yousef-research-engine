import pytest
from PIL import Image, ImageDraw

from mangavid import thumbnail
from mangavid.storyboard import parse

STORY = """
@estilo: manhwa style
@negativo: lowres
@ana: young woman, black hair
@leo: young man, brown hair
@miniatura: 1boy, 1girl, @leo, @ana[red dress], shocked, burning house
@miniatura_texto: @leo=prota | @ana=Hija | ¡No saltes!

[001] 1girl, solo, @ana, smiling
Ana sonrió.

[002] city, night
La ciudad dormía.
"""


def test_thumbnail_directives():
    board = parse(STORY)
    assert set(board.characters) == {"ana", "leo"}  # @miniatura no es un personaje
    assert board.thumbnail_text.startswith("@leo=prota")
    t = board.thumbnail
    assert t.characters == ["leo", "ana"] and t.outfits == {"ana": "red dress"}
    assert thumbnail.thumbnail_scene(board) is t


def test_thumbnail_scene_fallback():
    board = parse("@ana: girl\n@leo: boy\n[001] city\nx\n[002] 1girl, @ana\ny\n[003] @leo, @ana\nz\n")
    assert thumbnail.thumbnail_scene(board).number == 3  # mejor con dos personajes


def test_jobs_use_portraits_and_thumbnail_tags(tmp_path):
    board = parse(STORY)
    portraits = tmp_path / "p"
    portraits.mkdir()
    Image.new("RGB", (8, 8)).save(portraits / "ana.png")
    Image.new("RGB", (8, 8), (9, 9, 9)).save(portraits / "leo.png")
    jobs = thumbnail.jobs(board, tmp_path / "m", portraits, 3, 10, "model")
    assert len(jobs) == 3 and len({j.out for j in jobs}) == 3
    j = jobs[0]
    assert j.prompt.startswith("1boy, 1girl, shocked, burning house, anime key visual")
    assert "young woman, black hair, red dress" in j.prompt
    assert "text" in j.negative and j.faces == [portraits / "leo.png", portraits / "ana.png"]


def test_parse_text():
    items = thumbnail.parse_text("@Leo=prota | @ana=*Hija* | ¡No saltes! |  ")
    assert [(i.text, i.character) for i in items] == [
        ("PROTA", "leo"), ("HIJA", "ana"), ("¡NO SALTES!", None)]


def test_wrap_long_label():
    from PIL import ImageFont

    font = ImageFont.truetype(str(thumbnail.FONT), 72)
    lines = thumbnail._wrap("Asesino secreto de rango SSS", font, 380)
    assert 2 <= len(lines) <= 3 and all(font.getlength(x) <= 380 for x in lines)
    assert thumbnail._wrap("PROTA", font, 380) == ["PROTA"]


def _two_people(path):
    img = Image.new("RGB", (1344, 768), (120, 180, 240))
    d = ImageDraw.Draw(img)
    for cx in (336, 1008):
        d.ellipse([cx - 110, 90, cx + 110, 330], fill=(250, 220, 200))
        d.rectangle([cx - 150, 330, cx + 150, 768], fill=(60, 60, 90))
    img.save(path)
    return path


def _yellow(img, x0, x1):
    return [(x, y) for x in range(x0, x1, 4) for y in range(0, 720, 4)
            if img.getpixel((x, y))[0] > 200 and img.getpixel((x, y))[1] > 180 and img.getpixel((x, y))[2] < 90]


def test_labels_go_next_to_their_character(tmp_path):
    base = _two_people(tmp_path / "b.png")
    out = thumbnail.compose(base, "@leo=PROTA", tmp_path / "l.jpg", ["leo", "ana"])
    img = Image.open(out)
    assert img.size == thumbnail.SIZE and out.stat().st_size < thumbnail.MAX_BYTES
    assert _yellow(img, 0, 640) and not _yellow(img, 640, 1280)

    out = thumbnail.compose(base, "@ana=HIJA", tmp_path / "r.jpg", ["leo", "ana"])
    img = Image.open(out)
    assert _yellow(img, 640, 1280) and not _yellow(img, 0, 640)

    with pytest.raises(ValueError, match="@luis"):
        thumbnail.compose(base, "@luis=CEO", tmp_path / "x.jpg", ["leo", "ana"])


def test_compose_without_text_and_sheet(tmp_path):
    base = _two_people(tmp_path / "b.png")
    plain = thumbnail.compose(base, "", tmp_path / "p.jpg")
    full = thumbnail.compose(base, "@leo=PROTA | @ana=HIJA | ¿?!", tmp_path / "f.jpg", ["leo", "ana"])
    assert Image.open(plain).size == thumbnail.SIZE
    assert thumbnail.contact_sheet([plain, full], tmp_path / "hoja.jpg").exists()


def test_arrows_are_slightly_curved():
    import math

    pts = thumbnail._curve((100, 400), (500, 400))
    assert pts[0] == (100, 400) and pts[-1] == (500, 400)
    # el centro se separa un poco de la línea recta (flechas casi rectas) hacia arriba
    mid = pts[len(pts) // 2]
    assert 400 - 0.1 * 400 < mid[1] < 400 - 0.04 * 400
    # casi vertical: se abomba hacia el borde más cercano (aquí, la izquierda)
    pts = thumbnail._curve((300, 600), (310, 300))
    assert min(p[0] for p in pts) < 300 - 10
    assert all(math.isfinite(c) for p in pts for c in p)


def test_cli_own_image(tmp_path):
    from mangavid.cli import main

    story = tmp_path / "h.txt"
    story.write_text("@alex: man\n[001] city\nx\n", encoding="utf-8")
    own = _two_people(tmp_path / "mia.png")
    main(["miniatura", str(story), "--imagen", str(own), "--texto", "@alex=PROTA | @tio=TÍO | ?!?"])
    out = tmp_path / "h_miniaturas" / "miniatura_1.jpg"
    assert Image.open(out).size == thumbnail.SIZE
    assert (tmp_path / "h_miniaturas" / "opciones.jpg").exists()


def test_parse_speech_and_thumbnail_style():
    items = thumbnail.parse_text("@kai=prota | @kai>¡No saltes! | ?!?")
    assert [(i.text, i.character, i.speech) for i in items] == [
        ("PROTA", "kai", False), ("¡NO SALTES!", "kai", True), ("?!?", None, False)]
    from mangavid.storyboard import parse
    board = parse("@estilo: soft glow\n@miniatura_estilo: crisp daylight\n@kai: 1boy\n[001] solo, @kai\nHola.")
    assert board.thumbnail_style == "crisp daylight" and board.style == "soft glow"
