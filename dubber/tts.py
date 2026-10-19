"""Voz sintética con Edge-TTS (voces neuronales de Microsoft, gratis)."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from .segments import Segment

DEFAULT_VOICE = "es-ES-AlvaroNeural"


def _run_async(coro):
    """asyncio.run que también funciona dentro de Jupyter/Colab (bucle ya activo)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    box: dict = {}
    thread = threading.Thread(target=lambda: box.update(result=asyncio.run(coro)))
    thread.start()
    thread.join()
    return box.get("result")


def synthesize(
    segments: list[Segment],
    workdir: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    retries: int = 3,
    concurrency: int = 4,
) -> list[Path | None]:
    import edge_tts

    workdir.mkdir(parents=True, exist_ok=True)
    paths: list[Path | None] = [
        workdir / f"tts_{i:04d}.mp3" if s.text.strip() else None for i, s in enumerate(segments)
    ]
    async def one(text: str, path: Path, sem: asyncio.Semaphore) -> None:
        async with sem:
            for attempt in range(retries):
                try:
                    await edge_tts.Communicate(text, voice, rate=rate).save(str(path))
                    return
                except Exception:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2**attempt)

    async def all_jobs() -> None:
        sem = asyncio.Semaphore(concurrency)
        await asyncio.gather(
            *(one(s.text, p, sem) for s, p in zip(segments, paths) if p is not None)
        )

    print(f"[voz] {sum(p is not None for p in paths)} frases con {voice}")
    _run_async(all_jobs())
    return paths
