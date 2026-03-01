from flask import Blueprint, jsonify, render_template, request, session
from .friendships import get_friends, pending_requests, respond_request, send_request
from .models import User
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

    return jsonify(
        {
            "friends": [
                {
                    "username": f.username,
                    "profile_image": f.profile_image,
                }
                for f in friends
            ],
            "pending": [
                {
                    "username": p.username,
                    "profile_image": p.profile_image,
                }
                for p in pending
            ],
        }
    )


@chat.route("/api/friends/request", methods=["POST"])
@login_required
def send_request_api():
    payload = request.get_json(silent=True) or {}
    target_username = (payload.get("username") or "").strip()

    user = User.query.filter_by(username=session["username"]).first_or_404()
    ok, message = send_request(user.id, target_username)
    code = 200 if ok else 400
    return jsonify({"ok": ok, "message": message}), code


@chat.route("/api/friends/respond", methods=["POST"])
@login_required
def respond_request_api():
    payload = request.get_json(silent=True) or {}
    requester_username = (payload.get("username") or "").strip()
    action = payload.get("action")

    current = User.query.filter_by(username=session["username"]).first_or_404()
    requester = User.query.filter_by(username=requester_username).first()

    if not requester:
        return jsonify({"ok": False, "message": "Usuário não encontrado"}), 404

    ok, message = respond_request(current.id, requester.id, action)
    code = 200 if ok else 400
    return jsonify({"ok": ok, "message": message}), code
