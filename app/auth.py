from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, db

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().replace("@", "")
        password = request.form["password"]

        if not username:
            error = "Informe um username"
        elif User.query.filter_by(username=username).first():
            error = "Usuário já existe"
        elif len(password) < 6:
            error = "A senha precisa ter pelo menos 6 caracteres"
        else:
            role = "admin" if User.query.count() == 0 else "user"
            db.session.add(
                User(username=username, password=generate_password_hash(password), role=role)
            )
            db.session.commit()
            return redirect(url_for("auth.login"))

    return render_template("register.html", error=error)


@auth.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().replace("@", "")
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user:
            error = "Usuário não encontrado"
        elif user.banned:
            error = "Usuário banido"
        elif not check_password_hash(user.password, password):
            error = "Senha incorreta"
        else:
            session["username"] = user.username
            session["role"] = user.role
            session["profile_image"] = user.profile_image
            return redirect(url_for("chat.dashboard"))

    return render_template("login.html", error=error)


@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
