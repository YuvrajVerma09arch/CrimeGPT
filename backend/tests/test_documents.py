"""Document engine: generation, versioning, listing, download and bulk zip."""
import io
import os
import zipfile

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


async def _generate(client, headers, case_id, doc_types):
    resp = await client.post(
        f"/api/v1/cases/{case_id}/documents/generate",
        json={"doc_types": doc_types},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_generate_two_doc_types(client, io_headers, make_case):
    case = await make_case()
    data = await _generate(
        client, io_headers, case["id"], ["CHARGESHEET", "SEIZURE_RECEIPT"]
    )
    assert data["status"] == "completed"
    assert data["task_id"]
    assert len(data["documents"]) == 2
    assert {d["doc_type"] for d in data["documents"]} == {
        "CHARGESHEET", "SEIZURE_RECEIPT",
    }
    # Files really exist on disk under the upload dir.
    for doc in data["documents"]:
        assert doc["version"] == 1
        assert doc["docx_path"] and os.path.exists(doc["docx_path"])


async def test_regenerate_bumps_version(client, io_headers, make_case):
    case = await make_case()
    first = await _generate(client, io_headers, case["id"], ["CHARGESHEET"])
    assert first["documents"][0]["version"] == 1

    second = await _generate(client, io_headers, case["id"], ["CHARGESHEET"])
    assert second["documents"][0]["version"] == 2


async def test_list_documents(client, io_headers, make_case):
    case = await make_case()
    await _generate(client, io_headers, case["id"], ["PANCHANAMA", "REMAND_REQUEST"])

    resp = await client.get(
        f"/api/v1/cases/{case['id']}/documents", headers=io_headers
    )
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 2
    assert {d["doc_type"] for d in docs} == {"PANCHANAMA", "REMAND_REQUEST"}
    assert all(d["case_id"] == case["id"] for d in docs)


async def test_download_docx(client, io_headers, make_case):
    case = await make_case()
    generated = await _generate(client, io_headers, case["id"], ["CHARGESHEET"])
    doc = generated["documents"][0]

    resp = await client.get(
        f"/api/v1/documents/{doc['id']}/download",
        params={"format": "docx"},
        headers=io_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == DOCX_MEDIA_TYPE
    assert len(resp.content) > 0


async def test_download_pdf_404_when_not_rendered(client, io_headers, make_case):
    case = await make_case()
    generated = await _generate(client, io_headers, case["id"], ["MEDICAL_LETTER"])
    doc = generated["documents"][0]

    resp = await client.get(
        f"/api/v1/documents/{doc['id']}/download",
        params={"format": "pdf"},
        headers=io_headers,
    )
    if doc["pdf_path"] is None:
        # Core install: WeasyPrint absent -> no PDF was rendered.
        assert resp.status_code == 404
    else:
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"


async def test_bulk_download_zip(client, io_headers, make_case):
    case = await make_case()
    await _generate(client, io_headers, case["id"], ["CHARGESHEET", "FACE_ID_FORM"])

    resp = await client.post(
        f"/api/v1/cases/{case['id']}/documents/bulk-download", headers=io_headers
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert len(resp.content) > 0
    archive = zipfile.ZipFile(io.BytesIO(resp.content))
    names = archive.namelist()
    assert any(n.startswith("CHARGESHEET") for n in names)
    assert any(n.startswith("FACE_ID_FORM") for n in names)
