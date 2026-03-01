from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            error = "Usuário já existe"
        elif len(password) < 6:
            error = "A senha precisa ter pelo menos 6 caracteres"
        else:
            role = "admin" if User.query.count() == 0 else "user"

            new_user = User(
                username=username,
                password=generate_password_hash(password),
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

            return redirect("/")

    return render_template("register.html", error=error)


@auth.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
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
            return redirect("/dashboard")

    return render_template("login.html", error=error)


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
