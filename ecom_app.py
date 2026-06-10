from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
import stripe
import smtplib
from email.message import EmailMessage

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
logger = logging.getLogger(__name__)
_log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=_log_level, format="%(message)s")
# Third-party loggers: verbose only at DEBUG, otherwise quiet (WARNING) to keep JSON output clean
_third_party_level = logging.DEBUG if _log_level <= logging.DEBUG else logging.WARNING
logging.getLogger("stripe").setLevel(_third_party_level)
logging.getLogger("werkzeug").setLevel(_third_party_level)
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from azure.storage.blob import BlobServiceClient

_blob_conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(_blob_conn_str) if _blob_conn_str else None
container_name = os.environ.get("AZURE_CONTAINER_NAME")

from sqlalchemy import func, text

# ==============================================================================
# 1. APPLICATION & DATABASE CONFIGURATION
# ==============================================================================
app = Flask(__name__)
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
if os.environ.get("TESTING"):
    _db_uri = (
        f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_TEST')}"
    )
elif all(os.environ.get(k) for k in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")):
    _db_uri = (
        f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    )
else:
    _db_uri = (
        f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_TEST')}"
    )
app.config["SQLALCHEMY_DATABASE_URI"] = _db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")
if _db_uri.startswith("mysql"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {
            "ssl": {"ssl_mode": "REQUIRED"}
        }
    }

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "customer_login"

MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")
FROM_NAME = os.environ.get("FROM_NAME", "POSHub Support")
FROM_EMAIL = os.environ.get("FROM_EMAIL", MAIL_USERNAME)


def send_email(to_email, subject, plain_text):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg.set_content(plain_text)

    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)

@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        return {"cart_count": CartItem.query.filter_by(user_id=current_user.id).count()}
    return {"cart_count": 0}


# ==============================================================================
# 2. DATABASE MODELS & FAKE ID STORAGE
# ==============================================================================
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id"), nullable=True)
    content = db.Column(db.String(4096))
    rating = db.Column(db.Integer, nullable=False, default=5)
    posted = db.Column(
        db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )
    commenter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    commenter = db.relationship("User", foreign_keys=commenter_id)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(512))
    name = db.Column(db.String(128))
    role = db.Column(db.String(50), default="customer")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(500))
    quantity_left = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )
    reviews = db.relationship("Comment", backref="product", lazy="dynamic")

    @property
    def avg_rating(self):
        ratings = [r.rating for r in self.reviews]
        return round(sum(ratings) / len(ratings), 1) if ratings else None

class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )
    items = db.relationship("OrderItem", backref="order")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    issue = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==============================================================================
# 3. GLOBAL / PUBLIC ROUTES
# ==============================================================================
@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("customer_dashboard"))

    products = InventoryItem.query.order_by(
        InventoryItem.created_at.desc()
    ).all()

    return render_template(
        "main.html",
        products=products
    )


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("customer_login"))


# ==============================================================================
# 4. CUSTOMER COMPONENTS (Signup, Login, Dashboard)
# ==============================================================================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password != password2:
            return "Passwords do not match!", 400

        user_exists = User.query.filter_by(username=email).first()
        if user_exists:
            return "Email already registered!", 400

        new_user = User(
            username=email, name=name, password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("customer_login"))

    return render_template("customer/signup.html")


@app.route("/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(username=email).first()

        if user and user.check_password(password):
            remember = request.form.get("remember") == "on"

            login_user(user, remember=remember)

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("customer_dashboard"))

        return "Invalid email or password!", 401

    return render_template("customer/customer_login.html")


@app.route("/dashboard")
@login_required
def customer_dashboard():
    q = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()

    query = InventoryItem.query
    if q:
        query = query.filter(InventoryItem.item_name.ilike(f"%{q}%") |
                             InventoryItem.description.ilike(f"%{q}%"))
    if selected_category:
        query = query.filter(InventoryItem.category == selected_category)

    products = query.order_by(InventoryItem.category, InventoryItem.item_name).all()
    categories = sorted({p.category for p in InventoryItem.query.all() if p.category})

    return render_template("customer/customer_view.html",
                           products=products,
                           categories=categories,
                           selected_category=selected_category,
                           search_query=q)

@app.route("/support", methods=["GET", "POST"])
def support():

    if request.method == "POST":

        ticket = SupportTicket(
            name=request.form["name"],
            email=request.form["email"],
            category=request.form["category"],
            issue=request.form["issue"],
            status="Open"
        )

        db.session.add(ticket)
        db.session.commit()

        email_subject = f"New Support Ticket #{ticket.id}"

        email_body = f"""
New support ticket has been submitted.

Ticket ID: #{ticket.id}
Name: {ticket.name}
Email: {ticket.email}
Category: {ticket.category}
Status: {ticket.status}

Issue:
{ticket.issue}

Admin Dashboard:
http://finalprojectepos.southeastasia.cloudapp.azure.com/admin/ticket/{ticket.id}
"""

        try:
            send_email(SUPPORT_EMAIL, email_subject, email_body)
        except Exception as e:
            print("Email failed:", e)

        return f"""
        <h2>Support Ticket Created Successfully</h2>
        <p>Your ticket has been submitted.</p>
        <p>Ticket ID: #{ticket.id}</p>
        <p>Status: Open</p>
        <a href='{url_for("customer_dashboard")}'>Back to Dashboard</a>
        """

    return render_template("customer/support.html")

# ==============================================================================
# 5. ADMIN COMPONENTS (Admin Login, Admin Dashboard)
# ==============================================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(username=email).first()

        if user and user.check_password(password) and user.role == "admin":
            return redirect(url_for("admin_dashboard", admin_email=email))

        return "Access Denied: Invalid Admin Credentials!", 403

    return render_template("admin/admin_login.html")

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":
        return "Access Denied", 403

    total_products = InventoryItem.query.count()
    total_orders = Order.query.count()

    total_sales = db.session.query(
        func.sum(Order.total)
    ).scalar() or 0

    # Daily sales (last 7 days)
    daily_sales = (
        db.session.query(
            func.date(Order.created_at),
            func.sum(Order.total)
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )

    labels = [str(day[0]) for day in daily_sales]
    values = [float(day[1]) for day in daily_sales]

    return render_template(
        "admin/admin_dashboard.html",
        admin_email=current_user.username,
        total_products=total_products,
        total_orders=total_orders,
        total_sales=round(float(total_sales), 2),
        chart_labels=labels,
        chart_values=values
    )

@app.route("/admin/sales-data")
@login_required
def sales_data():
    if current_user.role != "admin":
        return "Access Denied", 403

    period = request.args.get("period", "day")

    if period == "month":
        date_format = "%Y-%m"
    elif period == "year":
        date_format = "%Y"
    else:
        date_format = "%Y-%m-%d"

    results = db.session.execute(text("""
        SELECT DATE_FORMAT(created_at, :date_format) AS sales_date,
               SUM(total) AS revenue
        FROM orders
        WHERE status = 'paid'
        GROUP BY sales_date
        ORDER BY sales_date
    """), {"date_format": date_format}).fetchall()

    return jsonify({
        "labels": [row.sales_date for row in results],
        "values": [float(row.revenue) for row in results]
    })

@app.route("/admin/inventory")
@login_required
def admin_inventory():

    if current_user.role != "admin":
        return "Access Denied", 403

    products = InventoryItem.query.all()

    return render_template(
        "admin/admin_inventory.html",
        products=products,
        admin_email=current_user.username
    )

@app.route("/admin/product/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):

    if current_user.role != "admin":
        return "Access Denied", 403

    product = InventoryItem.query.get_or_404(product_id)

    if request.method == "POST":

        product.item_name = request.form.get("item_name")
        product.category = request.form.get("category")
        product.description = request.form.get("description")
        product.quantity_left = request.form.get("quantity")
        product.price = request.form.get("price")

        file = request.files.get("image")

        if file and file.filename != "":

            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=file.filename
            )

            blob_client.upload_blob(file, overwrite=True)

            product.image_url = blob_client.url

        db.session.commit()

        return redirect(url_for("admin_inventory"))

    return render_template(
        "admin/edit_product.html",
        product=product
    )

@app.route("/admin/add_product", methods=["GET", "POST"])
@login_required
def add_product():

    if current_user.role != "admin":
        return "Access Denied: Admins only!", 403

    if request.method == "POST":
        item_name = request.form.get("item_name")
        category = request.form.get("category")
        description = request.form.get("description")
        quantity = request.form.get("quantity")
        price = request.form.get("price")
        file = request.files["image"]

        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=file.filename
        )

        blob_client.upload_blob(file, overwrite=True)

        image_url = blob_client.url

        new_item = InventoryItem(
            item_name=item_name,
            category=category,
            description=description,
            quantity_left=quantity,
            price=price,
            image_url=image_url
        )

        db.session.add(new_item)
        db.session.commit()

        flash("Product added successfully!", "success")

        return redirect(url_for("admin_inventory"))

    return render_template("admin/add_product.html", admin_email=current_user.username)

@app.route("/admin/support-tickets")
@login_required
def support_tickets():
    if current_user.role != "admin":
        return "Access Denied", 403

    tickets = SupportTicket.query.order_by(
        SupportTicket.created_at.desc()
    ).all()

    return render_template("admin/support_tickets.html", tickets=tickets)


@app.route("/admin/ticket/<int:ticket_id>")
@login_required
def ticket_details(ticket_id):
    if current_user.role != "admin":
        return "Access Denied", 403

    ticket = SupportTicket.query.get_or_404(ticket_id)

    return render_template("admin/support_ticket_details.html", ticket=ticket)


@app.route("/admin/ticket/<int:ticket_id>/update", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    if current_user.role != "admin":
        return "Access Denied", 403

    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = request.form["status"]

    db.session.commit()
    flash("Ticket updated successfully", "success")

    return redirect(url_for("support_tickets"))

# ==============================================================================
# 6. CART ROUTES
# ==============================================================================
@app.route("/cart")
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(float(item.price) * item.quantity for item in items)
    names = [item.product_name for item in items]
    inv = InventoryItem.query.filter(InventoryItem.item_name.in_(names)).all() if names else []
    image_map = {p.item_name: p.image_url for p in inv}
    return render_template("customer/cart.html", items=items, total=total, image_map=image_map)


@app.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    inv_id = request.form.get("inventory_item_id", type=int)
    product = InventoryItem.query.get_or_404(inv_id)

    if product.quantity_left <= 0:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": False, "error": "Out of stock"}, 400
        flash(f"{product.item_name} is out of stock.", "error")
        return redirect(url_for("customer_dashboard"))

    existing = CartItem.query.filter_by(
        user_id=current_user.id, product_name=product.item_name
    ).first()
    if existing:
        if existing.quantity >= product.quantity_left:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"success": False, "error": "Not enough stock"}, 400
            flash(f"Only {product.quantity_left} units of {product.item_name} available.", "error")
            return redirect(url_for("customer_dashboard"))
        existing.quantity += 1
    else:
        db.session.add(CartItem(
            user_id=current_user.id,
            product_name=product.item_name,
            price=product.price,
            quantity=1,
        ))
    db.session.commit()
    cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"success": True, "cart_count": cart_count, "product_name": product.item_name}
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def cart_update(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    qty = request.form.get("quantity", type=int)
    if qty and qty > 0:
        item.quantity = qty
        db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        all_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(float(i.price) * i.quantity for i in all_items)
        return {"success": True,
                "item_total": float(item.price) * item.quantity,
                "cart_total": cart_total,
                "cart_count": len(all_items)}
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def cart_remove(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        all_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(float(i.price) * i.quantity for i in all_items)
        return {"success": True,
                "cart_total": cart_total,
                "cart_count": len(all_items),
                "empty": len(all_items) == 0}
    return redirect(url_for("cart"))


# ==============================================================================
# 7. CHECKOUT ROUTES
# ==============================================================================
@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return redirect(url_for("cart"))

    image_map = {}
    for item in items:
        product = InventoryItem.query.filter_by(item_name=item.product_name).first()
        if not product or product.quantity_left < item.quantity:
            available = product.quantity_left if product else 0
            flash(f"Sorry, only {available} units of {item.product_name} are available. Please update your cart.", "error")
            return redirect(url_for("cart"))
        if product.image_url:
            image_map[item.product_name] = product.image_url

    line_items = [
        {
            "price_data": {
                "currency": "sgd",
                "product_data": {
                    "name": item.product_name,
                    **({"images": [image_map[item.product_name]]} if item.product_name in image_map else {}),
                },
                "unit_amount": int(float(item.price) * 100),
            },
            "quantity": item.quantity,
        }
        for item in items
    ]
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        client_reference_id=str(current_user.id),
        success_url=url_for("checkout_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("checkout_cancel", _external=True),
    )
    return redirect(session.url, code=303)


@app.route("/checkout/success")
@login_required
def checkout_success():
    session_id = request.args.get("session_id")
    session = stripe.checkout.Session.retrieve(session_id)
    line_items = stripe.checkout.Session.list_line_items(session_id)
    return render_template("customer/checkout_success.html", session=session, line_items=line_items.data)


@app.route("/checkout/cancel")
@login_required
def checkout_cancel():
    flash("Payment cancelled. Your cart is still saved.", "info")
    return redirect(url_for("cart"))


# ==============================================================================
# 8. PRODUCT DETAIL + REVIEWS
# ==============================================================================
@app.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):
    product = InventoryItem.query.get_or_404(product_id)
    reviews = Comment.query.filter_by(product_id=product_id).order_by(Comment.posted.desc()).all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render_template("customer/product_detail.html",
                           product=product, reviews=reviews, avg_rating=avg_rating)


@app.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def product_review(product_id):
    InventoryItem.query.get_or_404(product_id)
    content = request.form.get("content", "").strip()
    rating = request.form.get("rating", type=int)
    if content and rating and 1 <= rating <= 5:
        db.session.add(Comment(
            product_id=product_id,
            content=content,
            rating=rating,
            commenter_id=current_user.id,
        ))
        db.session.commit()
        flash("Review submitted. Thank you!", "success")
    else:
        flash("Please provide a review and a star rating.", "error")
    return redirect(url_for("product_detail", product_id=product_id))


# ==============================================================================
# 9. ORDERS ROUTE
# ==============================================================================
@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("customer/orders.html", orders=user_orders)


# ==============================================================================
# 9. WEBHOOK + OBSERVABILITY
# ==============================================================================
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    ts = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.info(json.dumps({"event": "webhook_error", "error": "signature verification failed", "ts": ts}))
        return {"error": "invalid signature"}, 400
    except (ValueError, AttributeError):
        # Stripe SDK may raise AttributeError on minimal payloads lacking top-level "object" field.
        # Fall back to verifying the signature manually and parsing raw JSON.
        try:
            stripe.WebhookSignature.verify_header(
                payload.decode("utf-8") if hasattr(payload, "decode") else payload,
                sig_header,
                webhook_secret,
            )
            event = json.loads(payload)
        except stripe.error.SignatureVerificationError:
            logger.info(json.dumps({"event": "webhook_error", "error": "signature verification failed", "ts": ts}))
            return {"error": "invalid signature"}, 400

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        session_id = s["id"] if isinstance(s, dict) else s.id
        user_id = s.get("client_reference_id") if isinstance(s, dict) else getattr(s, "client_reference_id", None)
        amount_total = s.get("amount_total", 0) if isinstance(s, dict) else getattr(s, "amount_total", 0)

        if not user_id:
            logger.info(json.dumps({"event": "webhook_error", "error": "missing client_reference_id", "ts": ts}))
            return {"status": "ok"}, 200

        if Order.query.filter_by(stripe_session_id=session_id).first():
            return {"status": "ok"}, 200

        order = Order(
            user_id=int(user_id),
            stripe_session_id=session_id,
            total=amount_total / 100,
            status="paid",
        )
        db.session.add(order)
        db.session.flush()

        line_items = stripe.checkout.Session.list_line_items(session_id)
        for li in line_items.data:
            db.session.add(OrderItem(
                order_id=order.id,
                product_name=li.description,
                price=li.price.unit_amount / 100,
                quantity=li.quantity,
            ))
            item = InventoryItem.query.filter_by(item_name=li.description).first()
            if item and item.quantity_left >= li.quantity:
                item.quantity_left -= li.quantity

        CartItem.query.filter_by(user_id=int(user_id)).delete()
        db.session.commit()

        logger.info(json.dumps({
            "event": "checkout.session.completed",
            "session_id": session_id,
            "user_id": int(user_id),
            "total": amount_total,
            "status": "ok",
            "ts": ts,
        }))

    return {"status": "ok"}, 200


# ==============================================================================
# 10. HEALTH ENDPOINT
# ==============================================================================
@app.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok", "db": "connected"}, 200
    except Exception:
        return {"status": "error", "db": "unreachable"}, 500

# ==============================================================================
# 11. SUPPORT TICKET ENDPOINT
# ==============================================================================
@app.route("/api/create-ticket", methods=["POST"])
def create_ticket():
    data = request.get_json()

    if not data:
        return {"success": False, "error": "No data received"}, 400

    name = data.get("name")
    email = data.get("email")
    issue = data.get("issue")

    if not name or not email or not issue:
        return {"success": False, "error": "Missing required fields"}, 400

    ticket = SupportTicket(
        name=name,
        email=email,
        issue=issue,
        status="Open"
    )

    db.session.add(ticket)
    db.session.commit()

    return {
        "success": True,
        "message": "Support ticket created successfully",
        "ticket_id": ticket.id
    }

# ==============================================================================
# 12. APPLICATION RUNNER
# ==============================================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)