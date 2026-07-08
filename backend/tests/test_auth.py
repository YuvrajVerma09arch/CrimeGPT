"""Auth flow: login, wrong password, /me, refresh, unauthenticated access."""


async def test_login_success(client, io_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"badge_no": "IO900", "password": "demo123"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["badge_no"] == "IO900"
    assert data["user"]["role"] == "IO"


async def test_login_wrong_password(client, io_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"badge_no": "IO900", "password": "not-the-password"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_me_returns_current_user(client, io_headers):
    resp = await client.get("/api/v1/auth/me", headers=io_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["badge_no"] == "IO900"
    assert data["is_active"] is True


async def test_refresh_token_flow(client, io_user):
    login = await client.post(
        "/api/v1/auth/login",
        json={"badge_no": "IO900", "password": "demo123"},
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    assert new_access

    # The freshly-minted access token must be accepted.
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert me.status_code == 200
    assert me.json()["badge_no"] == "IO900"


async def test_protected_route_requires_auth(client):
    resp = await client.get("/api/v1/cases")
    assert resp.status_code == 401
