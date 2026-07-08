"""Full narrative -> legal suggestions RAG pipeline (CLAUDE.md section 6).

Steps: translate to English if needed, extract crime entities, build a
retrieval query, retrieve candidate sections and judgments, re-rank with a
keyword boost, and map into the API response shape consumed by
``POST /api/v1/legal/suggest``.
"""

from __future__ import annotations

from app.rag.retriever import get_retriever, tokenize
from app.services import nlp_service, translation_service

ENTITY_KEYS = ("crime_types", "weapons", "persons", "locations", "dates")

MAX_SECTIONS = 6
MAX_JUDGMENTS = 4
MIN_SCORE = 0.05
KEYWORD_BOOST = 0.15
EXCERPT_CHARS = 220
SUMMARY_CHARS = 300


def rerank(results: list[dict], query_tokens: set[str]) -> list[dict]:
    """Re-rank retriever hits.

    Boosts an entry's score by +0.15 when any of its keywords/tags tokens
    overlap the query tokens (clamped to 1.0), sorts by score descending,
    and deduplicates by (act, section) — falling back to title for entries
    without a section (judgments).
    """
    boosted: list[dict] = []
    for entry in results:
        keyword_tokens: set[str] = set()
        for kw in entry.get("keywords") or entry.get("tags") or []:
            keyword_tokens.update(tokenize(str(kw)))

        score = float(entry.get("score") or 0.0)
        if keyword_tokens & query_tokens:
            score = min(score + KEYWORD_BOOST, 1.0)
        boosted.append({**entry, "score": score})

    boosted.sort(key=lambda e: e["score"], reverse=True)

    seen: set[tuple] = set()
    deduped: list[dict] = []
    for entry in boosted:
        if entry.get("section"):
            key = (entry.get("act"), entry.get("section"))
        else:
            key = ("__title__", entry.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _section_out(entry: dict) -> dict:
    """Map a corpus section entry to the pinned response dict."""
    return {
        "act": entry.get("act") or "",
        "section": str(entry.get("section") or ""),
        "title": entry.get("title") or "",
        "relevance_score": round(float(entry.get("score") or 0.0), 3),
        "excerpt": (entry.get("text") or "")[:EXCERPT_CHARS],
        "source": "AI_SUGGESTED",
    }


def _judgment_out(entry: dict) -> dict:
    """Map a corpus judgment entry to the pinned response dict."""
    return {
        "title": entry.get("title") or "",
        "court": entry.get("court") or "",
        "year": entry.get("year"),
        "summary": (entry.get("summary") or "")[:SUMMARY_CHARS],
        "relevance_score": round(float(entry.get("score") or 0.0), 3),
    }


async def suggest_legal_sections(narrative: str, lang: str = "en") -> dict:
    """Suggest BNS/BNSS/BSA sections and landmark judgments for a narrative.

    Returns::

        {
            "sections": [{act, section, title, relevance_score, excerpt, source}],
            "judgments": [{title, court, year, summary, relevance_score}],
            "entities": {crime_types, weapons, persons, locations, dates},
        }
    """
    # 1. Translate to English if needed.
    if lang != "en":
        narrative_en, _engine = await translation_service.translate(
            narrative, lang, "en"
        )
    else:
        narrative_en = narrative

    # 2. Extract crime entities.
    entities = nlp_service.extract_entities(narrative_en)
    entities_out = {key: list(entities.get(key) or []) for key in ENTITY_KEYS}

    # 3. Build the retrieval query from entities + raw narrative.
    entity_terms = entities_out["crime_types"] + entities_out["weapons"]
    query = (" ".join(entity_terms) + " " + narrative_en[:500]).strip()

    # 4. Retrieve candidates.
    retriever = get_retriever()
    sections_raw = retriever.query(query, "sections", 8)
    judgments_raw = retriever.query(query, "judgments", 4)

    # 5. Re-rank, threshold, and cap.
    query_tokens = set(tokenize(query))
    sections_ranked = [
        s for s in rerank(sections_raw, query_tokens) if s["score"] >= MIN_SCORE
    ][:MAX_SECTIONS]
    judgments_ranked = [
        j for j in rerank(judgments_raw, query_tokens) if j["score"] >= MIN_SCORE
    ][:MAX_JUDGMENTS]

    # 6. Map to the response shape.
    return {
        "sections": [_section_out(s) for s in sections_ranked],
        "judgments": [_judgment_out(j) for j in judgments_ranked],
        "entities": entities_out,
    }
