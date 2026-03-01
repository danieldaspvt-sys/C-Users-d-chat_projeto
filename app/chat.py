from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, session
from .friendships import (
    get_friends,
    outgoing_requests,
    pending_requests,
    respond_request,
    send_request,
)
from .models import Group, GroupMember, Status, Story, User, db
from .security import login_required

chat = Blueprint("chat", __name__)


@chat.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@chat.route("/api/friends", methods=["GET"])
@login_required
def friends_api():
    user = User.query.filter_by(username=session["username"]).first_or_404()
    friends = get_friends(user.id)
    pending = pending_requests(user.id)
    outgoing = outgoing_requests(user.id)

    return jsonify(
        {
            "friends": [
                {"username": f.username, "profile_image": f.profile_image}
                for f in friends
            ],
            "pending": [
                {"username": p.username, "profile_image": p.profile_image}
                for p in pending
            ],
            "outgoing": [
                {"username": o.username, "profile_image": o.profile_image}
                for o in outgoing
            ],
        }
    )


@chat.route("/api/friends/request", methods=["POST"])
@login_required
def send_request_api():
    payload = request.get_json(silent=True) or {}
    target_username = (payload.get("username") or "").strip().replace("@", "")

    user = User.query.filter_by(username=session["username"]).first_or_404()
    ok, message = send_request(user.id, target_username)
    code = 200 if ok else 400
    return jsonify({"ok": ok, "message": message}), code


@chat.route("/api/friends/respond", methods=["POST"])
@login_required
def respond_request_api():
    payload = request.get_json(silent=True) or {}
    requester_username = (payload.get("username") or "").strip().replace("@", "")
    action = payload.get("action")

    current = User.query.filter_by(username=session["username"]).first_or_404()
    requester = User.query.filter_by(username=requester_username).first()

    if not requester:
        return jsonify({"ok": False, "message": "Usuário não encontrado"}), 404

    ok, message = respond_request(current.id, requester.id, action)
    code = 200 if ok else 400
    return jsonify({"ok": ok, "message": message}), code


@chat.route("/api/groups", methods=["GET"])
@login_required
def groups_api():
    user = User.query.filter_by(username=session["username"]).first_or_404()

    memberships = GroupMember.query.filter_by(user_id=user.id).all()
    group_ids = [m.group_id for m in memberships]
    groups = Group.query.filter(Group.id.in_(group_ids)).order_by(Group.name.asc()).all() if group_ids else []

    return jsonify(
        {
            "groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "role": next((m.role for m in memberships if m.group_id == g.id), "member"),
                    "muted": next((m.muted for m in memberships if m.group_id == g.id), False),
                }
                for g in groups
            ]
        }
    )


@chat.route("/api/status", methods=["GET", "POST"])
@login_required
def status_api():
    user = User.query.filter_by(username=session["username"]).first_or_404()

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        if not text:
            return jsonify({"ok": False, "message": "Status vazio"}), 400

        current = Status.query.filter_by(user_id=user.id).first()
        if current:
            current.text = text
            current.created_at = datetime.utcnow()
        else:
            db.session.add(Status(user_id=user.id, text=text))
        db.session.commit()
        return jsonify({"ok": True, "message": "Status atualizado"})

    status = Status.query.filter_by(user_id=user.id).first()
    return jsonify({"status": status.text if status else "Sem status"})


@chat.route("/api/stories", methods=["GET", "POST"])
@login_required
def stories_api():
    user = User.query.filter_by(username=session["username"]).first_or_404()

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        content = (payload.get("content") or "").strip()
        if not content:
            return jsonify({"ok": False, "message": "Story vazio"}), 400

        db.session.add(
            Story(
                user_id=user.id,
                content=content,
                media_type="text",
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
        )
        db.session.commit()
        return jsonify({"ok": True, "message": "Story publicado"})

    stories = (
        db.session.query(Story, User)
        .join(User, User.id == Story.user_id)
        .filter(Story.expires_at > datetime.utcnow())
        .order_by(Story.created_at.desc())
        .limit(30)
        .all()
    )

    return jsonify(
        {
            "stories": [
                {
                    "username": u.username,
                    "content": s.content,
                    "created_at": s.created_at.strftime("%d/%m %H:%M"),
                }
                for s, u in stories
            ]
        }
    )


@chat.route("/call/<room>")
@login_required
def call_room(room):
    return render_template("call.html", room=room)
