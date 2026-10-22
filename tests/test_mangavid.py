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
    assert board.prompt(board.scenes[0]) == "1girl, solo, young woman, black hair, smiling, manhwa style"


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
