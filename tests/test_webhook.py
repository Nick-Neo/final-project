import json
import time
from unittest.mock import patch, MagicMock
import stripe
from ecom_app import app, db, User, CartItem, Order


def _webhook_post(client, payload, sig="t=1,v1=dummy"):
    return client.post(
        "/webhook/stripe",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"Stripe-Signature": sig},
    )


def _completed_payload(session_id="cs_test_abc", user_id="1", amount=29999):
    return {
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": session_id,
            "client_reference_id": user_id,
            "amount_total": amount,
            "currency": "sgd",
        }},
    }


def test_webhook_valid_event_creates_order(client):
    payload = _completed_payload()
    mock_line_items = MagicMock()
    mock_line_items.data = [
        MagicMock(description="POS Terminal", price=MagicMock(unit_amount=29999), quantity=1)
    ]
    with app.app_context():
        user_id = str(User.query.first().id)
    payload["data"]["object"]["client_reference_id"] = user_id
    with patch("stripe.Webhook.construct_event", return_value=payload), \
         patch("stripe.checkout.Session.list_line_items", return_value=mock_line_items):
        resp = _webhook_post(client, payload)
    assert resp.status_code == 200
    with app.app_context():
        assert Order.query.filter_by(stripe_session_id="cs_test_abc").count() == 1
        assert CartItem.query.filter_by(user_id=int(user_id)).count() == 0


def test_webhook_invalid_signature_returns_400(client):
    with patch("stripe.Webhook.construct_event",
               side_effect=stripe.error.SignatureVerificationError("bad", "sig")):
        resp = _webhook_post(client, {})
    assert resp.status_code == 400


def test_webhook_duplicate_session_ignored(client):
    payload = _completed_payload(session_id="cs_dup")
    mock_line_items = MagicMock()
    mock_line_items.data = []
    with app.app_context():
        user_id = str(User.query.first().id)
    payload["data"]["object"]["client_reference_id"] = user_id
    with patch("stripe.Webhook.construct_event", return_value=payload), \
         patch("stripe.checkout.Session.list_line_items", return_value=mock_line_items):
        _webhook_post(client, payload)
        _webhook_post(client, payload)
    with app.app_context():
        assert Order.query.filter_by(stripe_session_id="cs_dup").count() == 1


def test_webhook_unknown_event_type_returns_200_no_db_write(client):
    payload = {"type": "payment_intent.created", "data": {"object": {}}}
    with patch("stripe.Webhook.construct_event", return_value=payload):
        resp = _webhook_post(client, payload)
    assert resp.status_code == 200
    with app.app_context():
        assert Order.query.count() == 0


def test_webhook_missing_client_reference_id_does_not_crash(client):
    payload = _completed_payload()
    payload["data"]["object"]["client_reference_id"] = None
    with patch("stripe.Webhook.construct_event", return_value=payload):
        resp = _webhook_post(client, payload)
    assert resp.status_code == 200
    with app.app_context():
        assert Order.query.count() == 0


def test_webhook_real_signature(client):
    secret = "whsec_testsecret"
    payload_dict = _completed_payload(session_id="cs_real")
    with app.app_context():
        user_id = str(User.query.first().id)
    payload_dict["data"]["object"]["client_reference_id"] = user_id
    payload_str = json.dumps(payload_dict)
    ts = int(time.time())
    header = stripe.WebhookSignature.generate_header(payload_str, secret, timestamp=ts)
    mock_line_items = MagicMock()
    mock_line_items.data = []
    with patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": secret}), \
         patch("stripe.checkout.Session.list_line_items", return_value=mock_line_items):
        resp = client.post(
            "/webhook/stripe",
            data=payload_str,
            content_type="application/json",
            headers={"Stripe-Signature": header},
        )
    assert resp.status_code == 200
