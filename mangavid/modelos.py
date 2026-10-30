"""Descarga de una vez todos los modelos que usa mangavid, para trabajar después sin conexión
(HF_HUB_OFFLINE=1).

    python -m mangavid modelos                       # Animagine + caras + detectores
    python -m mangavid modelos --model John6666/wai-nsfw-illustrious-sdxl-v150-sdxl   # otro modelo más
"""

from __future__ import annotations

import os
import time

from . import images

# Estilo «cine anime» que se probó con buenos resultados.
WAI_MODEL = "John6666/wai-nsfw-illustrious-sdxl-v150-sdxl"


def plan(models: list[str]) -> list[tuple[str, str]]:
    """(qué, repositorio) en el orden en que se descargan."""
    steps = [(f"Modelo de imagen {m}", m) for m in dict.fromkeys(models)]
    steps += [
        ("VAE fp16", images.FP16_VAE),
        ("IP-Adapter Plus Face (caras de las fichas)", images.IP_ADAPTER),
        ("Detectores anime de imgutils (caras, cabezas, personas, etiquetas, parecido)", "deepghs"),
    ]
    return steps


def _download_pipeline(repo: str) -> None:
    from diffusers import DiffusionPipeline

    DiffusionPipeline.download(repo)


def _download_vae() -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(images.FP16_VAE, allow_patterns=["config.json", "diffusion_pytorch_model.safetensors"])


def _download_ip_adapter() -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(images.IP_ADAPTER, allow_patterns=[
        f"sdxl_models/{images.IP_WEIGHTS}",
        "models/image_encoder/config.json",
        "models/image_encoder/model.safetensors",
    ])


def _download_detectors() -> None:
    """imgutils baja cada detector la primera vez que se usa: se usan todos con una imagen vacía."""
    from PIL import Image

    from imgutils.detect import detect_faces, detect_heads, detect_person
    from imgutils.metrics import ccip_difference
    from imgutils.tagging import get_wd14_tags

    blank = Image.new("RGB", (512, 512), (200, 200, 200))
    detect_faces(blank)
    detect_heads(blank)
    detect_person(blank)
    get_wd14_tags(blank)
    ccip_difference(blank, blank)


def download(models: list[str], runner=None) -> list[tuple[str, str, str]]:
    """Descarga todo y devuelve (qué, repositorio, «ok» o el error) por paso."""
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        raise SystemExit("Quita HF_HUB_OFFLINE=1 para descargar: ejecuta «unset HF_HUB_OFFLINE» y repite.")
    actions = {images.FP16_VAE: _download_vae, images.IP_ADAPTER: _download_ip_adapter,
               "deepghs": _download_detectors}
    results = []
    for k, (what, repo) in enumerate(plan(models), start=1):
        print(f"[modelos] {k}/{len(plan(models))} {what}…", flush=True)
        t0 = time.time()
        action = actions.get(repo) or (lambda r=repo: _download_pipeline(r))
        try:
            (runner or (lambda f: f()))(action)
            status = "ok"
        except Exception as e:  # sigue con el resto y lo cuenta al final
            status = f"falló: {e}"
        print(f"[modelos]    {status} ({time.time() - t0:.0f}s)", flush=True)
        results.append((what, repo, status))
    failed = [r for r in results if r[2] != "ok"]
    if failed:
        print(f"[modelos] {len(failed)} descargas fallaron; vuelve a lanzar el comando para reintentarlas.")
    else:
        print("[modelos] todo descargado. A partir de ahora usa HF_HUB_OFFLINE=1 delante de cada comando.")
    return results
