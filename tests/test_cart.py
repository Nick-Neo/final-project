from conftest import login
from ecom_app import app, db, CartItem, InventoryItem


def test_cart_unauthenticated_redirects_to_login(client):
    resp = client.get("/cart")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_add_to_cart(client):
    login(client)
    with app.app_context():
        inv_id = InventoryItem.query.filter_by(item_name="Barcode Scanner").first().id
    resp = client.post("/cart/add", data={"inventory_item_id": str(inv_id)})
    assert resp.status_code == 302
    with app.app_context():
        assert CartItem.query.filter_by(product_name="Barcode Scanner").count() == 1


def test_add_same_product_twice_increments_quantity(client):
    login(client)
    with app.app_context():
        inv_id = InventoryItem.query.filter_by(item_name="Barcode Scanner").first().id
    client.post("/cart/add", data={"inventory_item_id": str(inv_id)})
    client.post("/cart/add", data={"inventory_item_id": str(inv_id)})
    with app.app_context():
        items = CartItem.query.filter_by(product_name="Barcode Scanner").all()
        assert len(items) == 1
        assert items[0].quantity == 2


def test_update_cart_quantity(client):
    login(client)
    with app.app_context():
        item_id = CartItem.query.filter_by(product_name="POS Terminal").first().id
    resp = client.post(f"/cart/update/{item_id}", data={"quantity": "3"})
    assert resp.status_code == 302
    with app.app_context():
        assert CartItem.query.get(item_id).quantity == 3


def test_remove_from_cart(client):
    login(client)
    with app.app_context():
        item_id = CartItem.query.filter_by(product_name="POS Terminal").first().id
    resp = client.post(f"/cart/remove/{item_id}")
    assert resp.status_code == 302
    with app.app_context():
        assert CartItem.query.get(item_id) is None
