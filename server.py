from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'segredo'
socketio = SocketIO(app, async_mode="eventlet")

# Página de login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        session["username"] = username
        return redirect("/chat")
    return render_template("login.html")

# Página do chat
@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect("/")
    return render_template("chat.html", username=session["username"])

@socketio.on("message")
def handleMessage(msg):
    username = session.get("username", "Anônimo")
    send(f"{username}: {msg}", broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)