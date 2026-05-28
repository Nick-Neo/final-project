from unittest.mock import patch, MagicMock
from conftest import login
from ecom_app import app, db, CartItem


def test_checkout_creates_stripe_session_and_redirects(client):
    login(client)
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc"
    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        resp = client.post("/checkout")
    assert resp.status_code == 303
    assert "checkout.stripe.com" in resp.headers["Location"]
    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["mode"] == "payment"
    assert len(kwargs["line_items"]) == 1


def test_checkout_empty_cart_does_not_call_stripe(client):
    login(client)
    with app.app_context():
        CartItem.query.delete()
        db.session.commit()
    with patch("stripe.checkout.Session.create") as mock_create:
        resp = client.post("/checkout")
    mock_create.assert_not_called()
    assert resp.status_code == 302
    assert "/cart" in resp.headers["Location"]


def test_checkout_success_renders(client):
    login(client)
    mock_session = MagicMock()
    mock_session.id = "cs_test_abc"
    mock_session.amount_total = 29999
    mock_session.currency = "sgd"
    mock_line_items = MagicMock()
    mock_line_items.data = [
        MagicMock(description="POS Terminal", price=MagicMock(unit_amount=29999), quantity=1)
    ]
    with patch("stripe.checkout.Session.retrieve", return_value=mock_session), \
         patch("stripe.checkout.Session.list_line_items", return_value=mock_line_items):
        resp = client.get("/checkout/success?session_id=cs_test_abc")
    assert resp.status_code == 200


def test_checkout_cancel_redirects_to_cart(client):
    login(client)
    resp = client.get("/checkout/cancel")
    assert resp.status_code == 302
    assert "/cart" in resp.headers["Location"]
