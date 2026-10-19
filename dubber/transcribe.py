"""Transcripción con faster-whisper."""

from __future__ import annotations

from pathlib import Path

from .segments import Segment

# Pista para que Whisper escriba chino simplificado con puntuación.
_PROMPTS = {"zh": "以下是普通话的句子，使用简体中文。"}


def _device() -> tuple[str, str]:
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe(audio: Path, language: str = "zh", model_size: str = "large-v3") -> list[Segment]:
    from faster_whisper import WhisperModel

    device, compute_type = _device()
    print(f"[whisper] modelo {model_size} en {device}")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(
        str(audio),
        language=language or None,
        vad_filter=True,
        initial_prompt=_PROMPTS.get(language),
    )
    result = [Segment(s.start, s.end, s.text.strip()) for s in segments if s.text.strip()]
    print(f"[whisper] {len(result)} segmentos")
    return result
