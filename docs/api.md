# CrimeGPT API Reference

Base URL: `http://<host>/api/v1` (except `/health`, which has no prefix).

**Authentication:** All endpoints require a Bearer JWT (`Authorization: Bearer <access_token>`) except `POST /auth/login`, `POST /auth/refresh`, and `GET /health`.

**Conventions:** snake_case JSON, UUIDs as strings, ISO 8601 dates (`YYYY-MM-DD`) and times (`HH:MM:SS`). Errors are returned as `{"detail": "<message>"}` with an appropriate HTTP status.

---

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Liveness probe. Returns `{"status": "ok"}`. |

---

## Auth

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | No | `LoginRequest` `{badge_no, password}` (also accepts OAuth2 form `username`/`password` where `username` = badge_no, for Swagger) | `TokenResponse` `{access_token, refresh_token, token_type, user}` |
| POST | `/api/v1/auth/refresh` | No | `RefreshRequest` `{refresh_token}` | `AccessTokenResponse` `{access_token, token_type}` |
| POST | `/api/v1/auth/logout` | Yes | — | `{detail}` |
| GET | `/api/v1/auth/me` | Yes | — | `UserOut` |

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"badge_no": "GJ001", "password": "secret"}'
```

---

## Cases

| Method | Path | Auth | Body / Query | Response |
|---|---|---|---|---|
| GET | `/api/v1/cases` | Yes | Query: `page`, `page_size`, `status`, `io_id`, `date_from`, `date_to` | `PaginatedCases` `{total, page, page_size, items: [CaseListItem]}` |
| POST | `/api/v1/cases` | Yes | `CaseCreate` `{fir_number, station, ps_name, incident_date, incident_time, incident_place, narrative, language, persons[], items[], sections[]}` | `CaseOut` (201) |
| GET | `/api/v1/cases/search?q=` | Yes | Query: `q` (matches FIR number / narrative) | `[CaseListItem]` |
| GET | `/api/v1/cases/{id}` | Yes | — | `CaseOut` (with nested persons, items, sections, diary entries, documents) |
| PUT | `/api/v1/cases/{id}` | Yes | `CaseUpdate` (partial fields) | `CaseOut` |
| DELETE | `/api/v1/cases/{id}` | Yes (SHO or LEGAL_ADVISOR) | — | 204 (soft delete) |

```bash
curl -X POST http://localhost/api/v1/cases \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "fir_number": "11209001260001/2026",
    "station": "Navrangpura",
    "ps_name": "Navrangpura Police Station",
    "incident_date": "2026-07-04",
    "incident_time": "21:30:00",
    "incident_place": "CG Road, Ahmedabad",
    "narrative": "Two persons on a motorcycle snatched a gold chain...",
    "language": "en",
    "persons": [{"role": "VICTIM", "name": "Jane Doe", "age": 34, "gender": "F"}],
    "items": [{"item_name": "Gold chain", "quantity": 1}],
    "sections": []
  }'
```

### Nested resources

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/api/v1/cases/{id}/persons` | `PersonCreate` `{role, name, age, gender, address, phone, id_type, id_number, notes}` | `PersonOut` |
| PUT | `/api/v1/cases/{id}/persons/{pid}` | `PersonUpdate` | `PersonOut` |
| DELETE | `/api/v1/cases/{id}/persons/{pid}` | — | 204 |
| POST | `/api/v1/cases/{id}/items` | `SeizedItemCreate` `{item_name, quantity, description, seized_from, seized_at}` | `SeizedItemOut` |
| PUT | `/api/v1/cases/{id}/items/{iid}` | `SeizedItemUpdate` | `SeizedItemOut` |
| DELETE | `/api/v1/cases/{id}/items/{iid}` | — | 204 |
| POST | `/api/v1/cases/{id}/sections` | `CaseSectionCreate` `{act, section, description, source, confidence}` | `CaseSectionOut` |
| DELETE | `/api/v1/cases/{id}/sections/{sid}` | — | 204 |

---

## Documents

| Method | Path | Body / Query | Response |
|---|---|---|---|
| POST | `/api/v1/cases/{id}/documents/generate` | `GenerateDocumentsRequest` `{doc_types: [str]}` — any of the 7 supported doc types | `GenerateDocumentsResponse` `{task_id, status, documents}`. Sync path returns `status: "completed"` with the documents list. |
| GET | `/api/v1/cases/{id}/documents` | — | `[DocumentOut]` `{id, case_id, doc_type, version, docx_path, pdf_path, generated_by, generated_at}` |
| GET | `/api/v1/documents/{doc_id}/download?format=docx\|pdf` | — | `FileResponse` (404 if file or PDF missing) |
| POST | `/api/v1/cases/{id}/documents/bulk-download` | — | ZIP bytes, `application/zip`, `Content-Disposition: attachment; filename=fir_documents.zip` |

```bash
curl -X POST http://localhost/api/v1/cases/$CASE_ID/documents/generate \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"doc_types": ["fir", "arrest_memo"]}'
```

---

## Legal Intelligence

| Method | Path | Body / Query | Response |
|---|---|---|---|
| POST | `/api/v1/legal/suggest` | `SuggestRequest` `{narrative, language}` | `SuggestResponse` `{sections: [SectionSuggestion], judgments: [JudgmentSuggestion], entities: ExtractedEntities}` |
| GET | `/api/v1/legal/search?q=&act=BNS\|BNSS\|BSA` | — | `[LegalSectionOut]` `{act, section, title, text}` |
| GET | `/api/v1/legal/section/{act}/{number}` | — | `LegalSectionOut` (404 if unknown) |

```bash
curl -X POST http://localhost/api/v1/legal/suggest \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"narrative": "Two men on a motorcycle snatched a gold chain and threatened the victim with an iron rod", "language": "en"}'
```

---

## Case Diary

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/v1/cases/{id}/diary` | — | `[DiaryEntryOut]` |
| POST | `/api/v1/cases/{id}/diary` | `DiaryEntryCreate` `{entry_type, description}` | `DiaryEntryOut` |

---

## Audit

| Method | Path | Query | Response |
|---|---|---|---|
| GET | `/api/v1/audit` | `case_id`, `user_id`, `table_name`, `date_from`, `date_to` | `[AuditLogOut]` `{id, table_name, record_id, action, old_data, new_data, changed_by, user, changed_at}` |

---

## Utilities

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/api/v1/translate` | `TranslateRequest` `{text, source, target}` | `TranslateResponse` `{translated, engine}` |
| POST | `/api/v1/ocr/extract` | multipart `file` (image) | `{extracted_text, confidence}` (503 if OCR unavailable) |

---

## Roles

- **IO** (Investigating Officer): create/edit own cases, generate documents, diary entries.
- **SHO**: everything IO can do, plus delete (soft) cases and view all station cases.
- **LEGAL_ADVISOR**: full read access, section vetting, delete cases, audit review.
