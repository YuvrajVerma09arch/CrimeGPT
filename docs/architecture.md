# CrimeGPT Architecture

## System Overview

CrimeGPT is a monorepo with a React frontend, a FastAPI backend, and an optional
translation microservice. In production everything sits behind nginx, which serves
the built frontend statically and reverse-proxies `/api/` to the backend.

```
                        +---------------------+
                        |   Browser (React)   |
                        +----------+----------+
                                   |
                                   v
                        +---------------------+
                        |        nginx        |
                        |  / -> static dist   |
                        |  /api/ -> backend   |
                        +----------+----------+
                                   |
                                   v
                        +---------------------+
                        |   FastAPI backend   |
                        |  (uvicorn, async)   |
                        +--+-----+-----+---+--+
                           |     |     |   |
              +------------+     |     |   +-------------------+
              v                  v     v                       v
    +----------------+  +-----------+ +---------+  +----------------------+
    |  PostgreSQL /  |  | ChromaDB  | |  Redis  |  | Translation service  |
    |  SQLite (dev)  |  | (vectors) | | (celery)|  | (IndicTrans/Google)  |
    +----------------+  +-----------+ +---------+  +----------------------+
```

Every external dependency beyond the relational database is optional; the backend
degrades gracefully when a component is absent (see matrix below).

## RAG Pipeline (legal suggestions)

`POST /legal/suggest` runs a four-stage pipeline over the narrative:

```
narrative (gu|hi|en)
   |
   v
1. TRANSLATE  -> normalize to English (translation service -> Google API -> passthrough)
   |
   v
2. NER        -> extract entities: crime_types, weapons, persons, locations, dates
   |             (spaCy if installed, else regex/keyword fallback)
   v
3. RETRIEVE   -> query ChromaDB over BNS/BNSS/BSA sections + judgments corpus
   |             (fallback: keyword scoring over backend/data/legal/*.json)
   v
4. RERANK     -> combine vector similarity + keyword overlap + entity boosts,
                 return top sections with relevance_score, excerpt, source
                 plus matching landmark judgments
```

The corpus lives in `backend/data/legal/` (BNS, BNSS, BSA sections and the
IPC->BNS crossref) and `backend/data/judgments/judgments.json`.

## Document Engine

`POST /cases/{id}/documents/generate`:

```
Case (with persons, items, sections, diary, IO)
   |
   v
build_context(case)  -- one flat dict of template variables (case pool)
   |
   +--> docxtpl + Jinja2 templates  -> .docx  (always available)
   |
   +--> Jinja2 HTML + WeasyPrint    -> .pdf   (skipped when WeasyPrint missing;
                                               pdf_path stays NULL, download
                                               returns 404 for format=pdf)
   |
   v
Document row (doc_type, version auto-incremented per case+type, paths)
```

Seven document types are supported (FIR, arrest memo, seizure memo, etc. — see
`backend/app/schemas/document.py: DOC_TYPES`). Generation is synchronous by
default; when `use_celery` is enabled the same job is dispatched to a Celery
worker and the response carries the task id.

## Audit Trail

- SQLAlchemy `after_flush` listeners in `app/utils/audit.py` observe inserts,
  updates, and deletes on `cases`, `persons`, `seized_items`, `case_sections`,
  and `documents`, and write `audit_logs` rows with old/new JSON snapshots in
  the same transaction.
- The acting user is captured via `current_user_id_ctx` (a `ContextVar` set by
  the `get_current_user` dependency), so audit rows carry `changed_by` without
  threading the user through every service call.
- The module has import side effects and is imported once at startup
  (`import app.utils.audit` in `main.py`).
- `GET /audit` exposes filtered access to the log for SHO/Legal review.

## Graceful Degradation Matrix

| Component | When missing | Fallback behavior |
|---|---|---|
| ChromaDB | not installed / no index | Keyword scoring over the JSON legal corpus |
| OpenAI API | no key | Template-based summaries; retrieval-only suggestions |
| spaCy | not installed | Regex/keyword entity extraction |
| WeasyPrint | not installed | DOCX only; `pdf` download returns 404 |
| Translation service / Google Translate | unreachable / no key | Text passed through unchanged, `engine: "none"` |
| Celery + Redis | `use_celery=false` | Synchronous in-process document generation |
| Tesseract OCR | not installed | `POST /ocr/extract` returns 503 |
| PostgreSQL | dev environment | SQLite via `sqlite+aiosqlite` (default) |

## Role Model

Privilege ordering: **IO < SHO < LEGAL_ADVISOR**

| Capability | IO | SHO | LEGAL_ADVISOR |
|---|---|---|---|
| Create/edit cases, persons, items, diary | yes | yes | yes |
| Generate/download documents | yes | yes | yes |
| Soft-delete cases | no | yes | yes |
| Review audit trail | limited | yes | yes |
| Vet/approve legal sections | no | no | yes |

Role checks are enforced with the `require_role(*roles)` dependency in
`app/utils/security.py`. Deletion is always soft (`is_deleted` flag) so the
audit trail remains complete.
