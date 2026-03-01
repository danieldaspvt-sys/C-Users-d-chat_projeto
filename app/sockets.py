from flask import session
from flask_socketio import emit, join_room
from . import socketio

online_users = set()
private_messages = {}


def get_room(user1, user2):
    return "_".join(sorted([user1, user2]))


@socketio.on("connect")
def handle_connect():
    username = session.get("username")
    if not username:
        return

    online_users.add(username)
    join_room(username)
    emit("online_users", sorted(list(online_users)), broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")
    if not username:
        return

    online_users.discard(username)
    emit("online_users", sorted(list(online_users)), broadcast=True)


@socketio.on("start_chat")
def start_chat(data):
    current_user = session.get("username")
    target_user = data.get("to") if data else None

    if not current_user or not target_user:
        return

    room = get_room(current_user, target_user)
    join_room(room)

    history = private_messages.get(room, [])
    emit("chat_history", history)


@socketio.on("private_message")
def handle_private_message(data):
    sender = session.get("username")
    receiver = data.get("to") if data else None
    message = (data.get("message") or "").strip() if data else ""
    media = data.get("media") if data else None

    if not sender or not receiver or (not message and not media):
        return

    room = get_room(sender, receiver)
    payload = {
        "from": sender,
        "to": receiver,
        "message": message,
        "media": media,
    }

    history = private_messages.setdefault(room, [])
    history.append(payload)

    if len(history) > 100:
        del history[:-100]

    emit("private_message", payload, room=room)
    emit("private_message", payload, room=receiver)
