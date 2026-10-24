import pytest

from mangavid.storyboard import parse

STORY = """
# comentario
@estilo: manhwa style
@negativo: lowres
@ana: young woman, black hair

[001] 1girl, solo, @ana, smiling
Ana sonrió.
Y se fue.

[002] city, night
La ciudad dormía.
"""


def test_parse_storyboard():
    board = parse(STORY)
    assert board.negative == "lowres"
    assert [s.number for s in board.scenes] == [1, 2]
    assert board.scenes[0].narration == "Ana sonrió. Y se fue."
    # la acción va delante de los rasgos del personaje
    assert board.prompt(board.scenes[0]) == "1girl, solo, smiling, young woman, black hair, manhwa style"


def test_unknown_character_fails():
    with pytest.raises(ValueError, match="@luis"):
        parse("[001] @luis\nHola")


def test_duplicate_scene_fails():
    with pytest.raises(ValueError, match="repetida"):
        parse("[001] a\nHola\n[001] b\nAdiós")


def test_expected_people():
    from mangavid.review import expected_people

    assert expected_people("1boy, 1girl, hugging") == 2
    assert expected_people("1boy, solo, sad") == 1
    assert expected_people("2boys, fighting") == 2
    assert expected_people("city at night, no humans") == 0
    assert expected_people("close-up of hands, no face") == 0
    assert expected_people("crowd of villagers, square") is None


def test_derived_characters():
    board = parse("@a: young man, black hair\n@a5: @a, stubble\n[001] 1boy, solo, @a5\nHola\n[002] x, {semilla=2}\nAdiós")
    assert board.characters["a5"] == "young man, black hair, stubble"
    assert board.bases == {"a5": "a"}
    assert board.scenes[0].characters == ["a5"]
    assert board.scenes[1].reroll == 2 and "{semilla" not in board.scenes[1].image


def test_negative_solo_only_for_solo_scenes():
    board = parse("@negativo: lowres\n@negativo_solo: 2boys, clone\n[001] 1boy, solo, sad\nA\n[002] 1boy, 1girl\nB")
    assert board.negative_for(board.scenes[0]) == "lowres, 2boys, clone"
    assert board.negative_for(board.scenes[1]) == "lowres"


def test_avoid_per_scene():
    board = parse("@negativo: lowres\n[001] 1boy, solo, sad, {evitar=clone, 2boys}, {semilla=2}\nA\n[002] city\nB")
    s = board.scenes[0]
    assert s.avoid == "clone, 2boys" and s.reroll == 2 and "{" not in s.image
    assert board.negative_for(s) == "lowres, clone, 2boys"
    assert board.negative_for(board.scenes[1]) == "lowres"


def test_likeness_and_cast_order():
    board = parse("@a: young man\n@b: young woman\n@parecido: 0.4\n[001] 1boy, 1girl, @b, @a, hug\nX")
    assert board.likeness == 0.4
    assert board.prompt(board.scenes[0]) == "1boy, 1girl, hug, young woman, young man"


def test_outfit_and_scene_likeness():
    board = parse("@a: young man\n@b: young woman\n[001] 1boy, 1girl, @a[overalls], @b[white dress], {parecido=0.6}\nX")
    s = board.scenes[0]
    assert s.characters == ["a", "b"] and s.likeness == 0.6
    assert board.prompt(s) == "1boy, 1girl, young man, overalls, young woman, white dress"


def test_shots_per_scene(tmp_path):
    from mangavid import images

    board = parse("@planos: 3\n" + STORY)
    assert board.shots == 3
    (tmp_path / "ana.png").write_bytes(b"cara")
    shots = images.scene_shots(board, tmp_path, tmp_path, 1234, "modelo")
    assert [len(js) for js in shots] == [3, 3]
    first, second, third = shots[0]
    # el plano principal no cambia al añadir planos: se reutiliza la imagen ya generada
    single = images.scene_shots(parse(STORY), tmp_path, tmp_path, 1234, "modelo")[0][0]
    assert first.out == single.out and first.prompt == single.prompt
    assert second.prompt.startswith("close-up, ") and second.out.name.startswith("img_0001_1_")
    assert len({first.seed, second.seed, third.seed}) == 3
    assert images.scene_jobs(board, tmp_path, tmp_path, 1234, "modelo")[1] == shots[1][0]
