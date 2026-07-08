"""Keyword-scored search over the BNS/BNSS/BSA legal corpus and judgments.

The corpus lives as JSON files under ``backend/data`` and is loaded once
into module-level lists — no vector database required. This service is the
zero-dependency retrieval backbone that the RAG pipeline builds on.
"""
import json
import re
import threading
from pathlib import Path

# Resolves to backend/data regardless of the current working directory
DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"

_SECTION_FILES = ("bns_sections.json", "bnss_sections.json", "bsa_sections.json")

_sections: list[dict] = []
_judgments: list[dict] = []
_loaded = False
_lock = threading.Lock()


def _tokens(value: str) -> list[str]:
    return re.findall(r"\w+", value.lower())


def load_corpus() -> None:
    """Load legal sections and judgments into memory. Idempotent."""
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return

        sections: list[dict] = []
        for filename in _SECTION_FILES:
            path = DATA_DIR / "legal" / filename
            try:
                with path.open(encoding="utf-8") as fh:
                    sections.extend(json.load(fh))
            except FileNotFoundError:
                continue

        judgments: list[dict] = []
        try:
            with (DATA_DIR / "judgments" / "judgments.json").open(encoding="utf-8") as fh:
                judgments = json.load(fh)
        except FileNotFoundError:
            judgments = []

        _sections.extend(sections)
        _judgments.extend(judgments)
        _loaded = True


def all_sections() -> list[dict]:
    """Return every legal section in the corpus."""
    load_corpus()
    return list(_sections)


def all_judgments() -> list[dict]:
    """Return every landmark judgment in the corpus."""
    load_corpus()
    return list(_judgments)


def search_sections(q: str, act: str | None = None, limit: int = 20) -> list[dict]:
    """Tokenized case-insensitive keyword search over the section corpus.

    Scoring per query token: keyword hit = 3, title hit = 2, text hit = 1.
    An exact section-number match ranks first. Optionally filters by act.
    """
    load_corpus()
    query_tokens = _tokens(q)
    if not query_tokens:
        return []

    scored: list[tuple[int, dict]] = []
    for sec in _sections:
        if act and str(sec.get("act", "")).lower() != act.lower():
            continue

        keyword_tokens: set[str] = set()
        for kw in sec.get("keywords") or []:
            keyword_tokens.update(_tokens(kw))
        title_tokens = set(_tokens(sec.get("title") or ""))
        text_tokens = set(_tokens(sec.get("text") or ""))
        section_number = str(sec.get("section", "")).lower()

        score = 0
        for tok in query_tokens:
            if tok == section_number:
                score += 1000  # exact section-number match ranks first
            if tok in keyword_tokens:
                score += 3
            if tok in title_tokens:
                score += 2
            if tok in text_tokens:
                score += 1

        if score > 0:
            scored.append((score, sec))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [sec for _, sec in scored[:limit]]


def get_section(act: str, number: str) -> dict | None:
    """Return the section dict for an exact act + section number, or None."""
    load_corpus()
    for sec in _sections:
        if (
            str(sec.get("act", "")).lower() == act.lower()
            and str(sec.get("section", "")) == str(number).strip()
        ):
            return sec
    return None
