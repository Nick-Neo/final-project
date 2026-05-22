from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo
import os

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///comments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

app.secret_key = os.environ.get("SECRET_KEY")
login_manager = LoginManager()
login_manager.init_app(app)

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))
    posted = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))
    )
    commenter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    commenter = db.relationship('User', foreign_keys=commenter_id)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()

@app.route("/")
def index():
    return render_template("main.html")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)