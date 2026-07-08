"""Retrieval layer for the CrimeGPT RAG legal-intelligence pipeline.

Provides two interchangeable retrievers behind a common interface:

* :class:`KeywordRetriever` — a dependency-free TF-IDF-ish keyword scorer over
  the in-memory legal corpus loaded by ``legal_service``. Always available.
* :class:`ChromaRetriever` — semantic search over a persistent ChromaDB index
  built by ``app.rag.indexer``. Used automatically when chromadb is installed
  and both collections have been indexed.

Use :func:`get_retriever` to obtain the best available retriever.
"""

from __future__ import annotations

import math
import re
from typing import Any

from app.config import settings
from app.services import legal_service

# Chroma collection names (shared with app.rag.indexer).
COLLECTION_SECTIONS = "legal_sections"
COLLECTION_JUDGMENTS = "legal_judgments"

# Small inline English stopword set — enough to keep keyword scoring sane
# without pulling in any NLP dependency.
STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "any", "are", "as", "at", "be", "been", "but", "by",
        "did", "do", "does", "for", "from", "had", "has", "have", "he", "her",
        "him", "his", "i", "if", "in", "into", "is", "it", "its", "may", "me",
        "my", "no", "not", "of", "on", "or", "our", "shall", "she", "so",
        "some", "such", "than", "that", "the", "their", "them", "then",
        "there", "these", "they", "this", "those", "to", "up", "upon", "was",
        "we", "were", "when", "where", "which", "while", "who", "whoever",
        "whom", "will", "with", "would", "you", "your",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords and 1-char tokens."""
    return [
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) > 1 and tok not in STOPWORDS
    ]


class BaseRetriever:
    """Common retriever interface."""

    def query(self, text: str, collection: str, k: int = 8) -> list[dict]:
        """Return up to ``k`` corpus entries for ``collection`` ("sections" or
        "judgments"), each augmented with a ``score`` float in 0..1."""
        raise NotImplementedError


class KeywordRetriever(BaseRetriever):
    """Pure-Python TF-IDF-ish scoring over the in-memory legal corpus.

    Deterministic and dependency-free. The index is built lazily per
    collection on first query.
    """

    def __init__(self) -> None:
        self._indexes: dict[str, dict[str, Any]] = {}

    # -- index construction -------------------------------------------------

    def _entries_for(self, collection: str) -> tuple[list[dict], str, str]:
        """Return (entries, text_field, keywords_field) for a collection."""
        legal_service.load_corpus()
        if collection == "sections":
            return legal_service.all_sections(), "text", "keywords"
        if collection == "judgments":
            return legal_service.all_judgments(), "summary", "tags"
        raise ValueError(f"Unknown collection: {collection!r}")

    def _get_index(self, collection: str) -> dict[str, Any]:
        """Build (once) and return the inverted index for a collection."""
        index = self._indexes.get(collection)
        if index is not None:
            return index

        entries, text_field, kw_field = self._entries_for(collection)
        token_sets: list[set[str]] = []
        kw_sets: list[set[str]] = []
        df: dict[str, int] = {}

        for entry in entries:
            body = f"{entry.get('title') or ''} {entry.get(text_field) or ''}"
            tokens = set(tokenize(body))
            kw_tokens: set[str] = set()
            for kw in entry.get(kw_field) or []:
                kw_tokens.update(tokenize(str(kw)))
            tokens |= kw_tokens
            token_sets.append(tokens)
            kw_sets.append(kw_tokens)
            for tok in tokens:
                df[tok] = df.get(tok, 0) + 1

        n_docs = max(len(entries), 1)
        idf = {
            tok: math.log((n_docs + 1) / (count + 1)) + 1.0
            for tok, count in df.items()
        }

        index = {
            "entries": entries,
            "token_sets": token_sets,
            "kw_sets": kw_sets,
            "idf": idf,
        }
        self._indexes[collection] = index
        return index

    # -- querying ------------------------------------------------------------

    def query(self, text: str, collection: str, k: int = 8) -> list[dict]:
        """Score entries by idf overlap (+0.5*idf keyword bonus), normalize 0..1."""
        index = self._get_index(collection)
        query_tokens = set(tokenize(text))
        if not query_tokens:
            return []

        idf: dict[str, float] = index["idf"]
        scored: list[tuple[float, int, dict]] = []
        for pos, entry in enumerate(index["entries"]):
            overlap = query_tokens & index["token_sets"][pos]
            if not overlap:
                continue
            score = sum(idf.get(tok, 0.0) for tok in overlap)
            score += 0.5 * sum(
                idf.get(tok, 0.0)
                for tok in query_tokens & index["kw_sets"][pos]
            )
            if score > 0.0:
                scored.append((score, pos, entry))

        # Deterministic ordering: score desc, then original corpus position.
        scored.sort(key=lambda item: (-item[0], item[1]))
        top = scored[:k]
        if not top:
            return []

        max_score = top[0][0] or 1.0
        return [
            {**entry, "score": raw / max_score}
            for raw, _pos, entry in top
        ]


class ChromaRetriever(BaseRetriever):
    """Semantic retrieval over the persistent ChromaDB index."""

    _COLLECTION_MAP = {
        "sections": COLLECTION_SECTIONS,
        "judgments": COLLECTION_JUDGMENTS,
    }

    def __init__(self) -> None:
        import chromadb  # guarded: only instantiated when chromadb exists

        self._client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self._embedding_function = _embedding_function()
        self._collections: dict[str, Any] = {}

    def _get_collection(self, collection: str):
        name = self._COLLECTION_MAP.get(collection)
        if name is None:
            raise ValueError(f"Unknown collection: {collection!r}")
        cached = self._collections.get(name)
        if cached is not None:
            return cached
        kwargs: dict[str, Any] = {}
        if self._embedding_function is not None:
            kwargs["embedding_function"] = self._embedding_function
        col = self._client.get_collection(name, **kwargs)
        self._collections[name] = col
        return col

    @staticmethod
    def _strip_title_prefix(document: str, title: str) -> str:
        """Recover the body text from an indexed 'title. text' document."""
        prefix = f"{title}. "
        if title and document.startswith(prefix):
            return document[len(prefix):]
        return document

    def _to_corpus_entry(self, collection: str, meta: dict, document: str) -> dict:
        """Map a chroma hit back to a corpus-shaped dict, enriching from the
        in-memory corpus when possible (to recover keywords/tags/full text)."""
        legal_service.load_corpus()
        if collection == "sections":
            act = str(meta.get("act") or "")
            section = str(meta.get("section") or "")
            full = legal_service.get_section(act, section)
            if full:
                return dict(full)
            title = str(meta.get("title") or "")
            return {
                "act": act,
                "section": section,
                "title": title,
                "text": self._strip_title_prefix(document or "", title),
                "keywords": [],
            }
        title = str(meta.get("title") or "")
        for judgment in legal_service.all_judgments():
            if judgment.get("title") == title:
                return dict(judgment)
        return {
            "title": title,
            "court": meta.get("court") or "",
            "year": meta.get("year"),
            "summary": self._strip_title_prefix(document or "", title),
            "tags": [],
        }

    def query(self, text: str, collection: str, k: int = 8) -> list[dict]:
        """Vector-search a collection; score = 1 / (1 + distance)."""
        col = self._get_collection(collection)
        res = col.query(query_texts=[text], n_results=k)
        metas = (res.get("metadatas") or [[]])[0] or []
        docs = (res.get("documents") or [[]])[0] or []
        dists = (res.get("distances") or [[]])[0] or []

        results: list[dict] = []
        for i, meta in enumerate(metas):
            document = docs[i] if i < len(docs) else ""
            distance = float(dists[i]) if i < len(dists) else 0.0
            entry = self._to_corpus_entry(collection, meta or {}, document)
            entry["score"] = 1.0 / (1.0 + max(distance, 0.0))
            results.append(entry)
        return results


def _embedding_function():
    """Pick the chroma embedding function: OpenAI if a key is configured and
    the client can be built, else None (chroma's default). Never raises."""
    if not settings.openai_api_key:
        return None
    try:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name="text-embedding-3-small",
        )
    except Exception:
        return None


_retriever: BaseRetriever | None = None


def get_retriever() -> BaseRetriever:
    """Return the best available retriever (cached module-level).

    Uses :class:`ChromaRetriever` when chromadb imports cleanly and both
    ``legal_sections`` and ``legal_judgments`` collections exist with at
    least one document each; otherwise falls back to :class:`KeywordRetriever`.
    """
    global _retriever
    if _retriever is not None:
        return _retriever

    try:
        import chromadb

        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        for name in (COLLECTION_SECTIONS, COLLECTION_JUDGMENTS):
            if client.get_collection(name).count() <= 0:
                raise RuntimeError(f"Collection {name} is empty")
        _retriever = ChromaRetriever()
    except Exception:
        _retriever = KeywordRetriever()
    return _retriever


def reset_retriever_cache() -> None:
    """Clear the cached retriever (used by tests and after re-indexing)."""
    global _retriever
    _retriever = None
