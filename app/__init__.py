from flask import Flask
from flask_socketio import SocketIO
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from .models import User, db

socketio = SocketIO(cors_allowed_origins="*")


def _get_columns(table_name):
    rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def run_schema_migrations():
    tables = {
        row[0]
        for row in db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
    }

    if "user" in tables:
        user_columns = _get_columns("user")
        if "profile_image" not in user_columns:
            db.session.execute(
                text(
                    "ALTER TABLE user ADD COLUMN profile_image VARCHAR(255) DEFAULT 'uploads/default-avatar.svg'"
                )
            )

    if "message" in tables:
        message_columns = _get_columns("message")

        if "sender_id" not in message_columns:
            db.session.execute(text("ALTER TABLE message ADD COLUMN sender_id INTEGER"))
        if "receiver_id" not in message_columns:
            db.session.execute(text("ALTER TABLE message ADD COLUMN receiver_id INTEGER"))
        if "media_type" not in message_columns:
            db.session.execute(text("ALTER TABLE message ADD COLUMN media_type VARCHAR(20)"))
        if "media_data" not in message_columns:
            db.session.execute(text("ALTER TABLE message ADD COLUMN media_data TEXT"))

        refreshed = _get_columns("message")
        if "sender" in refreshed and "sender_id" in refreshed:
            db.session.execute(
                text(
                    """
                    UPDATE message
                    SET sender_id = (
                        SELECT id FROM user WHERE user.username = message.sender LIMIT 1
                    )
                    WHERE sender_id IS NULL AND sender IS NOT NULL
                    """
                )
            )
        if "receiver" in refreshed and "receiver_id" in refreshed:
            db.session.execute(
                text(
                    """
                    UPDATE message
                    SET receiver_id = (
                        SELECT id FROM user WHERE user.username = message.receiver LIMIT 1
                    )
                    WHERE receiver_id IS NULL AND receiver IS NOT NULL
                    """
                )
            )

    db.session.commit()


def seed_admin():
    admin = User.query.filter_by(username="admin").first()
    if admin:
        admin.role = "admin"
        admin.banned = False
        if not admin.profile_image:
            admin.profile_image = "uploads/default-avatar.svg"
    else:
        db.session.add(
            User(
                username="admin",
                password=generate_password_hash("admin123"),
                role="admin",
                profile_image="uploads/default-avatar.svg",
            )
        )
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "supersecretkey"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        db.create_all()
        run_schema_migrations()
        seed_admin()

    from .auth import auth
    from .chat import chat
    from .profile import profile
    from .admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(chat)
    app.register_blueprint(profile)
    app.register_blueprint(admin)

    from . import sockets  # noqa: F401

    return app
