"""Tesseract OCR wrapper for scanned/handwritten FIR images (bonus feature)."""
import logging

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract/Pillow unavailable — OCR endpoint will return 503.")


def extract_text(image_path: str, languages: str = "eng+guj+hin") -> tuple[str, float]:
    """Return (extracted_text, mean_confidence 0..1)."""
    if not TESSERACT_AVAILABLE:
        raise RuntimeError("OCR not available on this deployment")

    img = Image.open(image_path)
    try:
        data = pytesseract.image_to_data(img, lang=languages, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError:
        # Language packs missing — retry English only
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)

    words, confs = [], []
    for word, conf in zip(data["text"], data["conf"]):
        if word.strip():
            words.append(word)
            try:
                c = float(conf)
                if c >= 0:
                    confs.append(c)
            except (TypeError, ValueError):
                pass

    text = " ".join(words)
    confidence = round(sum(confs) / len(confs) / 100, 3) if confs else 0.0
    return text, confidence
