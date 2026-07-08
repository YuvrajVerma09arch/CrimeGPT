"""Language detection and translation with graceful engine fallback.

Engine order for :func:`translate`:

1. IndicTrans2 microservice (``settings.translation_service_url``)
2. Google Cloud Translation v2 REST (``settings.google_translate_api_key``)
3. Passthrough — return the input text unchanged

Every network engine is wrapped in try/except so the platform keeps working
completely offline.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


def detect_language(text: str) -> str:
    """Detect gu / hi / en via unicode block counting.

    Gujarati: U+0A80–U+0AFF, Devanagari (Hindi): U+0900–U+097F,
    everything else defaults to English (Latin letters).
    """
    gujarati = sum(1 for ch in text if 0x0A80 <= ord(ch) <= 0x0AFF)
    devanagari = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x097F)
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())

    counts = {"gu": gujarati, "hi": devanagari, "en": latin}
    best = max(counts, key=lambda lang: counts[lang])
    return best if counts[best] > 0 else "en"


async def translate(text: str, source: str, target: str) -> tuple[str, str]:
    """Translate ``text`` from ``source`` to ``target`` language.

    Returns ``(translated_text, engine)`` where engine is one of
    ``indictrans2``, ``google`` or ``passthrough``. Never raises — any
    engine failure falls through to the next, ending at passthrough.
    """
    if not text or not text.strip() or source == target:
        logger.debug("translate: passthrough (empty text or source == target)")
        return text, "passthrough"

    # 1. IndicTrans2 microservice
    if settings.translation_service_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    settings.translation_service_url.rstrip("/") + "/translate",
                    json={"text": text, "source": source, "target": target},
                )
                resp.raise_for_status()
                translated = resp.json()["translated"]
                logger.debug("translate: served by indictrans2 microservice")
                return translated, "indictrans2"
        except Exception as exc:
            logger.debug("translate: indictrans2 unavailable (%s), falling back", exc)

    # 2. Google Cloud Translation v2 REST
    if settings.google_translate_api_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    _GOOGLE_TRANSLATE_URL,
                    params={
                        "key": settings.google_translate_api_key,
                        "q": text,
                        "source": source,
                        "target": target,
                        "format": "text",
                    },
                )
                resp.raise_for_status()
                translated = resp.json()["data"]["translations"][0]["translatedText"]
                logger.debug("translate: served by google translate")
                return translated, "google"
        except Exception as exc:
            logger.debug("translate: google unavailable (%s), falling back", exc)

    # 3. Passthrough
    logger.debug("translate: passthrough (no engine available)")
    return text, "passthrough"
