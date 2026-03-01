from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User

auth = Blueprint("auth", __name__)

# REGISTRO
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Usuário já existe"

        # Se for o primeiro usuário → vira admin
        role = "admin" if User.query.count() == 0 else "user"

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# LOGIN
@auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user:
            return "Usuário não encontrado"

        if user.banned:
            return "Usuário banido"

        if not check_password_hash(user.password, password):
            return "Senha incorreta"

        session["username"] = user.username
        session["role"] = user.role

        return redirect("/dashboard")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")