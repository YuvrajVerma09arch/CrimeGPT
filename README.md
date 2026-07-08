# CrimeGPT

**AI-Powered Crime Documentation & Legal Intelligence Platform**
Kanad S.H.I.E.L.D. Hackathon 2026 · Cyber Crime Branch, Ahmedabad

Enter case data once → auto-generate all 7 required legal documents → get AI-powered
BNS/BNSS/BSA section suggestions — in Gujarati, Hindi, or English.

## Features

- **Unified Case Data Pool** — enter victim/accused/incident data once, populate everywhere
- **Document Engine** — 7 auto-generated legal documents (DOCX + PDF): chargesheet,
  medical letter, remand request, seizure receipt, court custody form, panchanama, face ID form
- **RAG Legal Intelligence** — narrative → NLP entity extraction → BNS/BNSS/BSA section
  suggestions with landmark judgment references
- **Case Diary Automation** — timestamped FIR-to-arrest timeline
- **Multilingual** — Gujarati / Hindi / English UI and content translation
- **Audit Trail** — immutable change log on every case mutation, role-based access (IO / SHO / Legal Advisor)

## Quick Start (Docker — recommended)

```bash
cp .env.example .env        # edit JWT_SECRET, DB_PASSWORD (OPENAI_API_KEY optional)
docker compose up -d --build
docker compose exec backend python -m app.seeds.demo_data   # seed demo users + cases
docker compose exec backend python -m app.rag.indexer       # index legal corpus
```

- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs

Optional heavy services (Celery worker, IndicTrans2 translation microservice):

```bash
docker compose --profile full up -d
```

## Quick Start (no Docker)

The backend defaults to **SQLite** and **local embeddings**, so it runs with zero
external services:

```bash
# Backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python -m app.seeds.demo_data
python -m app.rag.indexer          # optional; falls back to keyword search if skipped
uvicorn app.main:app --reload      # http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

## Demo Credentials (seeded)

| Role | Badge | Password |
|---|---|---|
| Investigating Officer | `IO001` | `demo123` |
| Station House Officer | `SHO001` | `demo123` |
| Legal Advisor | `LA001` | `demo123` |

## Demo Flow

1. Login as `IO001` → Dashboard with case list
2. **New Case** → type FIR narrative (Gujarati/Hindi/English) → entities extracted,
   legal section suggestions appear in seconds
3. Add accused, victim, seized items on the same screen
4. **Generate All Documents** → 7 pre-filled documents, bulk-download as ZIP
5. Open **Case Diary** → timestamped timeline of every case event
6. Edit accused address → see the change in **Audit Trail**
7. Switch UI language from the navbar → persists across sessions

## Architecture

```
React (Vite + Tailwind + Zustand + React Query)  ←→  FastAPI (async SQLAlchemy 2.0)
                                                        ├── PostgreSQL / SQLite
                                                        ├── ChromaDB (RAG vector store)
                                                        ├── docxtpl + WeasyPrint (documents)
                                                        ├── spaCy / rule-based NER
                                                        └── IndicTrans2 microservice (optional)
```

See [CLAUDE.md](CLAUDE.md) for the full technical specification and
[docs/](docs/) for API, architecture, and deployment guides.

## Graceful Degradation

The stack is demo-hardened — every heavy dependency has a fallback:

| Component | Primary | Fallback |
|---|---|---|
| Database | PostgreSQL 15 | SQLite (default when no `DATABASE_URL`) |
| Embeddings | OpenAI `text-embedding-3-small` | ChromaDB local ONNX embeddings |
| Vector search | ChromaDB | Pure-Python keyword/TF-IDF retriever |
| NER | spaCy | Rule-based crime lexicon extractor |
| Translation | IndicTrans2 microservice | Google Translate API → passthrough |
| PDF export | WeasyPrint | DOCX-only (PDF skipped with warning) |
| Doc generation | Celery async | Synchronous inline (default) |

## Legal Corpus Disclaimer

`backend/data/legal/` contains a **demo subset** of BNS/BNSS/BSA sections and landmark
judgments with paraphrased summaries for hackathon demonstration. It is **not** an
authoritative legal source — production deployment requires the official gazette texts.

## Testing

```bash
cd backend && pytest tests/ -v          # backend: pytest + httpx async client
cd frontend && npm run test             # frontend: Vitest + React Testing Library

# End-to-end smoke test — boots a live server and walks the full demo script
# (login → Gujarati FIR → AI suggestions → 7 documents → ZIP → diary → audit):
cd backend && .venv/bin/python smoke_test.py
```

---
*CrimeGPT — Built for Kanad S.H.I.E.L.D. Hackathon 2026, Cyber Crime Branch, Ahmedabad City*
