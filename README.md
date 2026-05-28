# POSHub Cloud Store

A cloud-based e-commerce platform for POS hardware, built with Flask and deployed on Azure. Supports customer registration, product browsing, cart management, and Stripe-powered checkout with webhook-based order persistence.

---

## Features

- Customer signup, login, and session management (Flask-Login)
- Product catalogue loaded from Azure MySQL
- Shopping cart — add, update quantity, remove (DB-persisted)
- Stripe Hosted Checkout (test mode) with payment webhook
- Order history stored in DB after confirmed payment
- Admin dashboard for inventory management
- Structured JSON logging on webhook events
- `/health` endpoint for Azure App Service health checks

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.1 |
| Database | Azure MySQL (Flexible Server) |
| ORM | Flask-SQLAlchemy 3.1 |
| Auth | Flask-Login |
| Payments | Stripe Python SDK 12+ |
| Tests | pytest, SQLite in-memory |

---

## Local Setup

### Prerequisites

- Python 3.12+
- pip
- Stripe CLI (for webhook testing) — https://stripe.com/docs/stripe-cli

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd final-project
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Where to get it |
|---|---|
| `SECRET_KEY` | Any long random string |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Azure MySQL credentials |
| `STRIPE_SECRET_KEY` | https://dashboard.stripe.com/test/apikeys |
| `STRIPE_WEBHOOK_SECRET` | Run `stripe listen` (see below) |

> **Note:** If `DB_PASSWORD` contains `@`, replace it with `%40` in `.env`.

### 3. Run the app

```bash
python ecom_app.py
```

App runs at http://localhost:5000

### 4. Test Stripe webhooks locally

In a separate terminal:

```bash
stripe listen --forward-to localhost:5000/webhook/stripe
```

Copy the `whsec_...` secret printed and update `STRIPE_WEBHOOK_SECRET` in `.env`, then restart the app.

Use test card `4242 4242 4242 4242`, any future expiry, any CVC.

---

## Running Tests

Tests run against SQLite in-memory — no DB connection or Stripe API keys needed.

```bash
# Run all tests
pytest tests/ -v

# Run a specific area
pytest tests/test_webhook.py -v
pytest tests/test_cart.py -v
```

### Test structure

```
tests/
  test_auth.py       — login flow (2 tests)
  test_cart.py       — cart add, update, remove (5 tests)
  test_checkout.py   — Stripe checkout flow (4 tests)
  test_webhook.py    — webhook handler (6 tests)
  test_orders.py     — orders page (2 tests)
  test_health.py     — health endpoint (1 test)
```

---

## Project Structure

```
final-project/
  ecom_app.py              — Flask app (routes, models, config)
  requirements.txt         — Python dependencies (pinned)
  .env                     — Local secrets (never committed)
  .env.example             — Template for environment variables
  conftest.py              — pytest shared fixture
  tests/                   — Unit tests
  templates/
    customer/
      base.html            — Shared layout (sidebar, nav, flash messages)
      customer_view.html   — Product dashboard
      cart.html            — Shopping cart
      checkout_success.html — Payment success page
      orders.html          — Order history
    admin/                 — Admin dashboard templates
  docs/
    superpowers/
      specs/               — Feature design specs
      plans/               — Implementation plans
```

---

## API Endpoints

| Route | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | — | Homepage (redirects to dashboard if logged in) |
| `/login` | GET, POST | — | Customer login |
| `/signup` | GET, POST | — | Customer registration |
| `/logout` | GET | — | Logout |
| `/dashboard` | GET | ✅ | Product catalogue |
| `/cart` | GET | ✅ | View cart |
| `/cart/add` | POST | ✅ | Add item to cart |
| `/cart/update/<id>` | POST | ✅ | Update item quantity |
| `/cart/remove/<id>` | POST | ✅ | Remove item from cart |
| `/checkout` | POST | ✅ | Create Stripe Checkout Session |
| `/checkout/success` | GET | ✅ | Payment success page |
| `/checkout/cancel` | GET | ✅ | Payment cancelled → redirect to cart |
| `/orders` | GET | ✅ | Order history |
| `/webhook/stripe` | POST | — | Stripe webhook (signature verified) |
| `/health` | GET | — | Health check → `{"status": "ok", "db": "connected"}` |
| `/admin/login` | GET, POST | — | Admin login |
| `/admin/dashboard` | GET | — | Admin inventory view |

---

## Observability

**Webhook logging** — every `checkout.session.completed` event logs to stdout:

```json
{"event": "checkout.session.completed", "session_id": "cs_test_...", "user_id": 3, "total": 29999, "status": "ok", "ts": "2026-05-28T18:53:34+08:00"}
```

**Health check** — wire up in Azure App Service:
`Settings → Health check → Path: /health`

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, deployable code |
| `feature/cart-checkout-stripe` | Cart, checkout, Stripe payment feature |
