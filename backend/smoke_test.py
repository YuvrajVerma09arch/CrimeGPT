"""End-to-end smoke test against a live uvicorn instance.

Walks the hackathon demo script (CLAUDE.md section 16) over real HTTP:
login -> create Gujarati case -> legal suggestions -> persons/items ->
generate all 7 documents -> bulk zip -> diary -> edit address -> audit.

Run: .venv/bin/python smoke_test.py
"""
import os
import subprocess
import sys
import time

import httpx

PORT = 8017
BASE = f"http://127.0.0.1:{PORT}"
API = f"{BASE}/api/v1"
ENV = {
    **os.environ,
    "DATABASE_URL": "sqlite+aiosqlite:///./smoke_check.db",
    "UPLOAD_DIR": "./smoke_uploads",
    "CHROMA_DB_PATH": "./smoke_chroma",
}

GUJARATI_NARRATIVE = (
    "તા. ૦૫/૦૭/૨૦૨૬ ના રોજ સાંજે આશરે ૭ વાગ્યે સી.જી. રોડ પર બે અજાણ્યા "
    "માણસોએ મોટરસાયકલ પર આવીને ફરિયાદીના ગળામાંથી સોનાની ચેન ખેંચી લીધી "
    "અને લોખંડના સળિયાથી ધમકી આપી મોબાઈલ ફોન પણ છીનવી લીધો હતો."
)

failures = []


def check(name, condition, detail=""):
    mark = "PASS" if condition else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def main():
    proc = subprocess.Popen(
        [".venv/bin/uvicorn", "app.main:app", "--port", str(PORT)],
        env=ENV,
        stdout=open("smoke_uvicorn.log", "w"),
        stderr=subprocess.STDOUT,
    )
    try:
        # Wait for startup
        for _ in range(60):
            try:
                if httpx.get(f"{BASE}/health", timeout=1).status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            check("server startup", False, "health never came up")
            return

        check("GET /health", True)

        # Seed users into the smoke DB
        subprocess.run(
            [".venv/bin/python", "-m", "app.seeds.demo_data"],
            env=ENV, check=True, capture_output=True,
        )

        c = httpx.Client(timeout=30)

        # 1. Login
        r = c.post(f"{API}/auth/login", json={"badge_no": "IO001", "password": "demo123"})
        check("login IO001", r.status_code == 200, f"status={r.status_code}")
        tokens = r.json()
        check("login returns user+tokens",
              "access_token" in tokens and "refresh_token" in tokens
              and tokens["user"]["role"] == "IO")
        h = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Bad login
        r = c.post(f"{API}/auth/login", json={"badge_no": "IO001", "password": "wrong"})
        check("bad login -> 401 with detail", r.status_code == 401 and "detail" in r.json())

        # 2. Legal suggestions for the Gujarati narrative
        r = c.post(f"{API}/legal/suggest",
                   json={"narrative": GUJARATI_NARRATIVE, "language": "gu"}, headers=h)
        check("POST /legal/suggest", r.status_code == 200, f"status={r.status_code}")
        sugg = r.json()
        check("suggest returns entities", "entities" in sugg and "crime_types" in sugg["entities"])
        check("suggest finds sections for Gujarati narrative",
              len(sugg.get("sections", [])) > 0,
              f"{len(sugg.get('sections', []))} sections, "
              f"crime_types={sugg['entities']['crime_types']}, "
              f"weapons={sugg['entities']['weapons']}")

        # 3. Create case with nested persons/items/sections
        payload = {
            "fir_number": "SMOKE/2026/0001",
            "station": "Navrangpura",
            "ps_name": "Navrangpura Police Station",
            "incident_date": "2026-07-05",
            "incident_time": "19:00:00",
            "incident_place": "C.G. Road, Ahmedabad",
            "narrative": GUJARATI_NARRATIVE,
            "language": "gu",
            "persons": [
                {"role": "VICTIM", "name": "Smt. Kokila Shah", "age": 52,
                 "gender": "FEMALE", "address": "12, Shanti Apartments, Navrangpura"},
                {"role": "ACCUSED", "name": "Unknown Person 1", "notes": "motorcycle rider"},
            ],
            "items": [
                {"item_name": "Gold chain", "quantity": "1 (approx 25g)",
                 "seized_from": "recovered near C.G. Road"},
            ],
            "sections": [
                {"act": "BNS", "section": "304", "description": "Snatching",
                 "source": "AI_SUGGESTED", "confidence": 0.9},
            ],
        }
        r = c.post(f"{API}/cases", json=payload, headers=h)
        check("POST /cases -> 201", r.status_code == 201, f"status={r.status_code} {r.text[:200]}")
        case = r.json()
        case_id = case["id"]
        check("case has nested persons/items/sections",
              len(case["persons"]) == 2 and len(case["items"]) == 1 and len(case["sections"]) == 1)
        check("diary auto FIR_FILED",
              any(d["entry_type"] == "FIR_FILED" for d in case["diary_entries"]))

        # 4. Generate all 7 documents
        r = c.post(f"{API}/cases/{case_id}/documents/generate", json={}, headers=h)
        check("generate documents", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")
        gen = r.json()
        check("7 documents generated", len(gen.get("documents", [])) == 7,
              f"{len(gen.get('documents', []))} docs, status={gen.get('status')}")

        # Download one docx
        if gen.get("documents"):
            doc_id = gen["documents"][0]["id"]
            r = c.get(f"{API}/documents/{doc_id}/download", params={"format": "docx"}, headers=h)
            check("download docx", r.status_code == 200 and len(r.content) > 1000,
                  f"status={r.status_code}, {len(r.content)} bytes")

        # 5. Bulk zip
        r = c.post(f"{API}/cases/{case_id}/documents/bulk-download", headers=h)
        check("bulk zip", r.status_code == 200
              and r.headers.get("content-type", "").startswith("application/zip")
              and len(r.content) > 5000, f"{len(r.content)} bytes")

        # 6. Diary shows DOCUMENT_GENERATED
        r = c.get(f"{API}/cases/{case_id}/diary", headers=h)
        check("diary DOCUMENT_GENERATED entry",
              any(d["entry_type"] == "DOCUMENT_GENERATED" for d in r.json()))

        # 7. Edit accused address -> audit UPDATE
        accused = next(p for p in case["persons"] if p["role"] == "ACCUSED")
        r = c.put(f"{API}/cases/{case_id}/persons/{accused['id']}",
                  json={"address": "Slum area, Vatva GIDC"}, headers=h)
        check("update person address", r.status_code == 200)
        r = c.get(f"{API}/audit", params={"case_id": case_id}, headers=h)
        audits = r.json()
        upd = [a for a in audits if a["action"] == "UPDATE" and a["table_name"] == "persons"]
        check("audit UPDATE row for person",
              len(upd) >= 1 and upd[0]["new_data"].get("address") == "Slum area, Vatva GIDC"
              and upd[0].get("changed_by"))

        # 8. Role enforcement: IO cannot delete
        r = c.delete(f"{API}/cases/{case_id}", headers=h)
        check("IO delete -> 403", r.status_code == 403)

        # SHO can
        r = c.post(f"{API}/auth/login", json={"badge_no": "SHO001", "password": "demo123"})
        sho_h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        r = c.delete(f"{API}/cases/{case_id}", headers=sho_h)
        check("SHO delete -> 204", r.status_code == 204)

        # 9. Legal search + section detail
        r = c.get(f"{API}/legal/search", params={"q": "theft", "act": "BNS"}, headers=h)
        check("legal search", r.status_code == 200 and len(r.json()) > 0)
        r = c.get(f"{API}/legal/section/BNS/303", headers=h)
        check("section BNS/303 = Theft", r.status_code == 200 and r.json()["title"] == "Theft")

        # 10. Translate endpoint (passthrough fallback ok)
        r = c.post(f"{API}/translate",
                   json={"text": "hello", "source": "en", "target": "gu"}, headers=h)
        check("translate endpoint", r.status_code == 200 and "engine" in r.json())

    finally:
        proc.terminate()
        proc.wait(timeout=10)

    print()
    if failures:
        print(f"SMOKE TEST: {len(failures)} FAILURE(S): {failures}")
        sys.exit(1)
    print("SMOKE TEST: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
