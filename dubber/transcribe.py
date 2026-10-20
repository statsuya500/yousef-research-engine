"""Transcripción con faster-whisper."""

from __future__ import annotations

import ctypes
import glob
import os
from pathlib import Path

from .segments import Segment

# Pista para que Whisper escriba chino simplificado con puntuación.
_PROMPTS = {"zh": "以下是普通话的句子，使用简体中文。"}


def _preload_cuda_libs() -> None:
    """faster-whisper necesita cuBLAS y cuDNN. Si no están en el sistema (típico en WSL),
    carga los que vienen con los paquetes pip de NVIDIA que instala PyTorch."""
    try:
        import nvidia
    except ImportError:
        return
    libs = []
    for base in nvidia.__path__:
        for pattern in ("**/libcublas*.so.*", "**/libcudnn*.so.*"):
            libs += sorted(glob.glob(os.path.join(base, pattern), recursive=True))
    # Dos pasadas: algunas librerías de cuDNN dependen de otras.
    for _ in range(2):
        for lib in libs:
            try:
                ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass


def _has_cuda() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def _run(audio: Path, language: str, model_size: str, device: str) -> list[Segment]:
    from faster_whisper import WhisperModel

    compute_type = "float16" if device == "cuda" else "int8"
    print(f"[whisper] modelo {model_size} en {device}")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(
        str(audio),
        language=language or None,
        vad_filter=True,
        initial_prompt=_PROMPTS.get(language),
    )
    # La transcripción ocurre al recorrer el generador, así que los fallos de CUDA saltan aquí.
    return [Segment(s.start, s.end, s.text.strip()) for s in segments if s.text.strip()]


def transcribe(audio: Path, language: str = "zh", model_size: str = "large-v3") -> list[Segment]:
    _preload_cuda_libs()
    if _has_cuda():
        try:
            result = _run(audio, language, model_size, "cuda")
        except (RuntimeError, OSError) as e:
            print(f"[whisper] la GPU falló ({e}); sigo con el procesador, irá más lento")
            result = _run(audio, language, model_size, "cpu")
    else:
        result = _run(audio, language, model_size, "cpu")
    print(f"[whisper] {len(result)} segmentos")
    return result
