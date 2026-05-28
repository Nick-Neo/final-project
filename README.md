# POSHub Cloud Store

A cloud-based e-commerce platform for POS hardware, built with Flask and hosted on Azure MySQL. Supports customer registration, product browsing with search and categories, cart management, Stripe-powered checkout, order history, customer reviews, and mobile-responsive UI.

---

## Features

- Customer signup, login (with Remember Me), and session management (Flask-Login)
- Product catalogue with **search** (name/description) and **category filters**
- Real-time stock display — In Stock / Low Stock / Out of Stock
- Server-side stock validation on add-to-cart and checkout
- Shopping cart — add, update quantity, remove (DB-persisted)
- Stripe Hosted Checkout (test mode) with webhook-based order persistence
- Inventory stock decremented automatically on confirmed payment
- Order history stored in DB after confirmed payment
- **Product detail page** with customer reviews and **star ratings (1–5)**
- Admin dashboard for inventory management
- Structured JSON logging on webhook events
- `/health` endpoint for Azure App Service health checks
- Flash messages for user feedback (payment cancelled, stock errors, review submitted)
- **Mobile-responsive** layout with hamburger sidebar navigation

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.1 |
| Database | Azure MySQL (Flexible Server) |
| ORM | Flask-SQLAlchemy 3.1 |
| Auth | Flask-Login |
| Payments | Stripe Python SDK 12+ |
| Frontend | Jinja2 templates, vanilla CSS (static files) |
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
  conftest.py              — pytest shared fixture + Stripe workaround
  tests/                   — Unit tests (split by feature area)
  static/
    css/
      base.css             — Shared layout (sidebar, hamburger, flash)
      auth.css             — Login/signup pages
      dashboard.css        — Products, search, category filters, toast
      cart.css             — Cart items and summary
      orders.css           — Order history cards
      checkout_success.css — Payment success page
      product_detail.css   — Product detail and reviews
  templates/
    customer/
      base.html            — Authenticated layout (sidebar, nav, responsive)
      auth_base.html       — Public layout (header, footer)
      customer_view.html   — Product dashboard with search and filters
      cart.html            — Shopping cart
      checkout_success.html — Payment success page
      orders.html          — Order history
      product_detail.html  — Product detail with reviews and star rating form
      customer_login.html  — Login page
      signup.html          — Registration page
    admin/                 — Admin dashboard templates
```

---

## API Endpoints

| Route | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | — | Homepage (redirects to dashboard if logged in) |
| `/login` | GET, POST | — | Customer login (supports Remember Me) |
| `/signup` | GET, POST | — | Customer registration |
| `/logout` | GET | — | Logout |
| `/dashboard` | GET | ✅ | Product catalogue with search (`?q=`) and category filter (`?category=`) |
| `/cart` | GET | ✅ | View cart |
| `/cart/add` | POST | ✅ | Add item to cart (stock validated server-side) |
| `/cart/update/<id>` | POST | ✅ | Update item quantity |
| `/cart/remove/<id>` | POST | ✅ | Remove item from cart |
| `/checkout` | POST | ✅ | Create Stripe Checkout Session (stock re-validated) |
| `/checkout/success` | GET | ✅ | Payment success page |
| `/checkout/cancel` | GET | ✅ | Payment cancelled → flash message → redirect to cart |
| `/orders` | GET | ✅ | Order history |
| `/product/<id>` | GET | ✅ | Product detail page with reviews |
| `/product/<id>/review` | POST | ✅ | Submit star rating and review |
| `/webhook/stripe` | POST | — | Stripe webhook — saves order, decrements stock |
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
| `feature/cart-checkout-stripe` | Cart, checkout, Stripe payment, reviews, mobile responsive |
