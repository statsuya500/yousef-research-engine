"""Traducción local con NLLB-200 (Meta), gratis y sin claves."""

from __future__ import annotations

from .segments import Segment

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"

LANG_CODES = {
    "zh": "zho_Hans",
    "es": "spa_Latn",
    "en": "eng_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "pt": "por_Latn",
}


def nllb_code(lang: str) -> str:
    return LANG_CODES.get(lang, lang)


def translate_segments(
    segments: list[Segment],
    src: str = "zh",
    tgt: str = "es",
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 16,
) -> list[Segment]:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[traducción] {model_name} en {device}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=nllb_code(src))
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device).eval()
    target_id = tokenizer.convert_tokens_to_ids(nllb_code(tgt))

    texts = [s.source for s in segments]
    outputs: list[str] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        enc = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=256)
        enc = enc.to(device)
        with torch.no_grad():
            generated = model.generate(
                **enc, forced_bos_token_id=target_id, max_length=256, num_beams=4
            )
        outputs += tokenizer.batch_decode(generated, skip_special_tokens=True)

    for seg, text in zip(segments, outputs):
        seg.text = text.strip()
    return segments
