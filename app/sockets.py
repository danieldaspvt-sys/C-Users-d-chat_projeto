from flask import session
from flask_socketio import emit, join_room
from . import socketio
from .friendships import are_friends, get_friends
from .models import Message, User, db

online_users = set()


def get_room(user1, user2):
    return "_".join(sorted([user1, user2]))


def get_current_user():
    username = session.get("username")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def emit_friends_presence(user):
    friends = get_friends(user.id)
    online = [friend.username for friend in friends if friend.username in online_users]
    emit("friends_online", online)


def notify_user_friends(user, online=True):
    friends = get_friends(user.id)
    for friend in friends:
        emit(
            "friend_presence",
            {"username": user.username, "online": online},
            room=friend.username,
        )


@socketio.on("connect")
def handle_connect():
    user = get_current_user()
    if not user or user.banned:
        return

    online_users.add(user.username)
    join_room(user.username)
    emit_friends_presence(user)
    notify_user_friends(user, online=True)


@socketio.on("disconnect")
def handle_disconnect():
    user = get_current_user()
    if not user:
        return

    online_users.discard(user.username)
    notify_user_friends(user, online=False)


@socketio.on("start_chat")
def start_chat(data):
    user = get_current_user()
    target_user = (data or {}).get("to")

    if not user or not target_user:
        return

    target = User.query.filter_by(username=target_user).first()
    if not target or not are_friends(user.id, target.id):
        emit("chat_error", {"message": "Somente amigos podem conversar no privado."})
        return

    room = get_room(user.username, target_user)
    join_room(room)

    history = Message.query.filter(
        ((Message.sender_id == user.id) & (Message.receiver_id == target.id))
        | ((Message.sender_id == target.id) & (Message.receiver_id == user.id))
    ).order_by(Message.timestamp.asc()).limit(100).all()

    payload = [
        {
            "from": User.query.get(item.sender_id).username,
            "to": User.query.get(item.receiver_id).username,
            "message": item.content,
            "media": {
                "type": item.media_type,
                "data": item.media_data,
            }
            if item.media_type and item.media_data
            else None,
        }
        for item in history
    ]
    emit("chat_history", payload)


@socketio.on("private_message")
def handle_private_message(data):
    user = get_current_user()
    receiver_username = (data or {}).get("to")
    message = ((data or {}).get("message") or "").strip()
    media = (data or {}).get("media")

    if not user or not receiver_username or (not message and not media):
        return

    receiver = User.query.filter_by(username=receiver_username).first()
    if not receiver or not are_friends(user.id, receiver.id):
        emit("chat_error", {"message": "Somente amigos podem conversar no privado."})
        return

    media_type = None
    media_data = None
    if media:
        media_type = media.get("type")
        media_data = media.get("data")

    db.session.add(
        Message(
            sender_id=user.id,
            receiver_id=receiver.id,
            content=message,
            media_type=media_type,
            media_data=media_data,
        )
    )
    db.session.commit()

    payload = {
        "from": user.username,
        "to": receiver.username,
        "message": message,
        "media": media,
    }

    room = get_room(user.username, receiver.username)
    emit("private_message", payload, room=room)
    emit("private_message", payload, room=receiver.username)
