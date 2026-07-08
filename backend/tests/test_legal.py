"""Legal intelligence: RAG suggestions, corpus search and section lookup."""

from tests.conftest import IRON_ROD_NARRATIVE


async def test_suggest_on_assault_narrative(client, io_headers):
    resp = await client.post(
        "/api/v1/legal/suggest",
        json={"narrative": IRON_ROD_NARRATIVE, "language": "en"},
        headers=io_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["sections"], "expected at least one section suggestion"
    first = data["sections"][0]
    assert set(first) == {
        "act", "section", "title", "relevance_score", "excerpt", "source",
    }
    assert first["source"] == "AI_SUGGESTED"
    # A BNS section with a positive relevance score must be suggested.
    bns = [s for s in data["sections"] if s["act"] == "BNS"]
    assert bns and bns[0]["relevance_score"] > 0

    entities = data["entities"]
    assert entities["crime_types"], "expected non-empty crime_types"
    assert "assault" in entities["crime_types"]
    assert "iron rod" in entities["weapons"]


async def test_search_theft_scoped_to_bns(client, io_headers):
    resp = await client.get(
        "/api/v1/legal/search",
        params={"q": "theft", "act": "BNS"},
        headers=io_headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert results
    assert all(r["act"] == "BNS" for r in results)
    assert "303" in [r["section"] for r in results]


async def test_get_section_bns_303(client, io_headers):
    resp = await client.get("/api/v1/legal/section/BNS/303", headers=io_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Theft"
    assert data["act"] == "BNS"
    assert data["text"]


async def test_get_unknown_section_404(client, io_headers):
    resp = await client.get("/api/v1/legal/section/BNS/99999", headers=io_headers)
    assert resp.status_code == 404
    assert "detail" in resp.json()
