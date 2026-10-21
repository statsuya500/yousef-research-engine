"""Genera una imagen por escena con SDXL en la GPU, pensado para poca RAM.

Trabaja en dos fases para no tener nunca el modelo entero en RAM:
1) carga solo los codificadores de texto, codifica las escenas nuevas y guarda
   cada resultado en disco; 2) carga UNet + VAE en la GPU y dibuja.
Cada imagen se guarda con un hash de su descripción: si se corta, al relanzar
solo se generan las que faltan o las que han cambiado.
"""

from __future__ import annotations

import gc
import hashlib
import time
from pathlib import Path

from .storyboard import Scene, Storyboard

DEFAULT_MODEL = "cagliostrolab/animagine-xl-4.0"
FP16_VAE = "madebyollin/sdxl-vae-fp16-fix"
WIDTH, HEIGHT = 1344, 768  # 16:9 aproximado, tamaño nativo de SDXL
STEPS = 28
GUIDANCE = 5.0


def _key(prompt: str, negative: str, seed: int, model: str) -> str:
    return hashlib.sha1(f"{model}|{prompt}|{negative}|{seed}|{STEPS}|{GUIDANCE}".encode()).hexdigest()[:10]


def image_paths(board: Storyboard, workdir: Path, seed: int, model: str) -> list[Path]:
    return [
        workdir / f"img_{s.number:04d}_{_key(board.prompt(s), board.negative, seed + s.number, model)}.png"
        for s in board.scenes
    ]


def generate(board: Storyboard, workdir: Path, seed: int = 1234, model: str = DEFAULT_MODEL) -> list[Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    paths = image_paths(board, workdir, seed, model)
    todo = [(s, p) for s, p in zip(board.scenes, paths) if not p.exists()]
    print(f"[imágenes] {len(todo)} nuevas de {len(paths)}")
    if not todo:
        return paths

    import torch

    embed_paths = _encode(board, todo, workdir, model, torch)
    _draw(todo, embed_paths, seed, model, torch)
    return paths


def _encode(board: Storyboard, todo: list[tuple[Scene, Path]], workdir: Path, model: str, torch) -> list[Path]:
    from diffusers import StableDiffusionXLPipeline

    out = [p.with_suffix(".pt") for _, p in todo]
    missing = [(s, e) for (s, _), e in zip(todo, out) if not e.exists()]
    if not missing:
        return out
    t0 = time.time()
    pipe = StableDiffusionXLPipeline.from_pretrained(model, unet=None, vae=None, dtype=torch.float16).to("cuda")
    with torch.no_grad():
        for scene, path in missing:
            tensors = pipe.encode_prompt(
                prompt=board.prompt(scene),
                negative_prompt=board.negative,
                device="cuda",
                num_images_per_prompt=1,
                do_classifier_free_guidance=True,
            )
            torch.save([t.cpu() for t in tensors], path)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[imágenes] {len(missing)} descripciones codificadas en {time.time() - t0:.0f}s")
    return out


def _draw(todo: list[tuple[Scene, Path]], embed_paths: list[Path], seed: int, model: str, torch) -> None:
    from diffusers import AutoencoderKL, EulerAncestralDiscreteScheduler, StableDiffusionXLPipeline

    vae = AutoencoderKL.from_pretrained(FP16_VAE, dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model, vae=vae, text_encoder=None, text_encoder_2=None, tokenizer=None, tokenizer_2=None,
        dtype=torch.float16,
    ).to("cuda")
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.vae.enable_tiling()
    pipe.set_progress_bar_config(disable=True)

    t0 = time.time()
    for k, ((scene, path), embed) in enumerate(zip(todo, embed_paths), start=1):
        pos, neg, pooled, neg_pooled = (t.to("cuda") for t in torch.load(embed))
        image = pipe(
            prompt_embeds=pos,
            negative_prompt_embeds=neg,
            pooled_prompt_embeds=pooled,
            negative_pooled_prompt_embeds=neg_pooled,
            width=WIDTH,
            height=HEIGHT,
            num_inference_steps=STEPS,
            guidance_scale=GUIDANCE,
            generator=torch.Generator("cuda").manual_seed(seed + scene.number),
        ).images[0]
        image.save(path)
        embed.unlink()
        left = (time.time() - t0) / k * (len(todo) - k)
        print(f"[imágenes] {k}/{len(todo)} escena {scene.number:03d} (quedan ~{left / 60:.0f} min)", flush=True)
    del pipe
    gc.collect()
    torch.cuda.empty_cache()
