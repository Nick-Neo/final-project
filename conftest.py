import os
os.environ["TESTING"] = "1"  # must be set before ecom_app is imported

import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import hmac, hashlib, time as _time
import stripe as _stripe

# Stripe 15.x removed WebhookSignature.generate_header — reconstruct it.
def _generate_header(payload, secret, timestamp=None):
    if timestamp is None:
        timestamp = int(_time.time())
    signed_payload = "%d.%s" % (timestamp, payload)
    sig = hmac.new(secret.encode("utf-8"), msg=signed_payload.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
    return "t=%d,v1=%s" % (timestamp, sig)

_stripe.WebhookSignature.generate_header = staticmethod(_generate_header)

# ── Shared fixtures ───────────────────────────────────────────────────────────
import pytest
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash
from ecom_app import app, db, User, CartItem, InventoryItem


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_TEST')}"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    with app.app_context():
        db.create_all()
        user = User(
            username="test@test.com",
            name="Test User",
            password_hash=generate_password_hash("testpass"),
        )
        db.session.add(user)
        db.session.flush()
        inv1 = InventoryItem(item_name="POS Terminal", description="", quantity_left=10, price=299.99)
        inv2 = InventoryItem(item_name="Barcode Scanner", description="", quantity_left=20, price=79.50)
        db.session.add_all([inv1, inv2])
        db.session.flush()
        db.session.add(CartItem(user_id=user.id, product_name="POS Terminal", price=299.99, quantity=1))
        db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()


def login(client):
    with client.session_transaction() as sess:
        sess["_user_id"] = "test@test.com"
        sess["_fresh"] = True
