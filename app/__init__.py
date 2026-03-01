from flask import Flask
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
from .models import User, db

socketio = SocketIO(cors_allowed_origins="*")


def seed_admin():
    admin = User.query.filter_by(username="admin").first()
    if admin:
        admin.role = "admin"
        admin.banned = False
    else:
        db.session.add(
            User(
                username="admin",
                password=generate_password_hash("admin123"),
                role="admin",
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
