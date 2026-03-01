from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash
from .models import Group, Message, User, db
from .security import admin_required, login_required

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/")
@admin_required
def panel():
    users = User.query.order_by(User.created_at.desc()).all()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(200).all()
    groups = Group.query.order_by(Group.created_at.desc()).all()
    return render_template("admin.html", users=users, messages=messages, groups=groups)


@admin.route("/supremo")
@login_required
def supreme_panel():
    if session.get("role") == "admin":
        return redirect(url_for("admin.panel"))
    return render_template("admin_supremo.html")


@admin.route("/supremo/ativar", methods=["POST"])
@login_required
def activate_supreme():
    username = session.get("username")
    user = User.query.filter_by(username=username).first_or_404()
    user.role = "admin"
    user.banned = False
    db.session.commit()
    session["role"] = "admin"
    return redirect(url_for("admin.panel"))


@admin.route("/user/create", methods=["POST"])
@admin_required
def create_user():
    username = request.form.get("username", "").strip().replace("@", "")
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if username and len(password) >= 6 and not User.query.filter_by(username=username).first():
        db.session.add(
            User(
                username=username,
                password=generate_password_hash(password),
                role="admin" if role == "admin" else "user",
            )
        )
        db.session.commit()

    return redirect(url_for("admin.panel"))


@admin.route("/user/<int:user_id>/ban", methods=["POST"])
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.banned = not user.banned
    db.session.commit()
    return redirect(url_for("admin.panel"))


@admin.route("/user/<int:user_id>/password", methods=["POST"])
@admin_required
def change_password(user_id):
    user = User.query.get_or_404(user_id)
    password = request.form.get("password", "")
    if len(password) >= 6:
        user.password = generate_password_hash(password)
        db.session.commit()
    return redirect(url_for("admin.panel"))


@admin.route("/group/create", methods=["POST"])
@admin_required
def create_group():
    name = request.form.get("name", "").strip()
    creator = User.query.filter_by(username=session.get("username")).first()
    if name and not Group.query.filter_by(name=name).first() and creator:
        db.session.add(Group(name=name, created_by=creator.id))
        db.session.commit()
    return redirect(url_for("admin.panel"))
