import os
from uuid import uuid4
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from .friendships import get_friends
from .models import User, db
from .security import login_required

profile = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    user = User.query.filter_by(username=session["username"]).first_or_404()
    error = None

    if request.method == "POST":
        upload = request.files.get("profile_image")
        if not upload or upload.filename == "":
            error = "Selecione uma imagem"
        elif not allowed_file(upload.filename):
            error = "Formato inválido. Use PNG/JPG/JPEG/GIF/WEBP"
        else:
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            if size > MAX_FILE_SIZE:
                error = "Imagem muito grande. Limite 5MB"
            else:
                filename = secure_filename(upload.filename)
                ext = filename.rsplit(".", 1)[1].lower()
                final_name = f"{uuid4().hex}.{ext}"

                upload_dir = os.path.join(current_app.static_folder, "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                upload.save(os.path.join(upload_dir, final_name))

                user.profile_image = f"uploads/{final_name}"
                db.session.commit()
                session["profile_image"] = user.profile_image
                return redirect(url_for("profile.profile_page"))

    friends_count = len(get_friends(user.id))
    return render_template("profile.html", user=user, friends_count=friends_count, error=error)
