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
