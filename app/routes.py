from flask import Blueprint, render_template, session, redirect

main = Blueprint("main", __name__)


@main.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html")
