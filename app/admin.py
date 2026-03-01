from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash
from .models import Group, GroupMember, Message, User, db
from .security import admin_required, login_required

admin = Blueprint("admin", __name__, url_prefix="/admin")
SUPREME_USERNAME = "admin"


def is_supreme_account():
    return (session.get("username") or "").lower() == SUPREME_USERNAME


@admin.route("/")
@admin_required
def panel():
    users = User.query.order_by(User.created_at.desc()).all()
    groups = Group.query.order_by(Group.created_at.desc()).all()
    members = GroupMember.query.all()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(200).all()

    members_by_group = {}
    for m in members:
        members_by_group.setdefault(m.group_id, []).append(m)

    users_map = {u.id: u for u in users}

    return render_template(
        "admin.html",
        users=users,
        messages=messages,
        groups=groups,
        members_by_group=members_by_group,
        users_map=users_map,
    )


@admin.route("/supremo")
@login_required
def supreme_panel():
    if not is_supreme_account():
        abort(403)

    if session.get("role") != "admin":
        return render_template("admin_supremo.html")

    return redirect(url_for("admin.panel"))


@admin.route("/supremo/ativar", methods=["POST"])
@login_required
def activate_supreme():
    if not is_supreme_account():
        abort(403)

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
    username = request.form.get("username", "").strip().replace("@", "").lower()
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
        group = Group(name=name, created_by=creator.id)
        db.session.add(group)
        db.session.commit()
        db.session.add(GroupMember(group_id=group.id, user_id=creator.id, role="owner"))
        db.session.commit()
    return redirect(url_for("admin.panel"))


@admin.route("/group/<int:group_id>/member/add", methods=["POST"])
@admin_required
def add_group_member(group_id):
    username = request.form.get("username", "").strip().replace("@", "").lower()
    role = request.form.get("role", "member")
    user = User.query.filter_by(username=username).first()
    if user and not GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first():
        db.session.add(
            GroupMember(
                group_id=group_id,
                user_id=user.id,
                role="admin" if role == "admin" else "member",
            )
        )
        db.session.commit()
    return redirect(url_for("admin.panel"))


@admin.route("/group/<int:group_id>/member/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_group_admin(group_id, user_id):
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first_or_404()
    if member.role != "owner":
        member.role = "admin" if member.role == "member" else "member"
        db.session.commit()
    return redirect(url_for("admin.panel"))


@admin.route("/group/<int:group_id>/member/<int:user_id>/toggle-mute", methods=["POST"])
@admin_required
def toggle_group_mute(group_id, user_id):
    member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first_or_404()
    member.muted = not member.muted
    db.session.commit()
    return redirect(url_for("admin.panel"))
