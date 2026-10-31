"""Validador de identidad y posición (mangavid/identidad.py), con imágenes y herramientas simuladas.

Cada persona es un bloque de color; el etiquetador falso responde según el color del recorte y la
diferencia CCIP falsa compara el color del rostro con el de cada referencia.
"""

from PIL import Image

from mangavid import continuidad as ct
from mangavid import identidad as idn

W, H = 1344, 400
CLARA, DANIEL, GHOST = (200, 190, 180), (90, 90, 95), (240, 240, 240)
MEZCLA = (205, 195, 185)  # ropa ambigua: jersey 0.60 frente a sudadera 0.55
TAGS = {CLARA: {"sweater": 0.9, "hoodie": 0.0}, DANIEL: {"sweater": 0.0, "hoodie": 0.85},
        GHOST: {}, MEZCLA: {"sweater": 0.6, "hoodie": 0.55}}


def _refs(tmp_path):
    Image.new("RGB", (50, 50), CLARA).save(tmp_path / "clara.png")
    Image.new("RGB", (50, 50), DANIEL).save(tmp_path / "daniel.png")
    return [idn.CharacterSpec("clara", ["sweater"], tmp_path / "clara.png", None, "izquierda"),
            idn.CharacterSpec("daniel", ["hoodie"], tmp_path / "daniel.png", None, "derecha")]


def _scene(tmp_path, people, faces, tags=None):
    """people: [(x0, x1, color de la ropa)]; faces: [(x0, x1, color del rostro)]."""
    img = Image.new("RGB", (W, H), (30, 120, 40))
    for x0, x1, c in people:
        img.paste(c, (x0, 100, x1, H))
    for x0, x1, c in faces:
        img.paste(c, (x0, 10, x1, 90))
    path = tmp_path / "escena.png"
    img.save(path)
    def tag(crop):
        # la ropa del recorte: el color de su parte baja
        return (tags or TAGS).get(crop.getpixel((crop.width // 2, crop.height - 5)), {})

    def difference(ref, face):
        return 0.05 if ref.getpixel((1, 1)) == face.getpixel((face.width // 2, face.height // 2)) else 0.35

    tools = idn.Tools(lambda im: [((x0, 0, x1, H), 0.9) for x0, x1, _ in people],
                      lambda im: [((x0, 10, x1, 90), 0.9) for x0, x1, _ in faces], tag, difference)
    return path, tools


def _status(report, who, attr):
    return [r.status for r in report.requirements if r.character == who and r.attribute == attr]


def test_correct_scene_needs_visual_review_never_valid(tmp_path):
    path, tools = _scene(tmp_path, [(100, 500, CLARA), (850, 1250, DANIEL)], [(200, 400, CLARA), (950, 1150, DANIEL)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "identificación por ropa") == [ct.PASS]
    assert _status(rep, "clara", "rostro frente a ropa") == [ct.PASS]
    assert _status(rep, "daniel", "posición") == [ct.PASS]
    assert not rep.crossed and not rep.retry_eligible
    assert ct.verdict(rep.requirements) == "NEEDS_VISUAL_REVIEW"
    assert _status(rep, "(escena)", "artefactos") == [ct.NOT_AUTO]


def test_crossed_identities_are_detected_and_retry_eligible(tmp_path):
    # Ropa en su lado, pero cada rostro es el del otro personaje (caso 301247).
    path, tools = _scene(tmp_path, [(100, 500, CLARA), (850, 1250, DANIEL)], [(200, 400, DANIEL), (950, 1150, CLARA)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "rostro frente a ropa") == [ct.FAIL]
    assert rep.crossed and rep.retry_eligible
    assert ct.verdict(rep.requirements) == "REJECTED"


def test_wrong_side_is_rejected_without_retry(tmp_path):
    # Identidades correctas pero Clara a la derecha: el guion la exige a la izquierda.
    path, tools = _scene(tmp_path, [(100, 500, DANIEL), (850, 1250, CLARA)], [(200, 400, DANIEL), (950, 1150, CLARA)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "rostro frente a ropa") == [ct.PASS]
    assert _status(rep, "clara", "posición") == [ct.FAIL]
    assert not rep.retry_eligible  # nunca se reintenta por posición
    assert ct.verdict(rep.requirements) == "REJECTED"


def test_centre_band_position_is_uncertain(tmp_path):
    path, tools = _scene(tmp_path, [(450, 840, CLARA), (900, 1300, DANIEL)], [(550, 750, CLARA), (1000, 1200, DANIEL)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "posición") == [ct.UNCERTAIN]  # centro x=645, a menos del 5 % del medio
    assert ct.verdict(rep.requirements) == "UNCERTAIN"


def test_ghost_face_is_rejected_and_not_retried(tmp_path):
    path, tools = _scene(tmp_path, [(100, 500, CLARA), (520, 700, GHOST), (850, 1250, DANIEL)],
                         [(200, 400, CLARA), (560, 680, CLARA), (950, 1150, CLARA)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "(escena)", "número de rostros") == [ct.FAIL]
    assert _status(rep, "(escena)", "número de personas") == [ct.FAIL]
    assert not rep.retry_eligible  # cruce presente, pero la escena no es fiable
    assert ct.verdict(rep.requirements) == "REJECTED"


def test_merged_people_and_missing_faces_are_uncertain(tmp_path):
    path, tools = _scene(tmp_path, [(100, 1250, CLARA)], [(200, 400, CLARA)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "(escena)", "número de personas") == [ct.UNCERTAIN]
    assert _status(rep, "(escena)", "número de rostros") == [ct.UNCERTAIN]
    assert _status(rep, "daniel", "identificación por ropa") == [ct.UNCERTAIN]
    assert ct.verdict(rep.requirements) == "UNCERTAIN"


def test_narrow_garment_margin_blocks_identification_and_retry(tmp_path):
    # Margen 0.6 frente a 0.55 (< 0.15): no se identifica a Clara aunque los rostros estén cruzados.
    path, tools = _scene(tmp_path, [(100, 500, MEZCLA), (850, 1250, DANIEL)], [(200, 400, DANIEL), (950, 1150, CLARA)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "identificación por ropa") == [ct.UNCERTAIN]
    assert not rep.retry_eligible
    assert ct.verdict(rep.requirements) in ("UNCERTAIN", "REJECTED")


def test_same_garment_on_both_people_is_uncertain(tmp_path):
    path, tools = _scene(tmp_path, [(100, 500, CLARA), (850, 1260, CLARA)], [(200, 400, CLARA), (950, 1150, DANIEL)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "identificación por ropa") == [ct.UNCERTAIN]
    assert "varias personas" in [r for r in rep.requirements if r.attribute == "identificación por ropa"][0].evidence


def test_person_without_face_is_uncertain(tmp_path):
    path, tools = _scene(tmp_path, [(100, 500, CLARA), (850, 1250, DANIEL)], [(950, 1150, DANIEL)])
    rep = idn.validate(path, _refs(tmp_path), tools)
    assert _status(rep, "clara", "rostro frente a ropa") == [ct.UNCERTAIN]


def test_mask_flip_name_and_order():
    import torch
    from mangavid import images

    job = images.Job("p", 1, images.Path("/x/img_0004_abc.png"), (1344, 768), [], None, 0.6)
    flipped = images.flipped(job)
    assert flipped.mask_flip and flipped.out.name == "img_0004_abc_inv.png"
    assert not job.mask_flip and job.out.name == "img_0004_abc.png"  # el original no cambia
    normal, inv = images._masks(2, 1344, 768)[0], images._masks(2, 1344, 768, flip=True)[0]
    assert torch.equal(inv[:, 0], normal[:, 1]) and torch.equal(inv[:, 1], normal[:, 0])


def test_scene_jobs_names_unchanged_without_flip(tmp_path):
    from mangavid import images
    from mangavid.storyboard import parse

    (tmp_path / "a.png").write_bytes(b"x")
    board = parse("@a: 1girl\n[001] solo, @a\nX")
    job = images.scene_jobs(board, tmp_path, tmp_path, 1234, "m")[0]
    assert job.mask_flip is False and "_inv" not in job.out.name


# --- Reintento en el bucle de continuidad ----------------------------------------------------------

STORY = """@clara: 1girl, young woman, grey eyes
@daniel: 1boy, young man, brown eyes

[001] solo, @daniel[grey hoodie], cafe
a
[002] solo, @clara[cream knit sweater], park
b
[004] 1boy, 1girl, @clara, @daniel, park bench
c
"""


def _loop(tmp_path, evaluations):
    from mangavid.storyboard import parse

    board = parse(STORY)
    portraits = tmp_path / "fichas"
    portraits.mkdir()
    for n in ("clara", "daniel"):
        Image.new("RGB", (8, 8), (1, 1, 1)).save(portraits / f"{n}.png")
    reg = {"personajes": {n: {"ficha": board.characters[n], "permanentes": {}, "ropa": [], "extra_prompt": "",
                              "detras_prompt": ""} for n in ("clara", "daniel")}}
    sspec = ct.SceneSpec(4, "park bench", ["clara", "daniel"], sides={"clara": "izquierda", "daniel": "derecha"})
    generated, written = [], []

    def generate(jobs):
        for j in jobs:
            j.out.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), (len(generated), 0, 0)).save(j.out)
            generated.append(j)

    calls = iter(evaluations)
    result, cands = ct.run_scene("@clara: 1girl\n@daniel: 1boy", board, sspec, reg, tmp_path / "c", portraits,
                                 batch_size=1, max_batches=2, model="m", generate=generate,
                                 evaluate_fn=lambda b, s, sp, p: next(calls), log=lambda *_: None,
                                 on_candidate=lambda cs: written.append(len(cs)))
    return result, cands, generated, written


CROSSED = [ct.Requirement("clara", "rostro frente a ropa", "", ct.FAIL, "cruzado"),
           ct.Requirement("(escena)", "cruce de identidades", "", ct.FAIL, "", True, retry=True)]
WRONG_SIDE = [ct.Requirement("clara", "posición", "izquierda", ct.FAIL, "derecha")]
UNSURE = [ct.Requirement("clara", "identificación por ropa", "", ct.UNCERTAIN, "")]
OK = [ct.Requirement("clara", "posición", "izquierda", ct.PASS, ""),
      ct.Requirement("(escena)", "artefactos", "", ct.NOT_AUTO, "")]


def test_crossed_gets_exactly_one_flipped_retry_validated_from_scratch(tmp_path):
    result, cands, generated, written = _loop(tmp_path, [CROSSED, OK])
    assert [j.mask_flip for j in generated] == [False, True]
    assert generated[1].out.name.endswith("_inv.png") and generated[1].seed == generated[0].seed
    assert cands[1].retry_of == cands[0].image and cands[1].mask_flip
    assert result.state == "CANDIDATE_NEEDS_VISUAL_REVIEW" and result.candidate == cands[1].image
    assert written == [1, 2]  # registro escrito tras cada imagen


def test_retry_with_wrong_side_is_rejected_and_not_retried_again(tmp_path):
    # El reintento arregla las identidades pero mueve a los personajes: se rechaza por posición.
    result, cands, generated, _ = _loop(tmp_path, [CROSSED, WRONG_SIDE, UNSURE])
    assert [j.mask_flip for j in generated] == [False, True, False]  # un reintento; el lote 2 es normal
    assert cands[1].verdict == "REJECTED" and cands[1].retry_of
    assert result.state == "NO_VALID_CANDIDATE"


def test_no_retry_for_wrong_side_or_uncertain(tmp_path):
    result, cands, generated, _ = _loop(tmp_path, [WRONG_SIDE, UNSURE])
    assert all(not j.mask_flip for j in generated) and len(generated) == 2
    assert result.state == "NO_VALID_CANDIDATE"


def test_identity_uses_outfit_changed_by_script(tmp_path):
    from mangavid.storyboard import parse

    board = parse("@clara: 1girl\n[001] solo, @clara[cream knit sweater], a\nx\n[002] solo, @clara[black suit], b\ny")
    reg = {"personajes": {"clara": {"ropa": [{"texto": "cream knit sweater", "desde_escena": 1},
                                             {"texto": "black suit", "desde_escena": 2}]}}}
    assert ct.outfit_at(reg, "clara", 2)["texto"] == "black suit"
    from mangavid import coherencia as co
    assert sorted(co.profile_from(ct.outfit_at(reg, "clara", 2)["texto"]).garments) == ["suit"]
    assert sorted(co.profile_from(ct.outfit_at(reg, "clara", 1)["texto"]).garments) == ["sweater"]
