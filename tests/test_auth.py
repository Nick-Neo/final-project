from conftest import login


def test_login_valid_credentials_redirects(client):
    resp = client.post("/login", data={"email": "test@test.com", "password": "testpass"})
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_invalid_password_returns_401(client):
    resp = client.post("/login", data={"email": "test@test.com", "password": "wrongpass"})
    assert resp.status_code == 401
