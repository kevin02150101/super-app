def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "email": "a@b.com", "password": "secret123", "nickname": "Tester"
    })
    assert r.status_code == 201
    assert r.get_json()["ok"] is True

    r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 200

    r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert r.status_code == 401


def test_analyze_requires_login(client):
    r = client.post("/api/analyze")
    assert r.status_code == 401
