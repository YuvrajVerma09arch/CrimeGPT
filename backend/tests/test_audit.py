"""Audit trail: automatic INSERT/UPDATE capture with actor attribution."""


async def test_case_update_produces_update_row(client, io_headers, io_user, make_case):
    case = await make_case()

    resp = await client.put(
        f"/api/v1/cases/{case['id']}",
        json={"incident_place": "Ellis Bridge, Ahmedabad"},
        headers=io_headers,
    )
    assert resp.status_code == 200

    audit = await client.get(
        "/api/v1/audit",
        params={"case_id": case["id"], "table_name": "cases"},
        headers=io_headers,
    )
    assert audit.status_code == 200
    rows = audit.json()

    updates = [r for r in rows if r["action"] == "UPDATE"]
    assert updates, "expected an UPDATE audit row for the case"
    row = updates[0]
    assert row["record_id"] == case["id"]
    assert row["new_data"]["incident_place"] == "Ellis Bridge, Ahmedabad"
    # The actor is attributed via the request contextvar.
    assert row["changed_by"] == io_user.id
    assert row["user"]["badge_no"] == "IO900"


async def test_case_create_produces_insert_rows(client, io_headers, make_case):
    case = await make_case()

    audit = await client.get(
        "/api/v1/audit", params={"case_id": case["id"]}, headers=io_headers
    )
    assert audit.status_code == 200
    rows = audit.json()

    inserts = [r for r in rows if r["action"] == "INSERT"]
    tables = {r["table_name"] for r in inserts}
    # Case + nested persons/items/sections were all captured in one flush.
    assert {"cases", "persons", "seized_items", "case_sections"} <= tables

    case_insert = next(r for r in inserts if r["table_name"] == "cases")
    assert case_insert["old_data"] is None
    assert case_insert["new_data"]["fir_number"] == case["fir_number"]
