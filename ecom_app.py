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
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///comments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "a-very-secret-dev-key-12345")

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
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()


# --- Temporary Fake Identity storage ---
class FakeUser:
    def __init__(self, email, password, role="customer"):
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.id = 1 if role == "customer" else 2
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


FAKE_USERS_DB = {
    "test@email.com": FakeUser("test@email.com", "password123", role="customer"),
    "admin@poshub.com": FakeUser("admin@poshub.com", "adminpass456", role="admin"),
}


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

        user = FAKE_USERS_DB.get(email)

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

        user = FAKE_USERS_DB.get(email)

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
