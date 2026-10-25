"""Sistema automático de continuidad: registro, evaluación, correcciones y bucle, sin modelos.

Las «imágenes» son bloques de color: cada persona es un rectángulo de un color, el detector
devuelve esos rectángulos y el etiquetador falso responde según el color del recorte.
"""

from PIL import Image

from mangavid import coherencia as co
from mangavid import continuidad as ct
from mangavid.review import Check
from mangavid.storyboard import parse

STORY = """@clara: 1girl, young woman, 24 years old, short auburn bob hair, grey eyes
@daniel: 1boy, young man, 25 years old, dark brown wavy hair, brown eyes

[001] solo, @daniel[grey hoodie], cafe
a
[002] solo, @clara[cream knit sweater], park
b
[003] 1boy, 1girl, @clara, @daniel, cafe
c
[004] 1boy, 1girl, @clara, @daniel, park bench
d
[005] solo, @clara[black suit], office
e
"""
HEADER = STORY.split("\n[001]")[0]

GREY_EYES = (99, 77, 80)  # iris gris de Clara (tono ~350°)
CREAM = (198, 194, 190)
HOODIE = (150, 141, 134)
BROWN = (85, 64, 51)
WHITE_HOODIE = (225, 225, 228)


def _tools(tags_by_color, diff=None):
    def color(im):
        return im.getpixel((im.width // 2, im.height // 2))

    return co.Tools(
        detect=lambda im: [(b, 0.9) for b in getattr(im, "people", [(0, 0, im.width, im.height)])],
        tag=lambda im: tags_by_color.get(color(im), {}),
        difference=diff or (lambda a, b: 0.05 if color(a) == color(b) else 0.4),
        faces=lambda im: [((0, 0, im.width, im.height // 2), 0.9)],
    )


def _registry(tmp_path, tools, refs=None, spec=None):
    board = parse(STORY)
    portraits = tmp_path / "fichas"
    portraits.mkdir(exist_ok=True)
    Image.new("RGB", (200, 300), GREY_EYES).save(portraits / "clara.png")
    Image.new("RGB", (200, 300), BROWN).save(portraits / "daniel.png")
    images = {}
    for n, c in (refs or {1: HOODIE, 2: CREAM}).items():
        images[n] = tmp_path / f"ref{n}.png"
        Image.new("RGB", (200, 300), c).save(images[n])
    return board, portraits, ct.build_registry(board, portraits, images, set(images), spec or {}, tools)


# --- Registro y continuidad -----------------------------------------------------------------

def test_registry_independent_sheets_and_continuity(tmp_path):
    board, _, reg = _registry(tmp_path, _tools({}))
    clara, daniel = reg["personajes"]["clara"], reg["personajes"]["daniel"]
    assert clara["permanentes"]["ojos"]["esperado"] == ["grey"]
    assert daniel["permanentes"]["ojos"]["esperado"] == ["brown"]  # cada ficha la suya
    assert "ojos" in clara["permanentes"] and clara["permanentes"]["ojos"]["medida"]["hue"] > 300
    # Continuidad: la ropa se hereda hasta que el guion la cambia (escena 005).
    assert ct.outfit_at(reg, "clara", 3)["texto"] == "cream knit sweater"
    assert ct.outfit_at(reg, "clara", 4)["desde_escena"] == 2
    assert ct.outfit_at(reg, "clara", 5)["texto"] == "black suit"
    assert ct.outfit_at(reg, "daniel", 4)["texto"] == "grey hoodie"
    # El color de la ropa sale de su escena de referencia.
    assert ct.outfit_at(reg, "clara", 3)["medida"]["rgb"] == list(CREAM)
    assert ct.outfit_at(reg, "clara", 5).get("medida") is None  # la 005 no es referencia


def test_scene_line_keeps_each_character_in_its_bracket(tmp_path):
    spec = {"personajes": {"daniel": {"prompt": "medium dark brown wavy hair covering the ears"}}}
    board, _, reg = _registry(tmp_path, _tools({}), spec=spec)
    sspec = ct.scene_spec(board, 3, {})
    line = ct.scene_line(sspec, reg, ct.Plan(), 7, board)
    clara_part = line.split("@clara[")[1].split("]")[0]
    daniel_part = line.split("@daniel[")[1].split("]")[0]
    assert "cream knit sweater" in clara_part and "covering the ears" not in clara_part
    assert "grey hoodie" in daniel_part and "covering the ears" in daniel_part
    assert "the girl on the left" in line and "{semilla=7}" in line
    assert parse(HEADER + "\n\n" + line + "\nx").scenes[0].characters == ["clara", "daniel"]


# --- Evaluación --------------------------------------------------------------------------------

def _scene_image(tmp_path, name, colors):
    """Una persona por color, de izquierda a derecha."""
    img = Image.new("RGB", (200 * len(colors), 300), (250, 250, 250))
    for i, c in enumerate(colors):
        img.paste(c, (200 * i, 0, 200 * (i + 1), 300))
    path = tmp_path / f"{name}.png"
    img.save(path)
    return path


def _evaluate(tmp_path, colors, tags, number=2, people_status="OK", diff=None):
    tools = _tools(tags, diff)
    board, portraits, reg = _registry(tmp_path, tools)
    path = _scene_image(tmp_path, f"cand{number}", colors)
    scene = board.scenes[number - 1]
    people = lambda s, p: Check("x", p, len(s.characters), len(colors), len(colors), people_status)  # noqa: E731
    real_open = Image.open

    def detect(im):  # una caja por persona
        return [((200 * i, 0, 200 * (i + 1), 300), 0.9) for i in range(len(colors))]

    tools.detect = detect
    reqs = ct.evaluate(board, scene, ct.scene_spec(board, number, {}), path, reg, portraits, tools, people)
    assert Image.open is real_open
    return {(r.character, r.attribute): r for r in reqs}, reqs


CLARA_OK = {"grey_eyes": 0.8, "brown_hair": 0.8, "short_hair": 0.8, "sweater": 0.8, "white_sweater": 0.7}


def test_clara_correct_is_valid_when_both_sources_agree(tmp_path):
    # Clara: el mismo color en su ficha y en la escena -> iris y ropa coinciden con la referencia.
    reg_colors = {GREY_EYES: CLARA_OK}
    res, reqs = _evaluate(tmp_path, [GREY_EYES], reg_colors)
    assert res[("clara", "identidad")].status == ct.PASS
    assert res[("clara", "ojos")].status == ct.PASS


def test_eye_color_change_is_detected(tmp_path):
    res, reqs = _evaluate(tmp_path, [BROWN], {BROWN: {"brown_eyes": 0.8, "brown_hair": 0.8}},
                          diff=lambda a, b: 0.05)
    assert res[("clara", "ojos")].status == ct.FAIL
    assert ct.verdict(reqs) == "REJECTED"


def test_wrong_clothing_is_detected(tmp_path):
    res, reqs = _evaluate(tmp_path, [WHITE_HOODIE], {WHITE_HOODIE: {"grey_eyes": 0.8, "white_hoodie": 0.8}},
                          diff=lambda a, b: 0.05)
    # Sudadera en vez de jersey: FAIL aunque el color (blanco ≈ crema) se parezca a la referencia,
    # porque prenda y color son requisitos distintos.
    assert res[("clara", "prenda")].status == ct.FAIL
    assert ct.verdict(reqs) == "REJECTED"


def test_different_hair_is_detected(tmp_path):
    black = (20, 20, 20)
    res, _ = _evaluate(tmp_path, [black], {black: {"black_hair": 0.8, "grey_eyes": 0.8}}, diff=lambda a, b: 0.05)
    assert res[("clara", "color de pelo")].status == ct.FAIL


def test_duplicates_and_absent_or_extra_characters(tmp_path):
    res, reqs = _evaluate(tmp_path, [GREY_EYES, GREY_EYES], {GREY_EYES: CLARA_OK}, people_status="DUPLICADO")
    assert res[("(escena)", "personas")].status == ct.FAIL
    assert res[("clara", "clon")].status == ct.FAIL  # la otra persona tiene su cara
    # Escena 003 sin Daniel: la segunda persona no aparece.
    res, reqs = _evaluate(tmp_path, [GREY_EYES], {GREY_EYES: CLARA_OK}, number=3,
                          diff=lambda a, b: 0.05 if a.getpixel((1, 1)) == GREY_EYES else 0.4)
    assert res[("daniel", "presencia")].status == ct.FAIL
    assert ct.verdict(reqs) == "REJECTED"


def test_uncertain_blocks_and_not_visible_does_not(tmp_path):
    reqs = [ct.Requirement("clara", "ojos", "grey", ct.PASS, ""),
            ct.Requirement("daniel", "ojos", "no visibles", ct.NA, "de espaldas", False)]
    assert ct.verdict(reqs) == "VALID"
    reqs.append(ct.Requirement("clara", "ropa", "cream", ct.UNCERTAIN, "fuentes en desacuerdo"))
    assert ct.verdict(reqs) == "UNCERTAIN"
    assert ct.combine(ct.PASS, ct.UNCERTAIN) == ct.UNCERTAIN  # una herramienta sola no basta
    assert ct.combine(ct.FAIL, ct.PASS) == ct.UNCERTAIN  # se contradicen
    assert ct.combine(ct.FAIL, ct.UNCERTAIN) == ct.FAIL


def test_outfit_change_authorised_by_script(tmp_path):
    suit = (15, 15, 15)
    tools = _tools({})
    board, portraits, reg = _registry(tmp_path, tools, refs={1: HOODIE, 2: CREAM, 5: suit})
    assert ct.outfit_at(reg, "clara", 5)["texto"] == "black suit"
    assert ct.outfit_at(reg, "clara", 5)["medida"]["rgb"] == list(suit)
    assert ct.outfit_at(reg, "clara", 4)["texto"] == "cream knit sweater"  # antes del cambio, no


# --- Correcciones y estrategias ---------------------------------------------------------------

def test_targeted_correction_does_not_contradict_other_character(tmp_path):
    board, _, reg = _registry(tmp_path, _tools({}))
    sspec = ct.scene_spec(board, 3, {})
    failed = [ct.Requirement("clara", "ojos", "grey", ct.FAIL, "")]
    plan = ct.correct(ct.Plan(), failed, reg, sspec)
    assert any("grey eyes" in e for e in plan.emphasis["clara"])
    assert "brown eyes" not in plan.avoid  # Daniel está en la escena y tiene ojos marrones
    assert "red eyes" in plan.avoid
    assert "daniel" not in plan.emphasis  # no se toca lo que no falló
    assert plan.likeness is None and plan.composition == []
    clone = ct.correct(plan, [ct.Requirement("clara", "clon", "", ct.FAIL, "")], reg, sspec)
    assert clone.likeness > ct.co_default_likeness() and "clone" in clone.avoid
    assert clone.emphasis == plan.emphasis  # lo que ya estaba bien se conserva


def _loop(tmp_path, verdicts, max_batches=10, fail_gen=None):
    """verdicts(batch, reroll) -> lista de requisitos de esa candidata."""
    tools = _tools({})
    board, portraits, reg = _registry(tmp_path, tools)
    sspec = ct.scene_spec(board, 3, {})
    work = tmp_path / "continuidad"
    calls = []

    def generate(jobs):
        if fail_gen:
            raise fail_gen
        for j in jobs:
            j.out.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), (1, 2, 3)).save(j.out)
        calls.append(len(jobs))

    seen = []

    def evaluate(b, scene, s, path):
        seen.append(b.scenes[0])
        return verdicts(len(calls), scene.reroll)

    result, cands = ct.run_scene(HEADER, board, sspec, reg, work, portraits, batch_size=4, max_batches=max_batches,
                                 model="m", generate=generate, evaluate_fn=evaluate, log=lambda *_: None)
    return result, cands, calls, seen, work


def _bad(attr="ojos", who="clara"):
    return [ct.Requirement(who, attr, "x", ct.FAIL, "")]


def test_retries_until_valid_candidate(tmp_path):
    ok = [ct.Requirement("clara", "ojos", "grey", ct.PASS, "")]
    result, cands, calls, seen, work = _loop(tmp_path, lambda batch, reroll: ok if (batch, reroll) == (2, 6) else _bad())
    assert result.state == "VALID_CANDIDATE" and result.batches == 2
    assert calls == [4, 4] and len(cands) == 8
    assert result.candidate.endswith(".png") and "/continuidad/003/" in result.candidate
    # Las semillas son reproducibles y distintas: 1-4 el primer lote, 5-8 el segundo.
    assert [s.reroll for s in seen] == list(range(1, 9))
    # El segundo lote lleva la corrección dirigida del primero (ojos de Clara).
    assert "grey irises" in seen[4].image and "grey irises" not in seen[0].image


def test_stops_at_limit_with_no_valid_candidate(tmp_path):
    result, cands, calls, _, _ = _loop(tmp_path, lambda b, r: _bad(), max_batches=3)
    assert result.state == "NO_VALID_CANDIDATE" and result.batches == 3 and len(calls) == 3
    assert result.unmet["clara ojos"] == 12 and len(cands) == 12


def test_repeated_same_failure_switches_strategy(tmp_path):
    result, _, _, seen, _ = _loop(tmp_path, lambda b, r: _bad(), max_batches=4)
    assert any("estrategia «secundarios de espaldas»" in n for n in result.corrections)
    last = seen[-1]
    assert last.characters == ["clara"] and "seen from behind" in last.image  # Daniel sin referencia facial


def test_gpu_out_of_memory_stops_and_keeps_results(tmp_path):
    result, cands, _, _, _ = _loop(tmp_path, lambda b, r: _bad(), fail_gen=RuntimeError("CUDA out of memory"))
    assert result.state == "GPU_ERROR" and cands == []


# --- Protección de archivos ------------------------------------------------------------------------

def test_original_images_are_protected(tmp_path):
    originals = [tmp_path / "img_0001_x.png", tmp_path / "img_0002_y.png"]
    for p in originals:
        Image.new("RGB", (4, 4), (9, 9, 9)).save(p)
    before = ct.snapshot(originals)
    result, cands, _, _, work = _loop(tmp_path, lambda b, r: _bad(), max_batches=1)
    assert ct.protected_changed(before) == []
    assert all(str(work) in c.image for c in cands)  # las candidatas solo van a su carpeta
    Image.new("RGB", (4, 4), (0, 0, 0)).save(originals[0])
    assert ct.protected_changed(before) == [str(originals[0])]


# --- Regresiones de la prueba controlada 003/004 ----------------------------------------------------

def test_regression_A_collar_tshirt_is_a_detail_not_a_second_garment():
    prof = co.profile_from("grey hoodie, light warm grey hoodie with long sleeves, hood down, "
                           "white t-shirt visible at the collar")
    assert prof.garments == {"hoodie": {"grey"}}
    assert prof.details == {"shirt": {"white"}}
    res = co.compare("daniel", prof, co.Seen({"hoodie": 0.82, "grey_hoodie": 0.5}))
    levels = {r.attribute: (r.level, r.requires_review) for r in res}
    assert levels["ropa"] == (co.OK, False)  # antes: «hoodie 0.82, ningún shirt» -> CONFIRMED
    assert levels["detalle de ropa"] == (co.UNCHECKABLE, False)
    assert not any(r.level == co.CONFIRMED for r in res)
    # Si el etiquetador sí la ve, el detalle queda verificado.
    res = co.compare("daniel", prof, co.Seen({"hoodie": 0.8, "white_shirt": 0.5}))
    assert {r.attribute: r.level for r in res}["detalle de ropa"] == co.OK


def test_regression_B_hair_correction_touches_only_hair(tmp_path):
    board, _, reg = _registry(tmp_path, _tools({}))  # Clara sin especificación propia
    sspec = ct.scene_spec(board, 3, {})
    plan = ct.Plan()
    for _ in range(3):  # el mismo fallo en tres lotes
        plan = ct.correct(plan, [ct.Requirement("clara", "color de pelo", "brown", ct.FAIL, "")], reg, sspec)
    assert plan.emphasis["clara"] == ["short auburn bob hair"]  # solo la frase del pelo, una vez
    line = ct.scene_line(sspec, reg, plan, 1, board)
    clara = line.split("@clara[")[1].split("]")[0]
    assert "24 years old" not in clara and "1girl" not in clara and "young woman" not in clara
    # La frase ya está en su ficha: el corchete no la repite (el generador ya pone la ficha).
    assert clara == "cream knit sweater"
    prompt = parse(HEADER + "\n\n" + line + "\nx").scenes[0]
    assert prompt.image.count("short auburn bob hair") == 1


def test_regression_B_final_prompt_is_not_truncated():
    class Tok:  # 1 token por palabra, más inicio y fin
        def __call__(self, text):
            from types import SimpleNamespace
            return SimpleNamespace(input_ids=[0] + text.replace(",", " ").split() + [0])

    short = ", ".join(["grey eyes"] * 10)
    tokens, chunks, truncated = ct.prompt_check(short, Tok())
    assert tokens == 20 and chunks == 1 and truncated is False
    long_prompt = ", ".join(f"tag{i} word" for i in range(60))  # 120 tokens: 2 trozos, sin cortar
    tokens, chunks, truncated = ct.prompt_check(long_prompt, Tok())
    assert chunks == 2 and truncated is False
    assert ct.prompt_check(" ".join(["w"] * 80), Tok())[2] is True  # una etiqueta de 80 tokens sí se corta


def test_regression_C_strategy_switches_when_a_problem_persists_with_varying_failures(tmp_path):
    varying = [
        [ct.Requirement("daniel", "prenda", "x", ct.FAIL, ""), ct.Requirement("clara", "ojos", "x", ct.UNCERTAIN, "")],
        [ct.Requirement("daniel", "prenda", "x", ct.FAIL, ""), ct.Requirement("(escena)", "estilo", "x", ct.UNCERTAIN, "")],
    ]
    result, _, _, seen, _ = _loop(tmp_path, lambda b, r: varying[(b - 1) % 2], max_batches=3)
    assert any("estrategia «secundarios de espaldas»" in n and "daniel" in n for n in result.corrections)
    assert seen[0].characters == ["clara", "daniel"]  # lote 1: referencias por región
    assert seen[-1].characters == ["clara"]  # lote 3: Daniel de espaldas sin referencia facial
    assert ct.persistent_failures([frozenset({("a", "x"), ("b", "y")}), frozenset({("a", "x")})], 2) == {("a", "x")}
    assert ct.persistent_failures([frozenset({("a", "x")}), frozenset({("b", "y")})], 2) == frozenset()


def test_reevaluate_only_reads_saved_candidates(tmp_path):
    tools = _tools({})
    board, portraits, reg = _registry(tmp_path, tools)
    sspec = ct.scene_spec(board, 3, {})
    folder = tmp_path / "continuidad"
    (folder / "003").mkdir(parents=True)
    known, unknown = folder / "003" / "img_0003_a.png", folder / "003" / "img_0003_b.png"
    for p in (known, unknown):
        Image.new("RGB", (8, 8), (5, 5, 5)).save(p)
    before = ct.snapshot([known, unknown])
    line = ct.scene_line(sspec, reg, ct.Plan(), 7, board)
    previous = {str(known): {"line": line, "batch": 2, "strategy": "referencias por región", "reroll": 7,
                             "prompt": "p", "negative": "n", "seed": 1241, "likeness": 0.6, "model": "m"}}
    ok = [ct.Requirement("clara", "ojos", "grey", ct.PASS, "")]
    cands = ct.reevaluate(HEADER, board, sspec, reg, folder, lambda b, s, sp, p: ok, previous)
    by = {c.image: c for c in cands}
    assert by[str(known)].reroll == 7 and by[str(known)].batch == 2 and by[str(known)].verdict == "VALID"
    assert by[str(unknown)].strategy.startswith("línea reconstruida") and by[str(unknown)].reroll == -1
    assert ct.protected_changed(before) == []  # leer y evaluar no cambia las imágenes
    ranked = sorted([ct.Candidate(3, 1, "s", 1, "", "", "", 0, 0.6, "m", "a", "", "REJECTED",
                                  [ct.Requirement("c", "x", "", ct.FAIL, "")]), by[str(known)]], key=ct.score)
    assert ranked[0] is by[str(known)]
