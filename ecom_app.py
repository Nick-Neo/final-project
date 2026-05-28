from dotenv import load_dotenv
load_dotenv()
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# ==============================================================================
# 1. APPLICATION & DATABASE CONFIGURATION
# ==============================================================================
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "ssl": {"ssl_mode": "REQUIRED"}
    }
}

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "customer_login"


# ==============================================================================
# 2. DATABASE MODELS & FAKE ID STORAGE
# ==============================================================================
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))
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
    description = db.Column(db.String(500))
    quantity_left = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )

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
    stripe_session_id = db.Column(db.String(255))
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )


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

# ==============================================================================
# 3. GLOBAL / PUBLIC ROUTES
# ==============================================================================
@app.route("/")
def home():
    return render_template("main.html")


@app.route("/logout")
def logout():
    # Shared logout route routing back to customer login
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
            return redirect(url_for("customer_dashboard", user_email=email))

        return "Invalid email or password!", 401

    return render_template("customer/customer_login.html")


@app.route("/dashboard")
def customer_dashboard():
    email = request.args.get("user_email", "Guest")
    return render_template("customer/customer_view.html", user_email=email)


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
def admin_dashboard():
    email = request.args.get("admin_email", "Admin")
    return render_template("admin/admin_dashboard.html", admin_email=email)


# ==============================================================================
# 6. APPLICATION RUNNER
# ==============================================================================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)