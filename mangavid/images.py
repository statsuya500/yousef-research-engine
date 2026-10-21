"""Genera imágenes con SDXL en la GPU, pensado para poca RAM y 8 GB de VRAM.

Dos usos:
- Fichas de personaje: varias opciones de retrato por personaje para elegir una.
- Escenas: cada personaje que sale en la escena se dibuja con la cara de su ficha
  elegida (IP-Adapter Plus Face). Con varios personajes, cada uno ocupa su franja
  de la imagen, de izquierda a derecha en el orden en que aparecen en la escena.

Se trabaja por fases para no tener nunca todo el modelo cargado a la vez:
1) codificadores de texto -> 2) codificador de imagen (caras) -> 3) UNet + VAE.
Cada resultado se guarda con un hash de lo que lo produce: si se corta, al
relanzar solo se genera lo que falta o lo que ha cambiado.
"""

from __future__ import annotations

import gc
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from .storyboard import Scene, Storyboard

DEFAULT_MODEL = "cagliostrolab/animagine-xl-4.0"
FP16_VAE = "madebyollin/sdxl-vae-fp16-fix"
IP_ADAPTER = "h94/IP-Adapter"
IP_WEIGHTS = "ip-adapter-plus-face_sdxl_vit-h.safetensors"
IP_SCALE = 0.6  # cuánto se impone la cara de la ficha frente a la descripción
WIDTH, HEIGHT = 1344, 768  # 16:9 aproximado, tamaño nativo de SDXL
PORTRAIT = (896, 1152)  # fichas de personaje en vertical
STEPS = 28
GUIDANCE = 5.0
PORTRAIT_TAGS = "solo, portrait, upper body, looking at viewer, simple background, white background"


@dataclass
class Job:
    prompt: str
    seed: int
    out: Path
    size: tuple[int, int]
    faces: list[Path]  # fichas de los personajes que salen, en orden


def _hash(*parts: object) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:10]


def _file_hash(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:10]


# --- Fichas de personaje -----------------------------------------------------------

def portrait_jobs(board: Storyboard, folder: Path, options: int, seed: int) -> dict[str, list[Job]]:
    jobs = {}
    for k, (name, tags) in enumerate(board.characters.items()):
        prompt = ", ".join(p for p in (tags, PORTRAIT_TAGS, board.style) if p)
        jobs[name] = [
            Job(prompt, seed + 1000 * k + i, folder / f"{name}_{i}.png", PORTRAIT, [])
            for i in range(1, options + 1)
        ]
    return jobs


def chosen_portrait(folder: Path, name: str) -> Path:
    return folder / f"{name}.png"


# --- Escenas -----------------------------------------------------------------------

def scene_jobs(board: Storyboard, workdir: Path, portraits: Path, seed: int, model: str) -> list[Job]:
    jobs = []
    for s in board.scenes:
        faces = [chosen_portrait(portraits, c) for c in s.characters]
        missing = [f.name for f in faces if not f.exists()]
        if missing:
            raise SystemExit(
                f"Escena [{s.number:03d}]: falta la ficha {', '.join(missing)} en {portraits}. "
                "Ejecuta primero: python -m mangavid personajes <historia.txt>"
            )
        prompt = board.prompt(s)
        key = _hash(model, prompt, board.negative, seed + s.number, STEPS, GUIDANCE, IP_SCALE,
                    *(_file_hash(f) for f in faces))
        jobs.append(Job(prompt, seed + s.number, workdir / f"img_{s.number:04d}_{key}.png",
                        (WIDTH, HEIGHT), faces))
    return jobs


# --- Generación --------------------------------------------------------------------

def generate(jobs: list[Job], negative: str, model: str = DEFAULT_MODEL) -> None:
    todo = [j for j in jobs if not j.out.exists()]
    print(f"[imágenes] {len(todo)} nuevas de {len(jobs)}")
    if not todo:
        return
    import torch

    for j in todo:
        j.out.parent.mkdir(parents=True, exist_ok=True)
    text = _encode_texts(todo, negative, model, torch)
    faces = _encode_faces(todo, torch)
    _draw(todo, text, faces, model, torch)


def _free(torch) -> None:
    gc.collect()
    torch.cuda.empty_cache()


def _encode_texts(todo: list[Job], negative: str, model: str, torch) -> list[Path]:
    from diffusers import StableDiffusionXLPipeline

    paths = [j.out.with_suffix(".txt.pt") for j in todo]
    missing = [(j, p) for j, p in zip(todo, paths) if not p.exists()]
    if missing:
        t0 = time.time()
        pipe = StableDiffusionXLPipeline.from_pretrained(model, unet=None, vae=None, dtype=torch.float16).to("cuda")
        with torch.no_grad():
            for job, path in missing:
                tensors = pipe.encode_prompt(
                    prompt=job.prompt, negative_prompt=negative, device="cuda",
                    num_images_per_prompt=1, do_classifier_free_guidance=True,
                )
                torch.save([t.cpu() for t in tensors], path)
        del pipe
        _free(torch)
        print(f"[imágenes] {len(missing)} descripciones codificadas en {time.time() - t0:.0f}s")
    return paths


def _encode_faces(todo: list[Job], torch) -> dict[Path, object]:
    """Huella de cada ficha usada: [negativa, positiva] con forma (2, 257, 1280)."""
    refs = sorted({f for j in todo for f in j.faces})
    if not refs:
        return {}
    from PIL import Image
    from transformers import CLIPImageProcessor, CLIPVisionModelWithProjection

    processor = CLIPImageProcessor()
    encoder = CLIPVisionModelWithProjection.from_pretrained(
        IP_ADAPTER, subfolder="models/image_encoder", dtype=torch.float16
    ).to("cuda")
    out = {}
    with torch.no_grad():
        for ref in refs:
            pixels = processor(Image.open(ref).convert("RGB"), return_tensors="pt").pixel_values
            pixels = pixels.to("cuda", torch.float16)
            pos = encoder(pixels, output_hidden_states=True).hidden_states[-2]
            neg = encoder(torch.zeros_like(pixels), output_hidden_states=True).hidden_states[-2]
            out[ref] = torch.cat([neg, pos]).cpu()
    del encoder
    _free(torch)
    return out


def _masks(count: int, width: int, height: int):
    """Una franja vertical por personaje, de izquierda a derecha, que se solapan un poco."""
    from diffusers.image_processor import IPAdapterMaskProcessor
    from PIL import Image, ImageDraw

    images = []
    for i in range(count):
        mask = Image.new("L", (width, height), 0)
        left = max(0, int(width * i / count - width * 0.05))
        right = min(width, int(width * (i + 1) / count + width * 0.05))
        ImageDraw.Draw(mask).rectangle([left, 0, right, height], fill=255)
        images.append(mask)
    masks = IPAdapterMaskProcessor().preprocess(images, height=height, width=width)
    return [masks.reshape(1, count, masks.shape[-2], masks.shape[-1])]


def _draw(todo: list[Job], text: list[Path], faces: dict, model: str, torch) -> None:
    from diffusers import AutoencoderKL, EulerAncestralDiscreteScheduler, StableDiffusionXLPipeline

    vae = AutoencoderKL.from_pretrained(FP16_VAE, dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model, vae=vae, text_encoder=None, text_encoder_2=None, tokenizer=None, tokenizer_2=None,
        dtype=torch.float16,
    )
    use_faces = bool(faces)
    if use_faces:
        pipe.load_ip_adapter(IP_ADAPTER, subfolder="sdxl_models", weight_name=IP_WEIGHTS,
                             image_encoder_folder=None)
    pipe.to("cuda", torch.float16)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.vae.enable_tiling()
    pipe.set_progress_bar_config(disable=True)

    t0 = time.time()
    for k, (job, text_path) in enumerate(zip(todo, text), start=1):
        pos, neg, pooled, neg_pooled = (t.to("cuda") for t in torch.load(text_path))
        w, h = job.size
        extra = {}
        if use_faces:
            if job.faces:
                # (2, n, 257, 1280): negativas y positivas de los n personajes
                stack = torch.stack([faces[f] for f in job.faces], dim=1).to("cuda")
                pipe.set_ip_adapter_scale(IP_SCALE)
                extra["ip_adapter_image_embeds"] = [stack]
                if len(job.faces) > 1:
                    extra["cross_attention_kwargs"] = {"ip_adapter_masks": _masks(len(job.faces), w, h)}
            else:
                pipe.set_ip_adapter_scale(0.0)
                extra["ip_adapter_image_embeds"] = [torch.zeros(2, 1, 257, 1280, dtype=torch.float16,
                                                                device="cuda")]
        image = pipe(
            prompt_embeds=pos, negative_prompt_embeds=neg,
            pooled_prompt_embeds=pooled, negative_pooled_prompt_embeds=neg_pooled,
            width=w, height=h, num_inference_steps=STEPS, guidance_scale=GUIDANCE,
            generator=torch.Generator("cuda").manual_seed(job.seed), **extra,
        ).images[0]
        image.save(job.out)
        text_path.unlink()
        left = (time.time() - t0) / k * (len(todo) - k)
        print(f"[imágenes] {k}/{len(todo)} {job.out.name[:20]} (quedan ~{left / 60:.0f} min)", flush=True)
    del pipe
    _free(torch)
