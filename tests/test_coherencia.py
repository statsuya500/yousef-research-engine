"""Coherencia visual: los 8 puntos, con herramientas simuladas (sin modelos ni imágenes reales).

Cada «imagen» es un PNG de un color; el detector devuelve la imagen entera como una persona y el
etiquetador falso responde según ese color. Así se prueba la lógica sin depender de los modelos.
"""

import json

from PIL import Image

from mangavid import coherencia as co
from mangavid.storyboard import parse

CLARA = """@clara: 1girl, young woman, 24 years old, short auburn hair, green eyes, no earrings
[001] solo, @clara[green shirt with number 10], entering a classroom
a
[002] solo, @clara, sitting at a desk
b
[003] solo, @clara, walking in a hallway
c
[004] solo, @clara[black suit], preparing for an interview
d
"""

# Lo que «ve» el etiquetador en cada color de imagen.
GOOD = {"green_eyes": 0.9, "brown_hair": 0.8, "short_hair": 0.8, "green_shirt": 0.85, "clothes_writing": 0.7}
SUIT = {"green_eyes": 0.9, "brown_hair": 0.8, "short_hair": 0.8, "black_suit": 0.8, "suit": 0.8}
WRONG = {"brown_eyes": 0.85, "brown_hair": 0.8, "short_hair": 0.8, "white_hoodie": 0.8}


def _img(tmp_path, name, color):
    path = tmp_path / f"{name}.png"
    Image.new("RGB", (200, 300), color).save(path)
    return path


def _tools(tags_by_color, diff=lambda a, b: 0.05):
    return co.Tools(
        detect=lambda im: [((0, 0, im.width, im.height), 0.9)],
        tag=lambda im: tags_by_color[im.getpixel((5, 5))],
        difference=diff,
        ocr=None,
    )


def _setup(tmp_path, colors):
    board = parse(CLARA)
    faces = tmp_path / "fichas"
    faces.mkdir()
    Image.new("RGB", (200, 300), (1, 1, 1)).save(faces / "clara.png")
    pics = [[_img(tmp_path, f"img{i}", c)] for i, c in enumerate(colors, 1)]
    return board, faces, pics


def _levels(rep, attribute):
    return [r.level for r in rep.results if r.attribute == attribute]


# 1. La ficha es la referencia, nunca la mayoría ------------------------------------------------

def test_1_sheet_is_reference_not_majority(tmp_path):
    wrong = (200, 0, 0)
    board, faces, pics = _setup(tmp_path, [wrong, wrong, wrong, wrong])
    reports = co.check(board, pics, faces, _tools({wrong: WRONG}))
    # Las 4 salen con ojos marrones: siguen siendo error aunque sean mayoría.
    assert all(_levels(r, "ojos") == [co.CONFIRMED] for r in reports)
    assert not hasattr(co, "outliers")


# 2. Rostro, ojos, pelo, edad, accesorios y ropa ----------------------------------------------------

def test_2_profile_and_compare_all_attributes():
    prof = co.profile_from("1boy, old man, 80 years old, clean-shaven, white hair neatly combed back, short hair, "
                           "grey eyes, glasses, no earrings, grey suit")
    assert prof.age == "old" and prof.facial_hair is False and prof.eyes == {"grey"}
    assert prof.hair_length == "short_hair" and "hair_slicked_back" in prof.hairstyles
    assert prof.accessories == {"glasses"} and prof.no_accessories == {"earrings"}
    assert prof.garments == {"suit": {"grey"}}
    seen = co.Seen({"grey_eyes": 0.9, "white_hair": 0.8, "long_hair": 0.7, "beard": 0.8, "earrings": 0.7,
                    "grey_suit": 0.8, "old_man": 0.6})
    res = {r.attribute: r for r in co.compare("aurelio", prof, seen)}
    assert res["ojos"].level == co.OK
    assert res["barba"].level == co.CONFIRMED  # la ficha dice afeitado
    assert res["largo de pelo"].level == co.CONFIRMED  # corto -> largo: se salta «medio»
    medium = co.compare("aurelio", co.profile_from("short hair"), co.Seen({"medium_hair": 0.9}))[0]
    assert medium.level == co.POSSIBLE  # corto -> medio: un paso, puede ser el dibujo
    assert res["peinado"].level == co.POSSIBLE  # no se ve peinado hacia atrás
    assert res["edad"].level == co.OK
    assert res["ropa"].level == co.OK
    acc = [r for r in co.compare("aurelio", prof, seen) if r.attribute == "accesorio"]
    assert {(r.expected, r.level) for r in acc} == {("glasses", co.POSSIBLE), ("sin earrings", co.CONFIRMED)}


def test_2_face_identity_thresholds():
    assert co.face_check("x", 0.05, "ficha", False).level == co.OK
    assert co.face_check("x", 0.2, "ficha", False).level == co.POSSIBLE
    assert co.face_check("x", 0.35, "ficha", False).level == co.CONFIRMED
    assert co.face_check("x", 0.35, "escena 002", False).level == co.POSSIBLE  # anterior: solo aviso


def test_2_age_contradiction():
    young = co.profile_from("1girl, 24 years old")
    assert co.compare("c", young, co.Seen({"old_woman": 0.8}))[0].level == co.CONFIRMED
    unknown = co.compare("c", young, co.Seen({}))[0]
    assert unknown.level == co.UNCHECKABLE and unknown.requires_review is False


# 3. Herencia de atributos hasta que el guion los cambie ----------------------------------------------

def test_3_inherited_outfit_is_expected():
    board = parse(CLARA)
    exp = [co.expected_for(board, s, "clara") for s in board.scenes]
    assert [sorted(e.garments) for e in exp] == [["shirt"], ["shirt"], ["shirt"], ["suit"]]
    assert [e.number for e in exp] == ["10", "10", "10", None]
    assert all(e.eyes == {"green"} for e in exp)  # los rasgos de la ficha no cambian con la ropa


def test_3_clara_example_flags_scene_003(tmp_path):
    good, wrong, suit = (0, 200, 0), (200, 0, 0), (0, 0, 0)
    board, faces, pics = _setup(tmp_path, [good, good, wrong, suit])
    reports = co.check(board, pics, faces, _tools({good: GOOD, wrong: WRONG, suit: SUIT}))
    by = {r.label: r for r in reports}
    assert _levels(by["003"], "ojos") == [co.CONFIRMED]
    assert _levels(by["003"], "ropa") == [co.CONFIRMED]  # sudadera blanca en vez de camisa verde
    assert _levels(by["004"], "ropa") == [co.OK]  # traje negro: el guion lo cambió
    assert _levels(by["002"], "ojos") == [co.OK] and _levels(by["002"], "ropa") == [co.OK]


# 4. Comparación con la ficha y con la aparición anterior ----------------------------------------------

def test_4_compares_with_sheet_and_previous_valid(tmp_path):
    good, other = (0, 200, 0), (0, 0, 200)
    board, faces, pics = _setup(tmp_path, [good, good, other, good])

    def diff(a, b):  # la imagen azul tiene otra cara
        return 0.4 if (0, 0, 200) in (a.getpixel((5, 5)), b.getpixel((5, 5))) else 0.05

    reports = co.check(board, pics, faces, _tools({good: GOOD, other: GOOD, (0, 0, 0): SUIT}, diff))
    by = {r.label: r for r in reports}
    faces_003 = {r.attribute: r.level for r in by["003"].results if r.attribute.startswith("cara")}
    assert faces_003 == {"cara (ficha)": co.CONFIRMED, "cara (escena 002)": co.POSSIBLE}
    # La 004 se compara con la última válida (002), no con la 003 que tenía la cara mal.
    assert any(r.attribute == "cara (escena 002)" for r in by["004"].results)


def test_4_previous_appearance_when_sheet_is_silent():
    exp = co.profile_from("1boy, young man")  # sin color de ojos en la ficha
    res = co.previous_check("d", exp, co.Seen({"red_eyes": 0.7}), ("002", co.Seen({"blue_eyes": 0.8})))
    assert [(r.attribute, r.level) for r in res] == [("ojos", co.POSSIBLE)]


# 5. Niveles, confianza y evidencias; nada correcto sin verificar -------------------------------------

def test_5_levels_confidence_and_unverifiable():
    prof = co.profile_from("1girl, green eyes, green shirt with number 10")
    res = {r.attribute: r for r in co.compare("c", prof, co.Seen({"green_shirt": 0.9}), hidden=True)}
    assert res["ojos"].level == co.UNCHECKABLE and res["ojos"].requires_review is False  # de espaldas
    assert res["número"].level == co.UNCHECKABLE and res["número"].requires_review is True  # sin OCR
    assert "OCR no disponible" in res["número"].evidence
    res = {r.attribute: r for r in co.compare("c", prof, co.Seen({}))}
    assert res["ojos"].level == co.UNCHECKABLE  # sin etiqueta: no se da por buena
    assert res["ropa"].level == co.UNCHECKABLE
    wrong = co.compare("c", prof, co.Seen({"red_eyes": 0.4}))[0]
    assert wrong.level == co.POSSIBLE and wrong.confidence == 0.4 and "red_eyes" in wrong.evidence


# 6. Informe estructurado por escena ------------------------------------------------------------------

def test_6_structured_report(tmp_path):
    good, wrong = (0, 200, 0), (200, 0, 0)
    board, faces, pics = _setup(tmp_path, [good, good, wrong, good])
    reports = co.check(board, pics, faces, _tools({good: GOOD, wrong: WRONG}))
    path = tmp_path / "revision" / "coherencia.json"
    co.write_report(reports, [], path)
    data = json.loads(path.read_text(encoding="utf-8"))
    img = next(i for i in data["images"] if i["label"] == "003")
    assert img["status"] == "ERROR" and img["image"] == "img3.png"
    keys = set(img["results"][0])
    assert {"character", "attribute", "expected", "detected", "level", "confidence", "evidence"} <= keys
    assert "[003] ERROR" in co.report_text(reports)


# 7. Bloqueo antes de montar, con aprobación y --forzar -------------------------------------------------

def test_7_gate_blocks_until_reviewed_and_approved(tmp_path):
    good, wrong = (0, 200, 0), (200, 0, 0)
    board, faces, pics = _setup(tmp_path, [good, good, wrong, good])
    folder = tmp_path / "revision"
    flat = [p for ps in pics for p in ps]
    assert co.blockers(folder / "coherencia.json", {}, flat) == ["no hay informe de coherencia: ejecuta «revisar»"]
    co.write_report(co.check(board, pics, faces, _tools({good: GOOD, wrong: WRONG})), [], folder / "coherencia.json")
    pending = co.blockers(folder / "coherencia.json", co.load_approvals(folder), flat)
    assert any("[003] ERROR" in p for p in pending)
    labels = [p.split("]")[0][1:] for p in pending]
    co.approve(folder, folder / "coherencia.json", labels)
    assert co.blockers(folder / "coherencia.json", co.load_approvals(folder), flat) == []
    regenerated = _img(tmp_path, "img3_nueva", wrong)
    assert "sin revisar" in co.blockers(folder / "coherencia.json", co.load_approvals(folder), [regenerated])[0]


def test_7_run_has_forzar_flag():
    import argparse
    from unittest import mock

    from mangavid import cli

    with mock.patch.object(cli, "cmd_run") as run:
        cli.main(["run", "historia.txt", "--forzar"])
    args = run.call_args[0][0]
    assert isinstance(args, argparse.Namespace) and args.forzar is True


# 8. Antes de producir: ficha, rostro, vestuario y miniatura ------------------------------------------------

def test_8_preflight(tmp_path):
    text = """@aurelio: 1boy, old man, 80 years old, clean-shaven, white hair, grey suit
@clara: 1girl, 24 years old, green eyes
@miniatura: 1boy, 1girl, @aurelio, @clara[pink pajamas]
[001] solo, @aurelio[black coat], street
a
[002] solo, @clara[green shirt with number 10], classroom
b
"""
    board = parse(text)
    faces = tmp_path / "fichas"
    faces.mkdir()
    Image.new("RGB", (100, 100), (9, 9, 9)).save(faces / "aurelio.png")  # falta clara.png
    pre = co.preflight(board, faces, tag=lambda im: {"beard": 0.9, "white_hair": 0.8, "old_man": 0.7})
    got = {(r.character, r.attribute, r.level) for r in pre}
    assert ("clara", "rostro de referencia", co.CONFIRMED) in got
    assert ("aurelio", "rostro vs ficha: barba", co.CONFIRMED) in got  # la ficha dice afeitado
    assert ("aurelio", "vestuario", co.CONFIRMED) in got  # traje en la ficha + abrigo en la escena
    assert ("clara", "miniatura", co.POSSIBLE) in got  # pijama que no sale en ninguna escena
    assert board.thumbnail.outfits["aurelio"] == "black coat"  # hereda su primera ropa
    without = co.preflight(board, faces, tag=None)
    assert ("aurelio", "rostro vs ficha", co.UNCHECKABLE) in {(r.character, r.attribute, r.level) for r in without}


# Regresiones de la auditoría del commit 7821192 -----------------------------------------------------

def _reviewed(tmp_path):
    good, wrong = (0, 200, 0), (200, 0, 0)
    board, faces, pics = _setup(tmp_path, [good, good, wrong, wrong])
    folder = tmp_path / "revision"
    co.write_report(co.check(board, pics, faces, _tools({good: GOOD, wrong: WRONG})), [], folder / "coherencia.json")
    return folder, [p for ps in pics for p in ps]


def test_regression_image_changed_after_report_is_blocked(tmp_path):
    folder, flat = _reviewed(tmp_path)
    image = flat[0]  # REVISAR: el número 10 no se puede verificar sin OCR
    co.approve(folder, folder / "coherencia.json", ["001"])
    assert co.blockers(folder / "coherencia.json", co.load_approvals(folder), [image]) == []
    Image.new("RGB", (200, 300), (0, 0, 255)).save(image)  # mismo nombre, otro contenido
    blocked = co.blockers(folder / "coherencia.json", co.load_approvals(folder), [image])
    assert blocked == ["[001] modificada después del informe: vuelve a ejecutar «revisar»"]


def test_regression_approval_is_per_file_and_content(tmp_path):
    folder, flat = _reviewed(tmp_path)
    co.approve(folder, folder / "coherencia.json", ["003"])
    pending = co.blockers(folder / "coherencia.json", co.load_approvals(folder), flat)
    assert not any("[003]" in p for p in pending)  # la aprobada pasa
    assert any("[004]" in p for p in pending)  # la otra con error sigue bloqueada
    # Retocar la imagen aprobada invalida la aprobación (y la revisión).
    Image.new("RGB", (200, 300), (9, 9, 9)).save(flat[2])
    pending = co.blockers(folder / "coherencia.json", co.load_approvals(folder), flat)
    assert any("[003] modificada" in p for p in pending)
    # Una aprobación del formato antiguo (solo el nombre) no vale.
    old = {flat[3].name: "004"}
    assert any("[004]" in p for p in co.blockers(folder / "coherencia.json", old, flat))


def test_regression_preflight_text_has_no_image_summary():
    pre = [co._r("clara", "peinado", "bob_cut", "-", co.POSSIBLE, 0.0, "bob_cut 0.00")]
    text = co.report_text([], pre)
    assert "Antes de producir" in text and "Coherencia:" not in text


def test_regression_people_count_ignores_expanded_sheets():
    from mangavid.review import _check_one, expected_people, scene_people_text

    board = parse("@d: 1boy, young man\n@c: 1girl, young woman\n[001] 1boy, 1girl, @c, @d, cafe\nX\n"
                  "[002] @c, @d, park\nY\n[003] solo, @c, street\nZ")
    s1, s2, s3 = board.scenes
    assert expected_people(s1.image) == 4  # el fallo: las fichas suman otro 1boy y 1girl
    assert expected_people(scene_people_text(s1)) == 2
    assert expected_people(scene_people_text(s3)) == 1
    three = lambda path: [((0, 0, 1, 1), "face", 0.9)] * 3  # noqa: E731
    # Con tres caras en una escena de dos: DUPLICADO (antes salía OK).
    assert _check_one(scene_people_text(s1), "001", "x", three, three, 2).status == "DUPLICADO"
    # Sin «1boy»/«solo», tantas personas como @personajes.
    assert _check_one(scene_people_text(s2), "002", "x", three, three, 2).status == "DUPLICADO"


def test_regression_duplicates_reach_the_gate(tmp_path):
    from mangavid.review import Check

    good = (0, 200, 0)
    board, faces, pics = _setup(tmp_path, [good, good, good, (0, 0, 0)])
    reports = co.check(board, pics, faces, _tools({good: GOOD, (0, 0, 0): SUIT}))
    checks = [Check("003", pics[2][0], 1, 2, 2, "DUPLICADO")]
    co.add_people_checks(reports, checks)
    rep = next(r for r in reports if r.label == "003")
    assert rep.status == "ERROR" and _levels(rep, "personas") == [co.CONFIRMED]
