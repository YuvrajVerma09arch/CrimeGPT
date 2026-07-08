"""Build the persistent ChromaDB vector index for the legal corpus.

Reads the BNS/BNSS/BSA sections and landmark judgments loaded by
``legal_service`` and indexes them into two chroma collections
(``legal_sections`` and ``legal_judgments``).

chromadb is an OPTIONAL dependency: when it is not installed this module
prints a notice and returns ``{"skipped": True}`` — the application then
falls back to the pure-Python :class:`app.rag.retriever.KeywordRetriever`.

Usage:
    python -m app.rag.indexer [--force]
"""

from __future__ import annotations

import argparse
from typing import Any

from app.config import settings
from app.services import legal_service

COLLECTION_SECTIONS = "legal_sections"
COLLECTION_JUDGMENTS = "legal_judgments"
BATCH_SIZE = 100


def _add_in_batches(
    collection: Any,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """Add documents to a chroma collection in batches of ``BATCH_SIZE``.

    Prefers ``upsert`` (idempotent re-runs); falls back to ``add`` on older
    chromadb versions.
    """
    for start in range(0, len(ids), BATCH_SIZE):
        chunk = slice(start, start + BATCH_SIZE)
        batch = {
            "ids": ids[chunk],
            "documents": documents[chunk],
            "metadatas": metadatas[chunk],
        }
        if hasattr(collection, "upsert"):
            collection.upsert(**batch)
        else:  # pragma: no cover - legacy chromadb
            collection.add(**batch)


def build_index(force: bool = False) -> dict:
    """Build (or rebuild with ``force=True``) the two chroma collections.

    Returns a summary dict ``{"sections": n, "judgments": n}`` on success or
    ``{"skipped": True}`` when chromadb is not installed.
    """
    try:
        import chromadb
    except Exception:
        print(
            "chromadb is not installed — vector indexing skipped. "
            "The keyword retriever will be used instead."
        )
        return {"skipped": True}

    from app.rag.retriever import _embedding_function, reset_retriever_cache

    legal_service.load_corpus()
    sections = legal_service.all_sections()
    judgments = legal_service.all_judgments()

    client = chromadb.PersistentClient(path=settings.chroma_db_path)

    if force:
        for name in (COLLECTION_SECTIONS, COLLECTION_JUDGMENTS):
            try:
                client.delete_collection(name)
            except Exception:
                pass  # collection did not exist yet

    kwargs: dict[str, Any] = {}
    embedding_function = _embedding_function()
    if embedding_function is not None:
        kwargs["embedding_function"] = embedding_function

    sections_col = client.get_or_create_collection(COLLECTION_SECTIONS, **kwargs)
    judgments_col = client.get_or_create_collection(COLLECTION_JUDGMENTS, **kwargs)

    # -- sections -------------------------------------------------------------
    if sections:
        ids = [f"{s.get('act')}-{s.get('section')}" for s in sections]
        documents = [
            f"{s.get('title') or ''}. {s.get('text') or ''}" for s in sections
        ]
        metadatas = [
            {
                "act": str(s.get("act") or ""),
                "section": str(s.get("section") or ""),
                "title": str(s.get("title") or ""),
            }
            for s in sections
        ]
        _add_in_batches(sections_col, ids, documents, metadatas)

    # -- judgments --------------------------------------------------------------
    if judgments:
        ids = [f"judgment-{i}" for i in range(len(judgments))]
        documents = [
            f"{j.get('title') or ''}. {j.get('summary') or ''}" for j in judgments
        ]
        metadatas = [
            {
                "title": str(j.get("title") or ""),
                "court": str(j.get("court") or ""),
                "year": j.get("year") or 0,
            }
            for j in judgments
        ]
        _add_in_batches(judgments_col, ids, documents, metadatas)

    # Make a live process pick up the freshly built index.
    reset_retriever_cache()

    return {"sections": len(sections), "judgments": len(judgments)}


def main() -> None:
    """CLI entrypoint: ``python -m app.rag.indexer [--force]``."""
    parser = argparse.ArgumentParser(
        description="Index the CrimeGPT legal corpus into ChromaDB."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and rebuild the collections from scratch.",
    )
    args = parser.parse_args()
    summary = build_index(force=args.force)
    print(f"Index build summary: {summary}")


if __name__ == "__main__":
    main()
