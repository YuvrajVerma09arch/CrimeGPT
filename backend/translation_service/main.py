"""CrimeGPT translation microservice — standalone FastAPI app on port 8001.

Contract (consumed by the main backend's translation_service):
    POST /translate  {text, source, target}  ->  {translated, engine}
    GET  /health                             ->  {status, engine}

Engine ladder, resolved once at startup with guarded imports:

    1. IndicTrans2 (AI4Bharat) via HuggingFace transformers — best quality
       gu/hi <-> en. HEAVY: first run downloads ~2GB of model weights and
       inference needs several GB of RAM, so its dependencies are commented
       out in requirements.txt. Uncomment them (torch, transformers,
       IndicTransToolkit) to enable.
    2. deep-translator GoogleTranslator — lightweight online fallback.
    3. Passthrough — returns the input text unchanged (fully offline).

Run with:  uvicorn main:app --host 0.0.0.0 --port 8001
"""
import logging

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("translation_service")

# IndicTrans2 / FLORES language tags for the languages CrimeGPT supports.
LANG_TAGS = {"en": "eng_Latn", "hi": "hin_Deva", "gu": "guj_Gujr"}


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------
class IndicTrans2Engine:
    """AI4Bharat IndicTrans2 via transformers (distilled 200M checkpoints).

    NOTE: downloading both direction checkpoints is a ~2GB one-time cost and
    the models stay resident in RAM. Requires the commented-out heavy lines
    in requirements.txt (torch, transformers, IndicTransToolkit).
    """

    name = "indictrans2"

    _MODELS = {
        "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
        "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
    }

    def __init__(self) -> None:
        import torch  # noqa: F401 — heavy optional dependency
        from IndicTransToolkit.processor import IndicProcessor
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._torch = torch
        self._processor = IndicProcessor(inference=True)
        self._pairs = {}
        for direction, checkpoint in self._MODELS.items():
            logger.info("Loading IndicTrans2 checkpoint %s ...", checkpoint)
            tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, trust_remote_code=True)
            model.eval()
            self._pairs[direction] = (tokenizer, model)

    def _translate_one(self, text: str, source: str, target: str) -> str:
        direction = "en-indic" if source == "en" else "indic-en"
        tokenizer, model = self._pairs[direction]
        src_tag, tgt_tag = LANG_TAGS[source], LANG_TAGS[target]

        batch = self._processor.preprocess_batch([text], src_lang=src_tag, tgt_lang=tgt_tag)
        inputs = tokenizer(batch, truncation=True, padding="longest", return_tensors="pt")
        with self._torch.no_grad():
            tokens = model.generate(**inputs, num_beams=5, max_length=512)
        decoded = tokenizer.batch_decode(
            tokens, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        return self._processor.postprocess_batch(decoded, lang=tgt_tag)[0]

    def translate(self, text: str, source: str, target: str) -> str:
        # Indic <-> Indic (gu <-> hi) is not a single model direction; pivot
        # through English.
        if source != "en" and target != "en":
            english = self._translate_one(text, source, "en")
            return self._translate_one(english, "en", target)
        return self._translate_one(text, source, target)


class GoogleEngine:
    """deep-translator GoogleTranslator — free web endpoint, needs internet."""

    name = "google"

    def __init__(self) -> None:
        from deep_translator import GoogleTranslator

        self._translator_cls = GoogleTranslator

    def translate(self, text: str, source: str, target: str) -> str:
        return self._translator_cls(source=source, target=target).translate(text)


class PassthroughEngine:
    """No-op engine so the platform keeps working fully offline."""

    name = "passthrough"

    def translate(self, text: str, source: str, target: str) -> str:
        return text


def _resolve_engine():
    """Instantiate the best available engine, falling down the ladder."""
    for factory in (IndicTrans2Engine, GoogleEngine):
        try:
            engine = factory()
            logger.info("Translation engine: %s", engine.name)
            return engine
        except Exception as exc:  # noqa: BLE001 — missing dep, download error, ...
            logger.info("%s unavailable (%s) — falling back", factory.name, exc)
    logger.warning("No translation engine available — running in passthrough mode")
    return PassthroughEngine()


_engine = _resolve_engine()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
class TranslateRequest(BaseModel):
    text: str
    source: str = Field(pattern="^(gu|hi|en)$")
    target: str = Field(pattern="^(gu|hi|en)$")


class TranslateResponse(BaseModel):
    translated: str
    engine: str


app = FastAPI(
    title="CrimeGPT Translation Service",
    version="1.0.0",
    description="Gujarati / Hindi / English translation microservice.",
)


# Sync endpoint on purpose: FastAPI runs it in a threadpool so heavy model
# inference never blocks the event loop.
@app.post("/translate", response_model=TranslateResponse)
def translate(payload: TranslateRequest) -> TranslateResponse:
    if not payload.text.strip() or payload.source == payload.target:
        return TranslateResponse(translated=payload.text, engine="passthrough")
    try:
        translated = _engine.translate(payload.text, payload.source, payload.target)
        return TranslateResponse(translated=translated, engine=_engine.name)
    except Exception:  # noqa: BLE001 — never 500 on a translation failure
        logger.exception("Translation failed — returning passthrough")
        return TranslateResponse(translated=payload.text, engine="passthrough")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": _engine.name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
