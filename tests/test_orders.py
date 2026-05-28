from conftest import login


def test_orders_page_unauthenticated_redirects(client):
    resp = client.get("/orders")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_orders_page_authenticated_renders(client):
    login(client)
    resp = client.get("/orders")
    assert resp.status_code == 200
