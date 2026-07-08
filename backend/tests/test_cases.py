"""Case CRUD, nested children, NLP inference, diary automation and RBAC."""

THEFT_NARRATIVE = (
    "The complainant reported that his wallet was stolen from his pocket "
    "while boarding a bus at Lal Darwaja bus stand. The theft was noticed "
    "only after reaching home."
)


async def test_create_case_with_nested_children(make_case):
    case = await make_case()
    # NLP crime-type inference ran on the English narrative.
    assert case["crime_type"] == "assault"
    assert case["narrative_en"] == case["narrative"]
    # Nested children persisted.
    assert len(case["persons"]) == 2
    assert {p["role"] for p in case["persons"]} == {"ACCUSED", "VICTIM"}
    assert len(case["items"]) == 1
    assert case["sections"][0]["act"] == "BNS"
    # Automatic FIR_FILED diary entry.
    assert any(e["entry_type"] == "FIR_FILED" for e in case["diary_entries"])


async def test_list_cases_pagination_shape(client, io_headers, make_case):
    await make_case()
    resp = await client.get(
        "/api/v1/cases", params={"page": 1, "page_size": 5}, headers=io_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"total", "page", "page_size", "items"}
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] >= 1
    assert len(data["items"]) <= 5
    assert "fir_number" in data["items"][0]


async def test_get_case_includes_nested(client, io_headers, make_case):
    created = await make_case()
    resp = await client.get(f"/api/v1/cases/{created['id']}", headers=io_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert {p["role"] for p in data["persons"]} == {"ACCUSED", "VICTIM"}
    assert data["items"][0]["item_name"] == "Iron rod"
    assert data["sections"][0]["section"] == "115"


async def test_search_by_fir_fragment(client, io_headers, make_case):
    created = await make_case()
    fragment = created["fir_number"].rsplit("/", 1)[-1]  # unique hex suffix
    resp = await client.get(
        "/api/v1/cases/search", params={"q": fragment}, headers=io_headers
    )
    assert resp.status_code == 200
    assert created["id"] in [c["id"] for c in resp.json()]


async def test_update_narrative_reruns_nlp(client, io_headers, make_case):
    created = await make_case()
    resp = await client.put(
        f"/api/v1/cases/{created['id']}",
        json={"narrative": THEFT_NARRATIVE},
        headers=io_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # English case: narrative_en re-derived from the new narrative.
    assert data["narrative_en"] == THEFT_NARRATIVE
    assert data["crime_type"] == "theft"


async def test_delete_case_role_enforcement(client, io_headers, sho_headers, make_case):
    created = await make_case()

    forbidden = await client.delete(
        f"/api/v1/cases/{created['id']}", headers=io_headers
    )
    assert forbidden.status_code == 403

    deleted = await client.delete(
        f"/api/v1/cases/{created['id']}", headers=sho_headers
    )
    assert deleted.status_code == 204

    gone = await client.get(f"/api/v1/cases/{created['id']}", headers=io_headers)
    assert gone.status_code == 404


async def test_add_person(client, io_headers, make_case):
    created = await make_case()
    resp = await client.post(
        f"/api/v1/cases/{created['id']}/persons",
        json={"role": "WITNESS", "name": "Kamlesh Joshi", "age": 52},
        headers=io_headers,
    )
    assert resp.status_code == 200
    person = resp.json()
    assert person["role"] == "WITNESS"
    assert person["case_id"] == created["id"]
    assert person["id"]


async def test_add_item_records_evidence_diary_entry(client, io_headers, make_case):
    created = await make_case()
    resp = await client.post(
        f"/api/v1/cases/{created['id']}/items",
        json={"item_name": "Stolen mobile phone", "quantity": "1"},
        headers=io_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["item_name"] == "Stolen mobile phone"

    diary = await client.get(
        f"/api/v1/cases/{created['id']}/diary", headers=io_headers
    )
    assert diary.status_code == 200
    entries = diary.json()
    seized = [e for e in entries if e["entry_type"] == "EVIDENCE_SEIZED"]
    assert any("Stolen mobile phone" in e["description"] for e in seized)
