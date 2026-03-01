from flask import Flask
from flask_socketio import SocketIO
from .models import db

socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "supersecretkey"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    from .routes import main
    app.register_blueprint(main)

    from .auth import auth
    app.register_blueprint(auth)

    # IMPORTA SOCKETS AQUI (SEM IMPORTAR socketio DELE)
    from . import sockets

    return app