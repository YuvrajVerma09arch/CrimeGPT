"""HTML → PDF export via WeasyPrint, with graceful DOCX-only fallback."""
import logging

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML  # noqa

    WEASYPRINT_AVAILABLE = True
except Exception:  # ImportError or missing system libs (pango/cairo)
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint unavailable — PDF export disabled, DOCX only.")

PDF_CSS = """
@page { size: A4; margin: 2cm 1.8cm; }
body  { font-family: 'Noto Sans', 'Noto Sans Gujarati', 'Noto Sans Devanagari', sans-serif;
        font-size: 11pt; color: #111; line-height: 1.55; }
h1    { font-size: 15pt; text-align: center; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 2px; }
h2    { font-size: 11pt; text-align: center; font-weight: normal;
        color: #444; margin-top: 0; }
hr    { border: none; border-top: 2px solid #222; margin: 10px 0 16px; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
td, th { border: 1px solid #999; padding: 5px 8px; font-size: 10.5pt; text-align: left; }
th    { background: #f0f0f0; }
.meta td:first-child { width: 34%; font-weight: bold; background: #fafafa; }
.body-text { text-align: justify; margin: 12px 0; }
.sign { margin-top: 48px; display: flex; justify-content: space-between; }
.sign div { text-align: center; width: 40%; border-top: 1px solid #333; padding-top: 6px; }
.footer { margin-top: 24px; font-size: 9pt; color: #666; text-align: center; }
"""


def html_to_pdf(html: str, pdf_path: str) -> bool:
    """Render HTML string to pdf_path. Returns False if PDF export unavailable."""
    if not WEASYPRINT_AVAILABLE:
        return False
    try:
        HTML(string=html).write_pdf(pdf_path)
        return True
    except Exception as exc:  # pragma: no cover - depends on system libs
        logger.error("PDF generation failed: %s", exc)
        return False
